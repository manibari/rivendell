---
name: Telegram Bot Development Guide
description: Comprehensive guide for building Telegram bots with grammY (TypeScript) or python-telegram-bot (Python). Covers framework selection, project structure, Bot API features, deployment, and common patterns.
when_to_use: when building a Telegram bot, working with Telegram Bot API, or using grammY, python-telegram-bot, aiogram, or Telegraf
version: 1.0.0
tags: [telegram, bot, grammy, python-telegram-bot, chatbot]
languages: [typescript, python]
user_invocable: false
---

# Telegram Bot Development Guide

## 1. Framework Selection

| Criteria | Recommendation |
|----------|---------------|
| TypeScript / JavaScript | **grammY** - best types, multi-runtime (Node/Deno/Bun/CF Workers), rich plugin ecosystem |
| Python | **python-telegram-bot** (PTB) - most popular, fully async, excellent docs |
| Python + high scale | **aiogram** - higher throughput, lighter weight |
| Telegraf | **Do NOT use for new projects** - legacy, grammY is its spiritual successor with better DX |

**Default choice:** grammY for TypeScript, PTB for Python. Ask user preference if unclear.

## 2. Project Structure

```
src/
├── bot.ts (or bot.py)        # Entry point, bot setup
├── commands/                  # Command handlers (/start, /help, etc.)
│   ├── start.ts
│   └── help.ts
├── handlers/                  # Message/callback handlers
│   ├── messages.ts
│   └── callbacks.ts
├── keyboards/                 # Inline and reply keyboard builders
├── middleware/                 # Auth, rate limiting, logging
├── services/                  # Business logic, external API calls
└── config.ts                  # Environment variables, constants
```

## 3. Essential Setup Checklist

- [ ] BOT_TOKEN from @BotFather stored in env var (NEVER hardcode)
- [ ] Error handler: grammY `bot.catch()` / PTB `application.add_error_handler()`
- [ ] Graceful shutdown on SIGINT/SIGTERM
- [ ] Rate limiter middleware from day one
- [ ] Structured logging (at minimum: user ID, command, timestamp)
- [ ] Set bot commands via `bot.api.setMyCommands()` or `application.bot.set_my_commands()`

### grammY Minimal Setup

```typescript
import { Bot } from "grammy";

const bot = new Bot(process.env.BOT_TOKEN!);

bot.command("start", (ctx) => ctx.reply("Hello!"));

bot.catch((err) => {
  console.error("Bot error:", err);
});

process.once("SIGINT", () => bot.stop());
process.once("SIGTERM", () => bot.stop());

bot.start();
```

### PTB Minimal Setup

```python
from telegram.ext import ApplicationBuilder, CommandHandler

async def start(update, context):
    await update.message.reply_text("Hello!")

app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_error_handler(error_handler)
app.run_polling()
```

## 4. Polling vs Webhooks

| Mode | When to Use | Tradeoffs |
|------|-------------|-----------|
| **Polling** | Development, simple bots, VPS | Easy setup, constant connection, slightly higher latency |
| **Webhooks** | Production, serverless, scale | Real-time, cost-efficient, requires HTTPS endpoint |

### Local Webhook Development

Use `ngrok` or `cloudflared tunnel` to expose localhost:

```bash
ngrok http 3000
# Then set webhook to https://<id>.ngrok-free.app/webhook
```

### grammY Webhook Mode

```typescript
import { webhookCallback } from "grammy";
import express from "express";

const app = express();
app.use(express.json());
app.post("/webhook", webhookCallback(bot, "express"));
app.listen(3000);

// Set webhook URL once:
await bot.api.setWebhook("https://your-domain.com/webhook");
```

### PTB Webhook Mode

```python
app = ApplicationBuilder().token(TOKEN).updater(None).build()
# Add handlers...
await app.bot.set_webhook("https://your-domain.com/webhook")
# Use with your ASGI/WSGI framework to feed updates
```

## 5. Key Telegram Bot API Features

