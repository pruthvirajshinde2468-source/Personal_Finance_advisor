import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional

class IntentSchema(BaseModel):
    intent: str = Field(description="One of: log_expense, set_budget, ask_advice, general_chat")
    amount: Optional[float] = Field(description="The monetary amount mentioned, if any", default=None)
    category: Optional[str] = Field(description="The category of expense. e.g., food, transport, shopping, bills, entertainment, other", default=None)
    description: Optional[str] = Field(description="Short description of what was bought or asked", default=None)

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    return genai.Client(api_key=api_key)

conversation_history = {}

def get_history(user_id: int) -> list:
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    return conversation_history[user_id]

def add_to_history(user_id: int, role: str, text: str):
    history = get_history(user_id)
    history.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
    if len(history) > 10:
        conversation_history[user_id] = history[-10:]

def parse_intent(message: str, user_id: int = None) -> dict:
    client = get_client()
    if not client:
        return None
        
    history_text = ""
    if user_id:
        history = get_history(user_id)
        for msg in history[-4:]:
            history_text += f"{msg.role}: {msg.parts[0].text}\n"
            
    prompt = f"Parse the following message into an intent, amount, category, and description.\n"
    if history_text:
        prompt += f"Recent Chat Context for pronoun resolution:\n{history_text}\n"
    prompt += f"Message: '{message}'"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IntentSchema,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error parsing intent with Gemini: {e}")
        return None

def generate_response(user_message: str, context: dict, intent_data: dict, user_id: int = None) -> str:
    client = get_client()
    if not client:
        return None

    system_prompt = """
    You are a sarcastic, witty, but caring older-sibling-style personal finance manager.
    You use dry wit, light sarcasm, and occasional pop culture references, but you are NEVER mean or shaming.
    Always use euros (€) in your responses.
    
    Financial Context:
    - Monthly Budget: €{budget}
    - Total Spent This Month: €{spent}
    - Remaining Budget: €{remaining}
    - Day of Month: {day} / {days_in_month}
    - Spending by Category: {categories}
    
    Intent parsed from user: {intent_data}
    
    Guidelines:
    1. If the user asks if they can afford something, give a clear verdict: YES / NO / WAIT / BUY A CHEAPER VERSION.
    2. Consider the day of the month vs the remaining budget. If they have €30 left and it's the 18th, warn them.
    3. Keep responses concise and natural for a Telegram chat. No markdown formatting unless necessary for emphasis.
    4. Provide the verdict first if asked for advice, then your sarcastic commentary.
    """
    
    formatted_system_prompt = system_prompt.format(
        budget=context.get('monthly_budget', 0),
        spent=context.get('total_spent_this_month', 0),
        remaining=context.get('remaining_budget', 0),
        day=context.get('day_of_month', 1),
        days_in_month=context.get('days_in_month', 30),
        categories=json.dumps(context.get('spent_by_category', {})),
        intent_data=json.dumps(intent_data)
    )

    try:
        contents_to_send = []
        if user_id:
            contents_to_send = get_history(user_id).copy()
            
        contents_to_send.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents_to_send,
            config=types.GenerateContentConfig(
                system_instruction=formatted_system_prompt,
            )
        )
        
        if user_id:
            add_to_history(user_id, "user", user_message)
            add_to_history(user_id, "model", response.text)
            
        return response.text
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'm speechless right now. Probably because of a server error."

def generate_nudge(context: dict) -> str:
    client = get_client()
    if not client:
        return None
        
    system_prompt = f"""
    You are a sarcastic, witty, but caring older-sibling-style personal finance manager.
    The user just logged an expense. Evaluate their current financial state and decide if they need a proactive nudge.
    
    Context:
    - Remaining Budget: €{context.get('remaining_budget')} (out of €{context.get('monthly_budget')})
    - Day of Month: {context.get('day_of_month')} out of {context.get('days_in_month')}
    
    Task:
    If they are spending too fast (e.g., low budget remaining early in the month), give them a funny warning.
    If they are doing great, give them a short compliment.
    If they are just normal, return the exact string "NO_NUDGE".
    Keep it to 1-2 sentences.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt
        )
        text = response.text.strip()
        if "NO_NUDGE" in text or text == "":
            return None
        return text
    except Exception as e:
        return None
