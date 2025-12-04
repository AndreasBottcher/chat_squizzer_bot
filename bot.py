import asyncio
import re
from datetime import datetime
from collections import defaultdict
from typing import List

import nltk
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

from config import BOT_TOKEN, DATETIME_FORMAT, DATETIME_FORMAT_SHORT, TOP_USERS_COUNT, TOP_NOUNS_COUNT, SUMMARY_PERIOD_HOURS, NLTK_DATA_DIR, logger

# Language configuration - Russian only
LANGUAGE = 'russian'
LANGUAGE_CODE = LANGUAGE[0:3]

# Set custom NLTK data directory
nltk.data.path.insert(0, str(NLTK_DATA_DIR))

# Download required NLTK data
def _download_nltk_data():
    """Download required NLTK data if not present"""
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        logger.info(f"Downloading NLTK punkt tokenizer to {NLTK_DATA_DIR}...")
        nltk.download('punkt_tab', quiet=True, download_dir=str(NLTK_DATA_DIR))

    try:
        nltk.data.find(f'taggers/averaged_perceptron_tagger_{LANGUAGE_CODE}')
    except LookupError:
        logger.info(f"Downloading NLTK POS tagger for {LANGUAGE} to {NLTK_DATA_DIR}...")
        nltk.download(f'averaged_perceptron_tagger_{LANGUAGE_CODE}', quiet=True, download_dir=str(NLTK_DATA_DIR))

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        logger.info(f"Downloading NLTK stopwords to {NLTK_DATA_DIR}...")
        nltk.download('stopwords', quiet=True, download_dir=str(NLTK_DATA_DIR))


# Initialize NLTK data
_download_nltk_data()

# Load stopwords for the configured language
try:
    STOPWORDS = set(stopwords.words(LANGUAGE))
    logger.info(f"Loaded NLTK stopwords for language: {LANGUAGE}")
except LookupError as e:
    logger.error(f"Stopwords for {LANGUAGE} not found in NLTK: {e}")
    raise ValueError(f"Stopwords for language '{LANGUAGE}' are not available in NLTK. Please install the required NLTK data or use a supported language.")
from db import (
    init_db,
    add_message,
    get_messages_period,
    clean_old_messages,
    clear_chat_messages
)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def extract_nouns(text: str) -> List[str]:
    """Extract nouns from text using NLTK"""
    # Skip media messages
    if text == "[Медиа сообщение]":
        return []

    # Remove URLs and mentions
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'@\w+', '', text)

    # Use NLTK for POS tagging with configured language
    tokens = word_tokenize(text.lower(), language=LANGUAGE)
    tagged = pos_tag(tokens, lang=LANGUAGE[0:3])

    # Extract nouns (NN, NNS, NNP, NNPS)
    nouns = [
        word for word, pos in tagged
        if pos == 'S' and len(word) > 2 and word not in STOPWORDS
    ]

    return nouns


def get_top_nouns(messages: List[tuple]) -> List[tuple]:
    """Get top N most used nouns from messages"""
    noun_counts = defaultdict(int)

    for _, _, text in messages:
        nouns = extract_nouns(text)
        for noun in nouns:
            noun_counts[noun] += 1

    # Sort by count and return top N
    top_nouns = sorted(noun_counts.items(), key=lambda x: x[1], reverse=True)[:TOP_NOUNS_COUNT]
    return top_nouns


def summarize_basic(messages: List[tuple], period_hours: int) -> str:
    """Basic summarization without OpenAI API"""
    if not messages:
        return f"Сообщений за последние {period_hours}ч не найдено."

    total_messages = len(messages)
    unique_users = len(set(msg[1] for msg in messages))

    # Count messages per user
    user_counts = defaultdict(int)
    for _, username, _ in messages:
        user_counts[username] += 1

    # Get top N most active users
    top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:TOP_USERS_COUNT]

    # Group messages by hour
    hourly_counts = defaultdict(int)
    for timestamp, _, _ in messages:
        hour = timestamp.replace(minute=0, second=0, microsecond=0)
        hourly_counts[hour] += 1

    # Get most active hour
    most_active_hour = max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None

    # Get top nouns
    top_nouns = get_top_nouns(messages)

    summary = f"📊 Сводка за последние {period_hours}ч:\n\n"
    summary += f"• Всего сообщений: {total_messages}\n"
    summary += f"• Активных пользователей: {unique_users}\n"

    # Add top N most active users
    if top_users:
        summary += f"\n👥 Топ {TOP_USERS_COUNT} самых активных пользователей:\n"
        for i, (username, count) in enumerate(top_users, 1):
            summary += f"  {i}. @{username}: {count} сообщений\n"

    # Add top nouns
    if top_nouns:
        summary += f"\n📝 Топ {TOP_NOUNS_COUNT} самых используемых существительных (кол-во раз):\n"
        for i, (noun, count) in enumerate(top_nouns, 1):
            summary += f"  {i}. {noun}: {count}\n"

    if most_active_hour:
        summary += f"\n• Самый активный час: {most_active_hour.strftime(DATETIME_FORMAT_SHORT)}\n"

    return summary


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    await message.answer(
        "👋 Привет! Я бот для суммирования сообщений.\n\n"
        "Я собираю сообщения в этом чате и могу их суммировать.\n"
        f"Используйте /summary для получения сводки сообщений за последние {SUMMARY_PERIOD_HOURS}ч.\n"
        "Используйте /help для получения дополнительной информации."
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    await message.answer(
        "📖 Команды бота:\n\n"
        "/start - Запустить бота\n"
        f"/summary - Получить сводку сообщений за последние {SUMMARY_PERIOD_HOURS}ч\n"
        "/stats - Показать статистику сохраненных сообщений\n"
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
        await message.answer(f"Сообщений за последние {SUMMARY_PERIOD_HOURS}ч не найдено.")
        return

    # Generate summary
    summary = summarize_basic(messages, SUMMARY_PERIOD_HOURS)

    # Send summary
    await message.answer(summary)


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command"""
    chat_id = message.chat.id

    messages = await get_messages_period(chat_id, SUMMARY_PERIOD_HOURS)

    if not messages:
        await message.answer("Для этого чата не сохранено сообщений.")
        return

    unique_users = len(set(msg[1] for msg in messages))
    oldest_message = min(msg[0] for msg in messages)
    newest_message = max(msg[0] for msg in messages)

    stats = (
        f"📈 Статистика за последние {SUMMARY_PERIOD_HOURS}ч:\n\n"
        f"• Всего сообщений: {len(messages)}\n"
        f"• Уникальных пользователей: {unique_users}\n"
        f"• Самое старое сообщение: {oldest_message.strftime(DATETIME_FORMAT)}\n"
        f"• Самое новое сообщение: {newest_message.strftime(DATETIME_FORMAT)}"
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
            await message.answer("❌ Только администраторы могут очищать сообщения.")
            return

    deleted_count = await clear_chat_messages(chat_id)
    await message.answer(f"✅ Очищено {deleted_count} сообщений для этого чата.")


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
    username = message.from_user.username or message.from_user.first_name or "Неизвестно"
    text = message.text or message.caption or "[Медиа сообщение]"
    timestamp = datetime.now()

    # Store message in database
    await add_message(chat_id, username, text, timestamp)

    logger.debug(f"Stored message from {username} in chat {chat_id}")


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


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
