import os
import asyncio
import tempfile
import time
from collections import defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
import yt_dlp
from yt_dlp.utils import DownloadError

# ----------------- Configuration -----------------
BOT_TOKEN = "TELEGRAM_BOT_TOKEN"
MAX_CONCURRENT_DOWNLOADS = 5
TEMP_DIR = tempfile.gettempdir()
MAX_REQUESTS_PER_MIN = 3  # Max 3 requests per user per minute

# Queue for multiple users
download_queue = asyncio.Queue()
# Track requests per user
user_requests = defaultdict(list)

# ----------------- Helper Functions -----------------
async def download_video(url: str, filename: str):
    """
    Downloads a video from Instagram using yt-dlp asynchronously.
    """
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': filename,
        'quiet': True,
        'noplaylist': True
    }

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
    return filename

async def process_queue(app):
    sem = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
    while True:
        chat_id, url = await download_queue.get()
        async with sem:
            print(f"[LOG] Processing download for user {chat_id}: {url}")
            msg = await app.bot.send_message(chat_id=chat_id, text="⏳ Downloading your video...")
            tmp_file = os.path.join(TEMP_DIR, f"{chat_id}_video.mp4")
            try:
                # Attempt download
                await download_video(url, tmp_file)
                with open(tmp_file, 'rb') as f:
                    await app.bot.send_video(chat_id=chat_id, video=f)
                await msg.edit_text("✅ Video sent successfully!")
                print(f"[LOG] Video sent successfully for user {chat_id}")
            except DownloadError as e:
                error_text = str(e)
                # Detect private/restricted content
                if "only available for registered users" in error_text or \
                   "Instagram API is not granting access" in error_text:
                    await msg.edit_text("⚠️ This content is private or unavailable.")
                    print(f"[WARN] User {chat_id} tried to download private content.")
                else:
                    await msg.edit_text(f"❌ Error downloading video.")
                    print(f"[ERROR] Failed to download for user {chat_id}: {error_text}")
            except Exception as e:
                await msg.edit_text(f"❌ Unexpected error occurred.")
                print(f"[ERROR] Unexpected error for user {chat_id}: {e}")
            finally:
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
        download_queue.task_done()

# ----------------- Countdown Timer -----------------
async def start_countdown(msg, wait_time):
    while wait_time > 0:
        await asyncio.sleep(1)
        wait_time -= 1
        try:
            await msg.edit_text(f"⚠️ Rate limit exceeded! Please wait {wait_time} seconds.")
        except:
            break
    try:
        await msg.edit_text("✅ You can now send a new video link!")
    except:
        pass

# ----------------- Handlers -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📥 Send me an Instagram video link!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.message.chat_id
    now = time.time()

    # Remove timestamps older than 60 seconds
    user_requests[chat_id] = [t for t in user_requests[chat_id] if now - t < 60]

    if len(user_requests[chat_id]) >= MAX_REQUESTS_PER_MIN:
        earliest_request = min(user_requests[chat_id])
        wait_time = int(60 - (now - earliest_request))

        # Send one initial message and start countdown
        msg = await update.message.reply_text(f"⚠️ Rate limit exceeded! Please wait {wait_time} seconds.")
        asyncio.create_task(start_countdown(msg, wait_time))
        print(f"[WARN] User {chat_id} exceeded request limit. Wait {wait_time}s.")
        return

    # Add current request timestamp
    user_requests[chat_id].append(now)

    # Add to download queue
    await download_queue.put((chat_id, url))
    await update.message.reply_text("✅ Your video request has been queued. Please wait...")
    print(f"[LOG] Queued download for user {chat_id}: {url}")

# ----------------- Startup -----------------
async def on_startup(app):
    asyncio.create_task(process_queue(app))
    print("[LOG] Bot started and queue processor running...")

# ----------------- Main -----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("[LOG] Bot is running...")
    app.run_polling()
