# Telegram Message Summarizer Bot

A Telegram bot built with Python and aiogram that collects messages and provides summaries of conversations from the last 24 hours.

## Features

- 📝 Automatically collects messages from chats where the bot is added
- ⏰ Tracks messages from the last 24 hours
- 📊 Provides summaries with statistics
- 🤖 Optional OpenAI integration for intelligent summarization
- 🧹 Automatic cleanup of old messages
- 📈 Statistics command to view message metrics

## Prerequisites

- Python 3.13 or higher
- A Telegram bot token (get it from [@BotFather](https://t.me/BotFather))
- (Optional) OpenAI API key for advanced summarization

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```bash
BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here_optional
```

   - `BOT_TOKEN` is required - get it from [@BotFather](https://t.me/BotFather)
   - `OPENAI_API_KEY` is optional - if not provided, the bot will use basic summarization

## Usage

1. Start the bot:
```bash
python bot.py
```

2. Add the bot to your Telegram group or channel

3. Use the following commands:
   - `/start` - Start the bot and see welcome message
   - `/help` - Show help information
   - `/summary` - Get a summary of messages from the last 24 hours
   - `/stats` - Show statistics about stored messages
   - `/clear` - Clear stored messages (admin only)

## How It Works

- The bot stores messages in memory with timestamps
- Messages older than 24 hours are automatically cleaned up
- When you request a summary, it collects all messages from the last 24 hours
- If OpenAI API is configured, it uses GPT-3.5-turbo for intelligent summarization
- Otherwise, it provides a basic summary with statistics and recent messages

## Notes

- Messages are stored in memory, so they will be lost when the bot restarts
- For production use, consider adding a database (SQLite, PostgreSQL, etc.)
- The bot needs to be added to groups/channels to collect messages
- Make sure the bot has permission to read messages in groups

## License

MIT License
