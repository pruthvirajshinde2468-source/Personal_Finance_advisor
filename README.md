# AI Personal Finance Telegram Bot

A witty, slightly sarcastic Telegram bot to manage your personal finances using natural language, built with Python, `python-telegram-bot`, and the Gemini API.

## Setup Instructions

### 1. Create a Telegram Bot
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow the prompts to name your bot and choose a username.
3. BotFather will give you a **HTTP API Token**. Copy this token.

### 2. Local Installation
1. Ensure you have Python 3.9+ installed.
2. Clone this repository or open the project folder.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your keys:
   ```
   TELEGRAM_TOKEN=your_bot_token
   GEMINI_API_KEY=your_gemini_api_key (Get one from Google AI Studio)
   ```
5. Run the bot:
   ```bash
   python bot.py
   ```

### 3. Usage
Just talk to it normally!
- "I spent 12 euros on pizza"
- "My monthly budget is 2500 euros"
- "Can I buy a jacket for 90 euros?"

### 4. Deployment (Render / Railway)
To deploy this bot for free 24/7:
1. Push this code to a GitHub repository.
2. Go to [Render](https://render.com) or [Railway](https://railway.app).
3. Create a new "Worker" or "Background Worker" service linked to your repository.
4. Set the Start Command to `python bot.py`.
5. Add your `TELEGRAM_TOKEN` and `GEMINI_API_KEY` as Environment Variables in the service settings.
6. Deploy!
