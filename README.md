# Instagram Video Downloader Telegram Bot

A Telegram bot to download Instagram videos. It handles multiple users, rate limits requests, and informs the user if the content is private or unavailable.

---

## Features

- Download Instagram videos in MP4 format.
- Queue system with limited simultaneous downloads.
- Rate limiting: maximum 3 requests per user per minute.
- Detects private/restricted content and warns the user.
- Live countdown timer for rate-limited users.
- Logs download status in the console.

---

## Setup Instructions

### 1. Create a virtual environment

```bash
python -m venv venv
# Instagram Video Downloader Telegram Bot

Download Instagram videos via Telegram with queueing, rate limiting, and private content detection.

---

## Setup

1. **Create & activate virtual environment**  

**Windows:** `venv\Scripts\activate`  
**Linux/macOS:** `source venv/bin/activate`  

2. **Upgrade pip**  
```bash
python -m pip install --upgrade pip

Replace TELEGRAM_BOT_TOKEN with the one u got from BotFather
Run the bot
