# DEPLOY.md — Habesha Bet: Render Deployment

This repo deploys 3 services on Render via `render.yaml`:

1. **Static Site** (`bingo-miniapp`) — serves the React Mini App frontend
2. **Web Service** (`bingo-api`) — FastAPI HTTP API (uvicorn)
3. **Background Worker** (`bingo-bot`) — Telegram bot polling

Each runs in its own Python process (own GIL, own DB pool), so neither can
starve the other during live games.

## 1. Set environment variables on Render

For the **web** and **worker** services, set these (Render UI → Environment):

```
BOT_TOKEN = "<from @BotFather>"
ADMIN_IDS = [<your numeric Telegram id>]
BOT_USERNAME = "<your_bot_username>"
MINI_APP_URL = "https://z-one-bingo-patched-1.onrender.com"
VITE_API_URL = "https://z-one-bingo-patched.onrender.com"
GROUP_CHAT_ID = -1001234567890   # optional, for broadcasts
SUPPORT_USERNAME = <optional>
```

`MINI_APP_URL` must be the public HTTPS URL of the static site — this is
what makes the "Open Habesha Bet" button appear and what `bot.py` uses to
register Telegram's menu button on startup.

## 2. Verify

- Visit `https://z-one-bingo-patched.onrender.com/health` → `{"status":"ok"}`
- Open your bot in Telegram, send `/start`
- Tap the menu button or the "Open Habesha Bet" inline button → Mini App loads

## 3. Free-tier note

Render free web services sleep after 15 min idle and cold-start on the next
request (10–30s delay). Acceptable for testing; for production either upgrade
to a paid instance or use a cron ping to `/health` every 10 min to keep it warm.

## Troubleshooting

- **Mini App shows blank screen:** check browser console via Telegram
  Desktop (right-click → Inspect) — usually a missing `dist/` build.
- **401 errors on every API call:** `BOT_TOKEN` in `config.py` doesn't
  match the bot the Mini App was opened from — `initData` is signed
  per-bot.
- **Menu button doesn't appear:** `MINI_APP_URL` wasn't set before
  `bot.py` started — restart the service after setting it.