"""avatar-gateway — the assistant's conversational brain behind the widget.

OpenAI-compatible /v1/chat/completions for dashboard's /avatar iframe
(ai-avatar-bot widget speaks this contract via its data-ollama param;
the `model` field selects the persona: lindir / miriel).

Engine chain (persona.conf `engine`, default codex):
    codex          `codex exec` — ChatGPT OAuth quota, read-only sandbox,
                   cwd = empty dir (cannot see the repo)
    claude         `claude -p --model haiku --allowedTools ""` (also the
                   automatic fallback when codex fails)
    openai-api /   direct HTTPS with keys from ~/.config/rivendell/
    anthropic-api  gateway-keys.env (managed via /settings/keys)

The chat model has ZERO tools on every engine. When it wants something done
it appends a `[[dispatch: ...]]` marker; the gateway strips it and runs
`sk dispatch new --source avatar` deterministically — the tiered
confirmation flow is untouched. Bound to 127.0.0.1; CORS allows :3000 only.

New event channels / frontends: point anything OpenAI-compatible at
POST /v1/chat/completions; persona = model field.
"""

import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

REPO_DIR = Path(__file__).resolve().parent.parent
CONF = REPO_DIR / "data" / "persona.conf"
KEYS_FILE = Path.home() / ".config" / "rivendell" / "gateway-keys.env"
CHAT_TIMEOUT = 60
KEY_NAMES = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")
DISPATCH_MARKER = re.compile(r"\[\[dispatch:\s*(.+?)\]\]", re.S)

app = FastAPI(title="rivendell avatar-gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"], allow_headers=["*"],
)


# ── persona.conf / keys ─────────────────────────────────────────────────

def read_conf() -> dict:
    conf = {}
    if CONF.exists():
        for line in CONF.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                conf[k.strip()] = v.strip()
    return conf


def write_active(slug: str):
    lines = CONF.read_text().splitlines()
    out = [f"active = {slug}" if l.replace(" ", "").startswith("active=") else l
           for l in lines]
    CONF.write_text("\n".join(out) + "\n")


def persona_slugs(conf: dict) -> list:
    return sorted({k.split(".")[0] for k in conf if "." in k})


def load_keys() -> dict:
    keys = {}
    if KEYS_FILE.exists():
        for line in KEYS_FILE.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                keys[k.strip()] = v.strip()
    return keys


def save_keys(keys: dict):
    KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEYS_FILE.write_text("".join(f"{k}={v}\n" for k, v in keys.items() if v))
    os.chmod(KEYS_FILE, 0o600)


def mask(v: str) -> str:
    return ("…" + v[-4:]) if len(v) >= 8 else "…"


# ── engines (all tool-less) ─────────────────────────────────────────────

def build_prompt(slug: str, messages: list) -> str:
    conf = read_conf()
    pfile = REPO_DIR / conf.get(f"{slug}.file", f"profiles/personas/{slug}.md")
    persona = pfile.read_text() if pfile.exists() else ""
    kg = subprocess.run(
        ["python3", str(REPO_DIR / "scripts" / "kg.py"), "dump", "--active-only"],
        capture_output=True, text=True).stdout[:8000] or "(知識庫目前是空的)"
    transcript = "\n".join(
        f"{'Peter' if m.get('role') == 'user' else '你'}：{m.get('content', '')}"
        for m in messages if m.get("role") in ("user", "assistant"))
    return f"""{persona}

---

## 知識庫 active facts（回答時的記憶依據，自然引用不列檔名）
{kg}

## 你的處境
你正透過語音/文字視窗跟 Peter 對話（回覆會被唸出來）。

## 說話鐵則——像個真人，不是客服機器人
1. 像同事傳訊息：短句、口語、可以省略主詞。閒聊一兩句就好，正事才多說
2. 禁止對仗排比句（「若A則B；若C則D」這種一看就是 AI）、禁止條列、禁止 emoji
3. 不重述 Peter 剛說的話，不每句都用敬語開頭，不硬加結尾問句
4. 意見和常識儘管給：吃什麼、怎麼安排、值不值得——直接給一個明確建議，
   不要「都可以」也不要推說查不了（給建議不需要工具）
5. 但【動作】不能瞎承諾：你沒有工具，查外送、看網頁、讀檔案這類「現在去查」
   的事做不到就別說會去做——要嘛開提案（見下），要嘛老實講

## 辦事
Peter 要你做事（寄信、排程、記待辦、查客戶資料…）時：自然地說你來處理，
回覆最後附 [[dispatch: 一句話描述]] ——系統會開提案給 Peter 確認。
純聊天不加標記。不要假裝已經做完任何事。

## 對話
{transcript}
你："""


