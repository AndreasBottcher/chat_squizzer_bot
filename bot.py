import asyncio
import re
from collections import defaultdict
from datetime import datetime
from typing import List

import nltk
import pymorphy3
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize

from config import (
    BOT_TOKEN,
    DATETIME_FORMAT_SHORT,
    NLTK_DATA_DIR,
    SUMMARY_PERIOD_HOURS,
    TOP_NOUNS_COUNT,
    TOP_USERS_COUNT,
    logger,
)
from db import (
    add_message,
    clean_old_messages,
    clear_chat_messages,
    get_messages_period,
    init_db,
)

# Language configuration - Russian only
LANGUAGE = "russian"
LANGUAGE_CODE = LANGUAGE[0:3]

# Set custom NLTK data directory
nltk.data.path.insert(0, str(NLTK_DATA_DIR))


# Download required NLTK data
def _download_nltk_data():
    """Download required NLTK data if not present"""
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        logger.info(f"Downloading NLTK punkt tokenizer to {NLTK_DATA_DIR}...")
        nltk.download("punkt_tab", quiet=True, download_dir=str(NLTK_DATA_DIR))

    try:
        nltk.data.find(f"taggers/averaged_perceptron_tagger_{LANGUAGE_CODE}")
    except LookupError:
        logger.info(f"Downloading NLTK POS tagger for {LANGUAGE} to {NLTK_DATA_DIR}...")
        nltk.download(
            f"averaged_perceptron_tagger_{LANGUAGE_CODE}",
            quiet=True,
            download_dir=str(NLTK_DATA_DIR),
        )

    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        logger.info(f"Downloading NLTK stopwords to {NLTK_DATA_DIR}...")
        nltk.download("stopwords", quiet=True, download_dir=str(NLTK_DATA_DIR))


# Initialize NLTK data
_download_nltk_data()

# Load stopwords for the configured language
try:
    STOPWORDS = set(stopwords.words(LANGUAGE))
    logger.info(f"Loaded NLTK stopwords for language: {LANGUAGE}")
except LookupError as e:
    logger.error(f"Stopwords for {LANGUAGE} not found in NLTK: {e}")
    raise ValueError(
        f"Stopwords for language '{LANGUAGE}' are not available in NLTK. Please install the required NLTK data or use a supported language."
    )

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
morph = pymorphy3.MorphAnalyzer()


def extract_nouns(text: str) -> List[str]:
    """Extract nouns from text using NLTK"""
    # Skip media messages
    if text == "[Медиа сообщение]":
        return []

    # Remove URLs and mentions
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"@\w+", "", text)

    # Use NLTK for POS tagging with configured language
    tokens = word_tokenize(text.lower(), language=LANGUAGE)
    tagged = pos_tag(tokens, lang=LANGUAGE[0:3])

    # Extract nouns
    nouns = [
        morph.parse(word)[0].normal_form
        for word, pos in tagged
        if pos == "S" and len(word) > 2 and word not in STOPWORDS
    ]

    return nouns


def get_top_nouns(messages: List[tuple]) -> List[tuple]:
    """Get top N most used nouns from messages"""
    noun_counts = defaultdict(int)

    for _, _, _, text in messages:
        nouns = extract_nouns(text)
        for noun in nouns:
            noun_counts[noun] += 1

    # Sort by count and return top N
    top_nouns = sorted(noun_counts.items(), key=lambda x: x[1], reverse=True)[
        :TOP_NOUNS_COUNT
    ]
    return top_nouns


async def summarize_basic(
    chat_id: int, messages: List[tuple], period_hours: int
) -> str:
    """Basic summarization without OpenAI API"""
    if not messages:
        return f"Сообщений за последние {period_hours}ч не найдено."

    total_messages = len(messages)
    unique_users = len(set(msg[1] for msg in messages))

    # Count messages per user
    user_counts = defaultdict(int)
    for _, user_id, _, _ in messages:
        user_counts[user_id] += 1

    # Get top N most active users
    top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[
        :TOP_USERS_COUNT
    ]

    # Group messages by hour
    hourly_counts = defaultdict(int)
    for timestamp, _, _, _ in messages:
        hour = timestamp.replace(minute=0, second=0, microsecond=0)
        hourly_counts[hour] += 1

    # Get most active hour
    most_active_hour = (
        max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None
    )

    # Get top nouns
    top_nouns = get_top_nouns(messages)

    summary = f"📊 Сводка за последние {period_hours}ч:\n\n"
    summary += f"• Всего сообщений: {total_messages}\n"
    summary += f"• Активных пользователей: {unique_users}\n"

    # Add top N most active users
    if top_users:
        summary += f"\n👥 Топ {TOP_USERS_COUNT} самых активных пользователей (пользователь: кол-во сообщений):\n"
        for i, (user_id, count) in enumerate(top_users, 1):
            user = (await bot.get_chat_member(chat_id=chat_id, user_id=user_id)).user
            if user.username:
                username = f"@{user.username}"
            else:
                username = f"tg://user?id={user_id}"
            summary += f"  {i}. {username}: {count}\n"

    # Add top nouns
    if top_nouns:
        summary += f"\n📝 Топ {TOP_NOUNS_COUNT} самых используемых существительных (кол-во раз):\n"
        for i, (noun, count) in enumerate(top_nouns, 1):
            summary += f"  {i}. {noun}: {count}\n"

    if most_active_hour:
        summary += f"\n• Самый активный час: {most_active_hour.strftime(DATETIME_FORMAT_SHORT)}\n"

    return summary


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    await message.answer(
        "📖 Команды бота:\n\n"
        f"/summary - Получить сводку сообщений за последние {SUMMARY_PERIOD_HOURS}ч\n"
        "/clear - Очистить сохраненные сообщения (только для администраторов)\n\n"
        "Бот автоматически собирает сообщения в группах/каналах, куда он добавлен."
    )


@dp.message(Command("summary"))
async def cmd_summary(message: Message):
    """Handle /summary command"""
    chat_id = message.chat.id

    # Get messages from configured period
    messages = await get_messages_period(chat_id, SUMMARY_PERIOD_HOURS)

    if not messages:
        await message.answer(
            f"Сообщений за последние {SUMMARY_PERIOD_HOURS}ч не найдено."
        )
        return

    # Generate summary
    summary = await summarize_basic(chat_id, messages, SUMMARY_PERIOD_HOURS)

    # Send summary
    await message.answer(summary)


@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    """Handle /clear command"""
    chat_id = message.chat.id

    # Check if user is admin (basic check)
    if message.chat.type in ["group", "supergroup"]:
        member = await bot.get_chat_member(chat_id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            await message.answer("❌ Только администраторы могут очищать сообщения.")
            return

    deleted_count = await clear_chat_messages(chat_id)
    await message.answer(f"✅ Очищено {deleted_count} сообщений для этого чата.")


@dp.message()
async def handle_message(message: Message):
    """Handle all incoming messages"""
    # Skip bot commands
    if message.text and message.text.startswith("/"):
        return

    # Skip messages from bots
    if message.from_user.is_bot:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    text = message.text or message.caption or "[Медиа сообщение]"
    timestamp = datetime.now()

    # Store message in database
    await add_message(chat_id, user_id, message.message_id, text, timestamp)

    logger.debug(f"Stored message from {user_id} in chat {chat_id}")


async def periodic_cleanup():
    """Periodically clean old messages"""
    while True:
        await asyncio.sleep(3600)  # Run every hour
        await clean_old_messages(SUMMARY_PERIOD_HOURS)
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
