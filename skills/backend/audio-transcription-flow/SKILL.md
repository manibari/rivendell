---
name: audio-transcription-flow
loop: dev
pdca: do
description: >
  Implement a complete audio upload → speech-to-text → transcript display workflow in a web app.
  TRIGGER when: user says "語音轉文字", "上傳音檔", "Whisper 整合", "轉逐字稿", "transcribe audio",
  "speech to text", "音檔上傳功能", or wants to add audio recording/transcription to their app.
  DO NOT TRIGGER when: user just wants to transcribe a local file for personal use (use a CLI tool instead).
tags: [backend, workflow]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# Audio Transcription Flow

Full-stack pattern for adding audio upload → Whisper transcription → transcript display to a web app.

## Stack Detection

Before writing any code, check the project stack:

```bash
# Detect backend
ls pyproject.toml requirements.txt package.json 2>/dev/null
grep -r "fastapi\|flask\|express\|nextjs" pyproject.toml package.json 2>/dev/null | head -5
```

Then adapt the implementation to the detected stack. This skill covers:
- **Backend**: FastAPI (Python) — primary pattern
- **Frontend**: Next.js / React — primary pattern
- **Transcription engine**: faster-whisper (preferred) or openai-whisper or OpenAI API

---

## Step 1: Detect Transcription Engine

```bash
# Prefer faster-whisper (4–5x faster, same accuracy)
if python3 -c "import faster_whisper" 2>/dev/null; then
    echo "faster-whisper available"
elif python3 -c "import whisper" 2>/dev/null; then
    echo "openai-whisper available"
else
    echo "no local engine — will use OpenAI API"
fi

command -v ffmpeg &>/dev/null && echo "ffmpeg available" || echo "ffmpeg missing — limited format support"
```

If no local engine and no `OPENAI_API_KEY`, ask the user which transcription method they want:
1. Install faster-whisper locally (`pip install faster-whisper`)
2. Use OpenAI Whisper API (requires API key, no local GPU needed)

---

## Step 2: Backend Endpoint

### FastAPI — multipart upload + transcription

```python
# POST /api/transcribe
# Accepts: multipart/form-data with field "audio" (file)
# Returns: { "transcript": str, "duration": float, "language": str }

from fastapi import APIRouter, UploadFile, File, HTTPException
import tempfile, os

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    # Validate file type
    allowed = {"audio/mpeg", "audio/wav", "audio/mp4", "audio/webm", "audio/ogg", "audio/flac"}
    if audio.content_type not in allowed:
        raise HTTPException(400, f"Unsupported type: {audio.content_type}")

    # Write to temp file (Whisper needs a file path)
    suffix = os.path.splitext(audio.filename or "audio.mp3")[1] or ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        result = _transcribe(tmp_path)
        return result
    finally:
        os.unlink(tmp_path)


def _transcribe(path: str) -> dict:
    """Auto-select engine: faster-whisper → whisper → OpenAI API"""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(path)
        text = " ".join(s.text.strip() for s in segments)
        return {"transcript": text, "duration": info.duration, "language": info.language}
    except ImportError:
        pass

    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(path)
        return {"transcript": result["text"], "duration": 0, "language": result.get("language", "unknown")}
    except ImportError:
        pass

    # Fallback: OpenAI API
    import openai
    client = openai.OpenAI()
    with open(path, "rb") as f:
        result = client.audio.transcriptions.create(model="whisper-1", file=f)
    return {"transcript": result.text, "duration": 0, "language": "unknown"}
```

### DB storage (optional but recommended)

If the project has a DB, save transcripts for history:
```python
# transcripts table: id, filename, transcript, duration, language, created_at
```

---

## Step 3: Frontend Upload Component

### React/Next.js

```tsx
// components/AudioUpload.tsx
"use client";
import { useState, useRef } from "react";

export function AudioUpload({ onTranscript }: { onTranscript: (text: string) => void }) {
  const [status, setStatus] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [progress, setProgress] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setStatus("uploading");
    setProgress(0);

    const form = new FormData();
    form.append("audio", file);

    try {
      // Use XHR for progress tracking
      const xhr = new XMLHttpRequest();
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) setProgress(Math.round((e.loaded / e.total) * 100));
      };

      const result = await new Promise<{ transcript: string }>((resolve, reject) => {
        xhr.onload = () => {
          if (xhr.status === 200) resolve(JSON.parse(xhr.responseText));
          else reject(new Error(xhr.statusText));
        };
        xhr.onerror = () => reject(new Error("Network error"));
        xhr.open("POST", "/api/transcribe");
        xhr.send(form);
      });

      onTranscript(result.transcript);
      setStatus("done");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept="audio/*"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
      />
      <button onClick={() => inputRef.current?.click()} disabled={status === "uploading"}>
        {status === "uploading" ? `轉錄中… ${progress}%` : "上傳音檔"}
      </button>
      {status === "error" && <p className="text-red-500">轉錄失敗，請重試</p>}
    </div>
  );
}
```

---

## Step 4: Transcript Display with Edit

```tsx
// components/TranscriptEditor.tsx
"use client";
import { useState } from "react";

export function TranscriptEditor({ initial }: { initial: string }) {
  const [text, setText] = useState(initial);
  const [saved, setSaved] = useState(false);

  return (
    <div>
      <textarea
        value={text}
        onChange={(e) => { setText(e.target.value); setSaved(false); }}
        className="w-full min-h-40 rounded border p-2 font-mono text-sm"
      />
      <div className="flex justify-between mt-1 text-xs text-zinc-500">
        <span>{text.split(/\s+/).filter(Boolean).length} 字</span>
        {saved && <span className="text-green-600">已儲存</span>}
      </div>
      <button onClick={() => setSaved(true)}>儲存逐字稿</button>
    </div>
  );
}
```

---

## Common Issues

| Issue | Fix |
|-------|-----|
| `ffmpeg not found` | `brew install ffmpeg` — needed for webm/ogg conversion |
| Slow transcription | Switch to `faster-whisper` or use `small` model instead of `base` |
| Large file timeout | Set `max_upload_size` and add chunked upload |
| Chinese/mixed lang | Add `language="zh"` param to whisper call |
| No GPU | Use `device="cpu", compute_type="int8"` for faster-whisper |