def run_codex(prompt: str) -> str:
    workdir = tempfile.mkdtemp(prefix="gw-codex-")
    r = subprocess.run(
        ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", "-"],
        input=prompt, capture_output=True, text=True,
        timeout=CHAT_TIMEOUT, cwd=workdir)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"codex exit={r.returncode}: {r.stderr[-200:]}")
    return r.stdout.strip()


def run_claude(prompt: str) -> str:
    r = subprocess.run(
        ["claude", "-p", prompt, "--model", "haiku",
         "--allowedTools", "", "--output-format", "text"],
        stdin=subprocess.DEVNULL, capture_output=True, text=True,
        timeout=CHAT_TIMEOUT, cwd=tempfile.gettempdir())
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"claude exit={r.returncode}: {r.stderr[-200:]}")
    return r.stdout.strip()


def run_openai_api(prompt: str) -> str:
    key = load_keys().get("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers={"Authorization": f"Bearer {key}"},
                      json={"model": "gpt-4o-mini",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 300},
                      timeout=CHAT_TIMEOUT)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def run_anthropic_api(prompt: str) -> str:
    key = load_keys().get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    r = requests.post("https://api.anthropic.com/v1/messages",
                      headers={"x-api-key": key,
                               "anthropic-version": "2023-06-01"},
                      json={"model": "claude-haiku-4-5-20251001",
                            "max_tokens": 300,
                            "messages": [{"role": "user", "content": prompt}]},
                      timeout=CHAT_TIMEOUT)
    r.raise_for_status()
    return r.json()["content"][0]["text"].strip()


ENGINES = {"codex": run_codex, "claude": run_claude,
           "openai-api": run_openai_api, "anthropic-api": run_anthropic_api}


def chat(prompt: str, engine: str):
    order = [engine] + (["claude"] if engine != "claude" else [])
    last_err = None
    for name in order:
        try:
            return ENGINES[name](prompt), name
        except Exception as e:  # fall through to claude
            last_err = e
    raise HTTPException(502, f"all engines failed: {last_err}")


# ── endpoints ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    model: str = "lindir"
    messages: list
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool | None = False


@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequest):
    conf = read_conf()
    slug = req.model if f"{req.model}.file" in conf else conf.get("active", "lindir")
    engine = conf.get("engine", "codex")
    reply, used = chat(build_prompt(slug, req.messages), engine)

    m = DISPATCH_MARKER.search(reply)
    if m:
        instruction = " ".join(m.group(1).split())
        reply = DISPATCH_MARKER.sub("", reply).strip()
        subprocess.Popen(
            [str(REPO_DIR / "bin" / "sk"), "dispatch", "new",
             "--source", "avatar", instruction],
            cwd=str(REPO_DIR), stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True)
        reply += "（提案我開好了，等你確認再動手。）"

    # 對話歷史落地（之後 facts-cron 也能來抽）
    last_user = next((m.get("content", "") for m in reversed(req.messages)
                      if m.get("role") == "user"), "")
    log_dir = REPO_DIR / "data" / "chat-log"
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / f"{time.strftime('%Y-%m-%d')}.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%H:%M:%S"), "persona": slug,
                            "engine": used, "user": last_user, "reply": reply,
                            "dispatch": bool(m)}, ensure_ascii=False) + "\n")

    return {"id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": f"{slug}@{used}",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": reply}}]}


@app.get("/history")
def history(date: str = "", limit: int = 50):
    day = date or time.strftime("%Y-%m-%d")
    path = REPO_DIR / "data" / "chat-log" / f"{day}.jsonl"
    if not path.exists():
        return {"date": day, "entries": []}
    lines = path.read_text().splitlines()[-limit:]
    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"date": day, "entries": entries}


