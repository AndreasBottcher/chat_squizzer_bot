# Telegram Message Summarizer Bot

A Telegram bot built with Python and aiogram that collects messages and provides summaries of conversations from the last 24 hours.

## Features

- 📝 Automatically collects messages from chats where the bot is added
- ⏰ Tracks messages from the last 24 hours
- 📊 Provides summaries with statistics
- 🧹 Automatic cleanup of old messages
- 📈 Statistics command to view message metrics

## Prerequisites

- Python 3.13 or higher
- A Telegram bot token (get it from [@BotFather](https://t.me/BotFather))

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -e .
```

3. Create a `.env` file in the project root:
```bash
BOT_TOKEN=your_telegram_bot_token_here
```

   - `BOT_TOKEN` is required - get it from [@BotFather](https://t.me/BotFather)

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

- The bot stores messages in SQLite database with timestamps
- Messages older than 24 hours are automatically cleaned up
- When you request a summary, it collects all messages from the last 24 hours
- It provides a summary with statistics including total messages, active users, top most active users, and most active hour

## Notes

- Messages are stored in SQLite database (`messages.db`), so they persist across bot restarts
- The bot needs to be added to groups/channels to collect messages
- Make sure the bot has permission to read messages in groups

## License

MIT License