| Feature | Method / Notes |
|---------|---------------|
| **Inline keyboards** | `InlineKeyboardMarkup` - buttons with `callback_data` (max 64 bytes) or URL |
| **Reply keyboards** | `ReplyKeyboardMarkup` - custom keyboard below input field |
| **Bot commands** | `setMyCommands` - appears in menu; set per-scope (all users, group admins, etc.) |
| **Photos** | `sendPhoto` - supports file_id, URL, or upload; max 10 MB |
| **Videos** | `sendVideo` - max 50 MB; `sendVideoNote` for round videos |
| **Documents** | `sendDocument` - max 50 MB (2 GB via local Bot API server) |
| **Media groups** | `sendMediaGroup` - up to 10 photos/videos in album |
| **Payments** | `sendInvoice` - supports Telegram Stars (digital goods) and payment providers |
| **Mini Apps** | Web apps inside Telegram via `WebAppInfo` button |
| **Inline mode** | `answerInlineQuery` - respond to @bot queries in any chat |
| **Edit messages** | `editMessageText`, `editMessageReplyMarkup` - update sent messages |
| **Delete messages** | `deleteMessage` - bot can delete own msgs and others' in groups (with permission) |

### Rate Limits

| Scope | Limit |
|-------|-------|
| Per chat | 1 message/second |
| Global | 30 messages/second |
| Bulk notifications | 30 users/second |
| Group chat | 20 messages/minute per group |

Exceeding limits returns 429 Too Many Requests with `retry_after` field.

## 6. Common Patterns

### Conversation / Multi-Step Flows

