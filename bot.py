import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

import db
import ai
import fallback

# Load env variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize database
db.init_db()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    text = ""
    image_bytes = None
    
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        byte_array = await photo_file.download_as_bytearray()
        image_bytes = bytes(byte_array)
        text = update.message.caption or "Here is a receipt. Extract the expense."
    else:
        text = update.message.text
    
    # Try Gemini first
    intent_data = ai.parse_intent(text, user_id=user_id, image_bytes=image_bytes)
    
    # Fallback to Regex if Gemini fails or is not configured
    if not intent_data:
        intent_data = fallback.parse_intent_fallback(text)
        
    intent = intent_data.get('intent')
    amount = intent_data.get('amount')
    category = intent_data.get('category', 'other')
    desc = intent_data.get('description', '')
    
    # Execute database actions
    if intent == "set_budget" and amount is not None:
        db.set_budget(user_id, float(amount))
    elif intent == "log_expense" and amount is not None:
        db.add_transaction(user_id, "expense", category, float(amount), desc)
        
    # Get updated financial context
    fin_context = db.get_financial_context(user_id)
    
    if intent == "analyze_spending":
        fin_context["all_transactions"] = [
            {"date": t["timestamp"], "amount": t["amount"], "category": t["category"], "desc": t["description"]}
            for t in db.get_all_transactions(user_id)
        ]
    
    # Generate Response
    response = ai.generate_response(text, fin_context, intent_data, user_id=user_id)
    if not response:
        response = fallback.get_fallback_response(intent_data, fin_context)
        
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    
    # Check for proactive nudge if an expense was logged
    if intent == "log_expense":
        nudge = ai.generate_nudge(fin_context)
        if nudge:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=nudge)


if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    if not token or token == "your_telegram_bot_token_here":
        print("Please set TELEGRAM_TOKEN in your .env file.")
        exit(1)
        
    application = ApplicationBuilder().token(token).build()
    
    # Handle text messages and photos
    msg_handler = MessageHandler((filters.TEXT | filters.PHOTO) & (~filters.COMMAND), handle_message)
    application.add_handler(msg_handler)
    
    print("Bot is running...")
    application.run_polling()
