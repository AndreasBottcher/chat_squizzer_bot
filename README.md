# Telegram Message Summarizer Bot

A Telegram bot built with Python and aiogram that collects messages and provides summaries of conversations from the last {SUMMARY_PERIOD_HOURS} hours.

## Features

- 📝 Automatically collects messages from chats where the bot is added
- ⏰ Tracks messages from the last {SUMMARY_PERIOD_HOURS} hours
- 📊 Provides summaries with statistics
- 🧹 Automatic cleanup of old messages
- 📈 Statistics command to view message metrics

## Prerequisites

- Python 3.13 or higher
- A Telegram bot token (get it from [@BotFather](https://t.me/BotFather))
- `uv` or `docker`

## Installation

0. Clone or download this repository

### Local installation

1. Install dependencies:
```bash
uv sync
```

2. Create a `.env` file in the project root:
```bash
BOT_TOKEN=your_telegram_bot_token_here
```

   - `BOT_TOKEN` is required - get it from [@BotFather](https://t.me/BotFather)
   - (other configurable variables you can see in `config.py` and in .env.example)

3. Start the bot:
```bash
python bot.py
```

### Docker image

1. Build docker image:
```bash
docker build -t chat_squizzer_bot .
```

2. Create a `.env` file in the working directory on the host machine (otherwise you should pass this parameters to `docker run`):
```bash
BOT_TOKEN=your_telegram_bot_token_here
```

   - `BOT_TOKEN` is required - get it from [@BotFather](https://t.me/BotFather)
   - set `DB_PATH` (e.g. `/app/db/messages.db`)
   - (other configurable variables you can see in `config.py` and in .env.example)

3. Start the contaner:
```bash
docker run -v /my_host_machine/path:/app/db --env-file=.env chat_bot:latest  # -v mount volume to make sqlite db persistent
```

## Usage

1. Add the bot to your Telegram group or channel

2. Make sure you adjust Group Policy of the bot via @BotFather (bot should have access to messages within group)

3. Use the following commands:
   - `/help` - Show help information
   - `/summary` - Get a summary of messages from the last 24 hours
   - `/clear` - Clear stored messages (admin only)

## How It Works

- The bot stores messages in SQLite database with timestamps
- Messages older than {SUMMARY_PERIOD_HOURS} hours are automatically cleaned up
- When you request a summary, it collects all messages from the last {SUMMARY_PERIOD_HOURS} hours
- It provides a summary with statistics including total messages, active users, top most active users, and most active hour

## Notes

- Messages are stored in SQLite database by default (`messages.db`), so they persist across bot restarts (see 'Docker' section)
- The bot needs to be added to groups/channels to collect messages
- Make sure the bot has permission to read messages in groups

## License

WTFPL License
