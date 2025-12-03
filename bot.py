import asyncio
from datetime import datetime
from collections import defaultdict
from typing import List

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from openai import OpenAI

from config import BOT_TOKEN, DATETIME_FORMAT, OPENAI_API_KEY, logger
from db import (
    init_db,
    add_message,
    get_messages_last_24h,
    clean_old_messages,
    clear_chat_messages,
    get_message_count
)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# OpenAI client (optional, for better summarization)
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("OpenAI API initialized")
else:
    logger.info("OpenAI API key not provided, using basic summarization")


async def summarize_with_openai(messages: List[tuple]) -> str:
    """Summarize messages using OpenAI API"""
    if not openai_client or not messages:
        return "No messages to summarize."

    # Format messages for summarization
    formatted_messages = []
    for timestamp, username, text in messages:
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        formatted_messages.append(f"[{time_str}] {username}: {text}")

    messages_text = "\n".join(formatted_messages)

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes chat messages from the last 24 hours. Provide a concise summary highlighting key topics, discussions, and important information."
                },
                {
                    "role": "user",
                    "content": f"Please summarize the following chat messages:\n\n{messages_text}"
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return summarize_basic(messages)


def summarize_basic(messages: List[tuple]) -> str:
    """Basic summarization without OpenAI API"""
    if not messages:
        return "No messages found in the last 24 hours."

    total_messages = len(messages)
    unique_users = len(set(msg[1] for msg in messages))

    # Group messages by hour
    hourly_counts = defaultdict(int)
    for timestamp, _, _ in messages:
        hour = timestamp.replace(minute=0, second=0, microsecond=0)
        hourly_counts[hour] += 1

    # Get most active hour
    most_active_hour = max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None

    summary = f"📊 Summary of last 24 hours:\n\n"
    summary += f"• Total messages: {total_messages}\n"
    summary += f"• Active users: {unique_users}\n"

    if most_active_hour:
        summary += f"• Most active hour: {most_active_hour.strftime('%Y-%m-%d %H:%M')}\n"

    # Show sample of recent messages
    summary += f"\n📝 Recent messages:\n"
    recent_messages = messages[-10:]  # Last 10 messages
    for timestamp, username, text in recent_messages:
        time_str = timestamp.strftime("%H:%M")
        preview = text[:50] + "..." if len(text) > 50 else text
        summary += f"  [{time_str}] {username}: {preview}\n"

    return summary


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    await message.answer(
        "👋 Hello! I'm a message summarizer bot.\n\n"
        "I collect messages in this chat and can summarize them.\n"
        "Use /summary to get a summary of messages from the last 24 hours.\n"
        "Use /help for more information."
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    await message.answer(
        "📖 Bot Commands:\n\n"
        "/start - Start the bot\n"
        "/summary - Get a summary of messages from the last 24 hours\n"
        "/stats - Show statistics about stored messages\n"
        "/clear - Clear stored messages (admin only)\n\n"
        "The bot automatically collects messages in groups/channels where it's added."
    )


@dp.message(Command("summary"))
async def cmd_summary(message: Message):
    """Handle /summary command"""
    chat_id = message.chat.id

    # Clean old messages first
    await clean_old_messages()

    # Get messages from last 24 hours
    messages = await get_messages_last_24h(chat_id)

    if not messages:
        await message.answer("No messages found in the last 24 hours.")
        return

    # Show processing message
    processing_msg = await message.answer("⏳ Generating summary...")

    # Generate summary
    if openai_client:
        summary = await summarize_with_openai(messages)
    else:
        summary = summarize_basic(messages)

    # Send summary
    await processing_msg.edit_text(summary)


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command"""
    chat_id = message.chat.id
    await clean_old_messages()

    messages = await get_messages_last_24h(chat_id)

    if not messages:
        await message.answer("No messages stored for this chat.")
        return

    unique_users = len(set(msg[1] for msg in messages))
    oldest_message = min(msg[0] for msg in messages)
    newest_message = max(msg[0] for msg in messages)

    stats = (
        f"📈 Statistics for last 24 hours:\n\n"
        f"• Total messages: {len(messages)}\n"
        f"• Unique users: {unique_users}\n"
        f"• Oldest message: {oldest_message.strftime(DATETIME_FORMAT)}\n"
        f"• Newest message: {newest_message.strftime(DATETIME_FORMAT)}"
    )

    await message.answer(stats)


@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    """Handle /clear command"""
    chat_id = message.chat.id

    # Check if user is admin (basic check)
    if message.chat.type in ['group', 'supergroup']:
        member = await bot.get_chat_member(chat_id, message.from_user.id)
        if member.status not in ['administrator', 'creator']:
            await message.answer("❌ Only administrators can clear messages.")
            return

    deleted_count = await clear_chat_messages(chat_id)
    await message.answer(f"✅ Cleared {deleted_count} messages for this chat.")


@dp.message()
async def handle_message(message: Message):
    """Handle all incoming messages"""
    # Skip bot commands
    if message.text and message.text.startswith('/'):
        return

    # Skip messages from bots
    if message.from_user.is_bot:
        return

    chat_id = message.chat.id
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    text = message.text or message.caption or "[Media message]"
    timestamp = datetime.now()

    # Store message in database
    await add_message(chat_id, username, text, timestamp)

    # Periodically clean old messages (every 100 messages)
    message_count = await get_message_count(chat_id)
    if message_count > 0 and message_count % 100 == 0:
        await clean_old_messages()

    logger.debug(f"Stored message from {username} in chat {chat_id}")


async def periodic_cleanup():
    """Periodically clean old messages"""
    while True:
        await asyncio.sleep(3600)  # Run every hour
        await clean_old_messages()
        logger.info("Periodic cleanup completed")


async def main():
    """Main function to start the bot"""
    logger.info("Starting bot...")

    # Initialize database
    await init_db()

    # Start periodic cleanup task
    asyncio.create_task(periodic_cleanup())

    # Start polling
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
