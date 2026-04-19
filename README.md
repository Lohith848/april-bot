# 🌸 April — Your Personal 24/7 AI Assistant

April is your private Telegram AI assistant that:
- Lives in **Telegram** (works on your phone and laptop)
- Runs **24/7 on the cloud** (even when your devices are off)
- Uses **Llama 3.3 70B** via Groq — the best free AI model
- **Remembers your conversations** with SQLite
- Knows **your personal info** — your own private AI

---

## 📁 Project Structure

```
april-bot/
├── bot.py            ← Main bot (don't need to edit)
├── memory.py         ← SQLite memory (don't need to edit)
├── config.py         ← Config loader (don't need to edit)
├── personal_info.py  ← ✏️ YOUR INFO — edit this!
├── requirements.txt  ← Python packages
├── .env.example      ← Template → copy to .env
├── .env              ← Your secrets (create this)
├── .gitignore        ← Keeps .env safe from git
├── Procfile          ← Railway deployment
└── railway.json      ← Railway config
```

---

## 🚀 SETUP GUIDE (Step by Step)

### STEP 1 — Create Your Telegram Bot

1. Open Telegram → Search **@BotFather** → tap it
2. Send `/newbot`
3. Give it a name: `April`
4. Give it a username: `april_yourname_bot` (must end in `bot`)
5. BotFather will give you a **token** that looks like:
   ```
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. **Copy and save this token** — you'll need it

---

### STEP 2 — Get Your Telegram Chat ID

1. Open Telegram → Search **@userinfobot** → tap it
2. Send `/start`
3. It will reply with your **Id** number, e.g. `123456789`
4. **Copy and save this number**

---

### STEP 3 — Get Your Free Groq API Key

1. Go to **https://console.groq.com**
2. Sign up for free (Google login works)
3. Go to **API Keys** → click **Create API Key**
4. Give it a name: `April`
5. **Copy and save the key** (starts with `gsk_...`)

Free limits: **14,400 requests/day** — plenty for personal use.

---

### STEP 4 — Fill In Your Personal Info

Open `personal_info.py` and fill in your details:

```python
YOUR_NAME = "Your Name"
YOUR_AGE = "25"
YOUR_LOCATION = "Your City, Country"
YOUR_OCCUPATION = "What you do"
YOUR_LANGUAGES = "Tamil, English"

YOUR_INTERESTS = """
- coding and building things
- cricket
- music (add your interests)
"""

YOUR_GOALS = """
- learning machine learning
- building a startup
- (add your goals)
"""
```

The more you fill in, the better April knows you!

---

### STEP 5 — Create Your .env File

In the `april-bot/` folder, copy `.env.example` → create a new file called `.env`:

```
TELEGRAM_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OWNER_CHAT_ID=123456789
WEBHOOK_URL=
PORT=8080
```

Leave `WEBHOOK_URL` empty for now (we'll fill it in Step 7 for cloud).

---

### STEP 6 — Test Locally First

Install Python 3.10+ if you don't have it.

Open terminal in the `april-bot/` folder:

```bash
# Install dependencies
pip install -r requirements.txt

# Run April locally
python bot.py
```

You should see:
```
✅ April is live! Owner chat ID: 123456789
```

Open Telegram → find your bot → send `/start`

April should respond! ✅

Press `Ctrl+C` to stop the local bot before deploying to cloud.

---

### STEP 7 — Deploy to Railway (24/7 Cloud)

This makes April run forever, even when your laptop is off.

#### A) Push to GitHub

```bash
cd april-bot
git init
git add .
git commit -m "April bot - initial commit"
```

Create a **private** repo on GitHub (important: private so your code is safe).

```bash
git remote add origin https://github.com/YOURUSERNAME/april-bot.git
git push -u origin main
```

**Note:** `.env` is in `.gitignore` so your secrets are NEVER uploaded. ✅

#### B) Deploy on Railway

1. Go to **https://railway.app** → Sign up free with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `april-bot` repository
4. Railway will start building automatically

#### C) Add Environment Variables on Railway

1. In Railway dashboard → click your project → **Variables** tab
2. Add these one by one:

| Variable | Value |
|---|---|
| `TELEGRAM_TOKEN` | your bot token |
| `GROQ_API_KEY` | your groq key |
| `OWNER_CHAT_ID` | your chat id |
| `PORT` | `8080` |

Don't add `WEBHOOK_URL` yet — we'll get it next.

#### D) Get Your Railway URL & Set Webhook

1. In Railway → your project → **Settings** tab
2. Under **Networking** → click **Generate Domain**
3. You'll get a URL like: `april-production-xxxx.up.railway.app`
4. Now add the final variable:

| Variable | Value |
|---|---|
| `WEBHOOK_URL` | `https://april-production-xxxx.up.railway.app` |

5. Railway will auto-redeploy with the webhook enabled

#### E) Verify It's Working

Open Telegram → send `/start` to your bot

If April responds → **you're done!** 🎉

She's now running 24/7 on the cloud.

---

## 📱 Using April

| Command | What it does |
|---|---|
| Just type anything | April will respond |
| `/start` | Wake her up / greeting |
| `/help` | Show all commands |
| `/clear` | Wipe memory (fresh start) |
| `/memory` | See memory stats |
| `/about` | About April |

---

## 🛠️ Updating April's Personal Info

1. Edit `personal_info.py` with your new info
2. Commit and push to GitHub:
   ```bash
   git add personal_info.py
   git commit -m "Update personal info"
   git push
   ```
3. Railway auto-deploys the update in ~1 minute

---

## 🔒 Privacy & Security

- `.env` is in `.gitignore` — your secrets are never on GitHub
- Only YOUR Telegram chat ID can talk to April
- Anyone else who finds the bot gets: `🔒 I'm a private assistant. Access denied.`
- April refuses to reveal her system prompt

---

## 💡 Tips

- **April knows Tamil!** Just message her in Tamil — she'll reply in Tamil
- **Give her context** — the more you tell her, the better she helps
- **Update `personal_info.py`** whenever something changes in your life
- **Railway free tier** gives you $5/month credit — a simple bot costs ~$0.50-1/month

---

## 🆘 Troubleshooting

**April doesn't respond:**
- Check Railway logs (Dashboard → your project → Logs tab)
- Make sure all 4 env variables are set in Railway
- Make sure `WEBHOOK_URL` doesn't have a trailing slash

**"Configuration errors" on startup:**
- Check your `.env` file — all 3 required values must be filled

**Groq rate limit error:**
- You've hit the free tier limit — wait until next day (resets daily)

**Bot responds to others:**
- Double-check `OWNER_CHAT_ID` is YOUR chat ID from @userinfobot

---

*Built with ❤️ — April is yours, forever.*