# ── TTS（widget 的 data-api 契約：POST {voice,text} → binary MP3）────────
# OPENAI_API_KEY 已設時走 OpenAI TTS（自然人聲）；未設回 404，widget 自動
# fallback 瀏覽器內建語音。ChatGPT app 的進階語音是產品功能、OAuth 借不到，
# 這是拿得到的最接近替代。

OPENAI_VOICE = {"m": "onyx", "f": "nova"}


class TTSRequest(BaseModel):
    voice: str = ""
    text: str = ""


@app.post("/api/tts")
def tts(req: TTSRequest):
    from fastapi.responses import Response
    key = load_keys().get("OPENAI_API_KEY", "")
    if not key or not req.text:
        raise HTTPException(404, "tts not configured")
    conf = read_conf()
    active = conf.get("active", "lindir")
    gender = conf.get(f"{active}.gender", "f")
    r = requests.post("https://api.openai.com/v1/audio/speech",
                      headers={"Authorization": f"Bearer {key}"},
                      json={"model": "gpt-4o-mini-tts",
                            "voice": OPENAI_VOICE.get(gender, "nova"),
                            "input": req.text[:600], "response_format": "mp3"},
                      timeout=30)
    if r.status_code != 200:
        raise HTTPException(502, "tts upstream failed")
    return Response(content=r.content, media_type="audio/mpeg")


@app.get("/health")
def health():
    conf = read_conf()
    keys = load_keys()
    codex_ok = (Path.home() / ".codex" / "auth.json").exists()
    return {"ok": True, "active": conf.get("active"),
            "engine": conf.get("engine", "codex"),
            "engines": {"codex": codex_ok, "claude": True,
                        "openai-api": bool(keys.get("OPENAI_API_KEY")),
                        "anthropic-api": bool(keys.get("ANTHROPIC_API_KEY"))}}


@app.get("/persona")
def get_persona():
    conf = read_conf()
    return {"active": conf.get("active"), "engine": conf.get("engine", "codex"),
            "personas": [{"slug": s,
                          "display_name": conf.get(f"{s}.display_name", s),
                          "gender": conf.get(f"{s}.gender", ""),
                          "voice": conf.get(f"{s}.voice", ""),
                          "vrm": conf.get(f"{s}.vrm", "")}
                         for s in persona_slugs(conf)]}


class PersonaRequest(BaseModel):
    active: str | None = None
    engine: str | None = None


@app.post("/persona")
def set_persona(req: PersonaRequest):
    conf = read_conf()
    if req.active:
        if f"{req.active}.file" not in conf:
            raise HTTPException(400, f"unknown persona '{req.active}'")
        write_active(req.active)
    if req.engine:
        if req.engine not in ENGINES:
            raise HTTPException(400, f"unknown engine '{req.engine}'")
        lines = CONF.read_text().splitlines()
        out = [f"engine = {req.engine}" if l.replace(" ", "").startswith("engine=") else l
               for l in lines]
        CONF.write_text("\n".join(out) + "\n")
    return get_persona()


@app.get("/settings/keys")
def get_keys():
    keys = load_keys()
    return {k: {"set": bool(keys.get(k)), "masked": mask(keys[k]) if keys.get(k) else None}
            for k in KEY_NAMES}


class KeysRequest(BaseModel):
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None


@app.post("/settings/keys")
def set_keys(req: KeysRequest):
    keys = load_keys()
    for name in KEY_NAMES:
        val = getattr(req, name)
        if val:
            keys[name] = val.strip()
    save_keys(keys)
    return get_keys()


@app.delete("/settings/keys/{name}")
def delete_key(name: str):
    if name not in KEY_NAMES:
        raise HTTPException(400, "unknown key")
    keys = load_keys()
    keys.pop(name, None)
    save_keys(keys)
    conf = read_conf()
    if conf.get("engine", "").startswith(name.split("_")[0].lower()):
        set_persona(PersonaRequest(engine="codex"))
    return get_keys()