**grammY:** Use the [conversations plugin](https://grammy.dev/plugins/conversations)

```typescript
import { conversations, createConversation } from "@grammyjs/conversations";

bot.use(session({ initial: () => ({}) }));
bot.use(conversations());
bot.use(createConversation(onboarding));

async function onboarding(conversation, ctx) {
  await ctx.reply("What is your name?");
  const nameCtx = await conversation.waitFor("message:text");
  const name = nameCtx.message.text;
  await ctx.reply(`Hello, ${name}!`);
}
```

**PTB:** Use `ConversationHandler`

```python
from telegram.ext import ConversationHandler, MessageHandler, filters

NAME, AGE = range(2)

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NAME: [MessageHandler(filters.TEXT, got_name)],
        AGE: [MessageHandler(filters.TEXT, got_age)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
```

### Session / State Management

**grammY:** Sessions plugin with pluggable storage

```typescript
import { session } from "grammy";
import { RedisAdapter } from "@grammyjs/storage-redis";

bot.use(session({
  initial: () => ({ step: 0, data: {} }),
  storage: new RedisAdapter({ instance: redisClient }),
}));
```

Storage progression: `freeStorage` (dev) -> `RedisAdapter` -> `PsqlAdapter`

**PTB:** Persistence layer

```python
from telegram.ext import PicklePersistence

persistence = PicklePersistence(filepath="bot_data.pickle")
app = ApplicationBuilder().token(TOKEN).persistence(persistence).build()
# Access via context.user_data, context.chat_data, context.bot_data
```

### Interactive Menus

**grammY:** Use the [menu plugin](https://grammy.dev/plugins/menu)

```typescript
import { Menu } from "@grammyjs/menu";

const menu = new Menu("settings")
  .text("Language", (ctx) => ctx.reply("Choose language"))
  .row()
  .text("Notifications", (ctx) => ctx.reply("Toggle notifications"));

bot.use(menu);
bot.command("settings", (ctx) => ctx.reply("Settings:", { reply_markup: menu }));
```

**PTB:** Build `InlineKeyboardMarkup` + handle callbacks manually.

### Error Handling and Retries

**grammY:**
```typescript
import { autoRetry } from "@grammyjs/auto-retry";
import { apiThrottler } from "@grammyjs/transformer-throttler";

bot.api.config.use(autoRetry());       // Auto-retry on 429
bot.api.config.use(apiThrottler());     // Pre-emptive throttling
```

**PTB:**
```python
from telegram.ext import AIORateLimiter

app = ApplicationBuilder().token(TOKEN).rate_limiter(AIORateLimiter()).build()
```

## 7. Deployment Guide

| Platform | Best For | Cost | Notes |
|----------|----------|------|-------|
| **Cloudflare Workers** | grammY webhooks | Free 100k req/day | Best for grammY; use `webhookCallback(bot, "cloudflare-mod")` |
| **AWS Lambda** | Any framework + webhooks | Free 1M invocations/mo | Use API Gateway or Function URL as webhook endpoint |
| **Railway** | Persistent polling bots | $5/mo | Easy deploy from GitHub, always-on |
| **Fly.io** | Low-latency global | $5/mo | Good for bots needing persistent connections |
| **VPS (Hetzner)** | Full control, long polling | ~EUR 4/mo | Use systemd/PM2/supervisor for process management |
| **Vercel Functions** | Quick deploys | Free tier, 10s limit | Edge functions have shorter timeout; not ideal for heavy processing |

### Deployment Checklist

- [ ] HTTPS endpoint for webhooks (most platforms provide this automatically)
- [ ] Set webhook URL via `bot.api.setWebhook(url)` or Bot API call
- [ ] Health check endpoint (`GET /` returns 200)
- [ ] Environment secrets configured in platform (never in code/repo)
- [ ] Process manager for polling mode (PM2, systemd, supervisor)
- [ ] Webhook secret token for verification (`secret_token` parameter)

### Cloudflare Workers Example (grammY)

```typescript
import { Bot, webhookCallback } from "grammy";

export default {
  async fetch(req: Request, env: Env) {
    const bot = new Bot(env.BOT_TOKEN);
    // Add handlers...
    return webhookCallback(bot, "cloudflare-mod")(req);
  },
};
```

## 8. Database Patterns

| Data Type | Recommended Storage |
|-----------|-------------------|
| Session / ephemeral state | Redis or in-memory (grammY session, PTB context) |
| User profiles, persistent data | PostgreSQL (Prisma/Drizzle) or MongoDB |
| Serverless environments | Upstash Redis, Supabase, DynamoDB, Cloudflare D1 |
| File/media cache | S3, Cloudflare R2 |
| Scheduled jobs | BullMQ (Node), PTB `JobQueue` (Python), or external cron |

**Key principle:** Start with in-memory/file storage for prototyping, migrate to proper database before production.

## 9. Testing

### grammY

Mock the context object for unit tests:

```typescript
import { Context } from "grammy";

// Create mock context
const ctx = {
  reply: vi.fn(),
  message: { text: "/start", from: { id: 123 } },
} as unknown as Context;

await startHandler(ctx);
expect(ctx.reply).toHaveBeenCalledWith("Hello!");
```

### PTB

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_start_command():
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    await start(update, context)
    update.message.reply_text.assert_called_once_with("Hello!")
```

### Integration Testing

Telegram provides a test environment at `test.telegram.org`. Create a test bot there for integration tests that hit real Telegram API without affecting production.

## 10. Mini Apps (Advanced)

Mini Apps are web applications (HTML/CSS/JS) that run inside Telegram's UI.

| Aspect | Details |
|--------|---------|
| **SDK** | `@twa-dev/sdk` (npm) or `@telegram-apps/sdk` |
| **Launch methods** | Inline keyboard button (`web_app` field), bot menu button, direct link `t.me/bot?startapp=` |
| **Auth** | `initData` sent by Telegram, validate with HMAC on backend |
| **Storage** | `CloudStorage` (per-user, 1 MB), `SecureStorage` |
| **Payments** | Can trigger Telegram Payments from within Mini App |
| **Viewport** | Expandable to full screen; handle safe area insets |

### Launching a Mini App

```typescript
bot.command("app", (ctx) =>
  ctx.reply("Open app", {
    reply_markup: {
      inline_keyboard: [[{
        text: "Launch",
        web_app: { url: "https://your-app.com" },
      }]],
    },
  })
);
```

### Validating initData on Backend

Always validate `initData` server-side using HMAC-SHA256 with your bot token. Never trust client-side data alone.

## Quick Decision Flowchart

```
Need a Telegram bot?
├── TypeScript? → grammY
│   ├── Serverless? → Cloudflare Workers + webhooks
│   └── VPS/Railway? → Long polling or webhooks
├── Python? → python-telegram-bot
│   ├── High scale? → Consider aiogram
│   └── Standard? → PTB with polling or webhooks
└── Need web UI inside Telegram? → Mini App + bot backend
```
