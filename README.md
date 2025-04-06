# 🔗 InviteLinkBot™ — Auto Invite Link Generator Bot

A powerful Telegram bot that auto-generates new invite links, revokes old ones, and updates a pinned message in your main channel/group with clickable names.

✅ Fully automated  
♻️ Refreshes links every 10 minutes  
📡 Runs 24/7 on **Koyeb**

---

## 🚀 Features

- 🔗 Auto-create and auto-revoke invite links
- 📌 Updates a pinned message with new links
- 🤖 Works with unlimited channels/groups
- 🔒 Admin-only alerts
- 🧠 No need to host `.env` or `channels.json` — everything is **in-code**

---

## 🧠 Requirements

- Telegram Bot Token
- Telegram User ID (as admin)
- Channel ID where pinned message will be updated
- Message ID of that pinned message
- List of all channel/group IDs where bot is admin (with invite permission)

---

## 🌐 Deploy on Koyeb (Step-by-step)

### 1. 🍴 Fork or Upload Code to GitHub

- Fork this repo or upload your code with `main.py` to a new GitHub repo.

### 2. ✏️ Edit `main.py`

Inside `main.py`, change these variables:

## ✅ How to set environment variables in Koyeb
While deploying:


```python
BOT_TOKEN: Your bot token from @BotFather

ADMIN_ID: Your own Telegram user ID (numeric)

TARGET_CHANNEL_ID: The channel ID where pinned message lives (e.g. -100xxxxxxxxxx)

MESSAGE_ID: The message ID that should be edited

CHANNELS: A space-separated list of all your channel/group IDs (example: -1001234567890 -1002345678901 -1003456789012)
```
