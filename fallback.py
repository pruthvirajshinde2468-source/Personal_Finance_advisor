import re

def parse_intent_fallback(message: str) -> dict:
    message = message.lower()
    
    # Check for budget setting
    budget_match = re.search(r'budget.*?(\d+(?:\.\d{1,2})?)', message)
    if budget_match:
        return {
            "intent": "set_budget",
            "amount": float(budget_match.group(1)),
            "category": None,
            "description": "budget update"
        }
        
    # Check for expense logging
    expense_match = re.search(r'(spent|bought|paid).*?(\d+(?:\.\d{1,2})?)', message)
    if expense_match:
        amount = float(expense_match.group(2))
        category = "other"
        
        categories = ["food", "transport", "shopping", "bills", "entertainment"]
        for cat in categories:
            if cat in message:
                category = cat
                break
                
        return {
            "intent": "log_expense",
            "amount": amount,
            "category": category,
            "description": message
        }
        
    # If it's a question
    if '?' in message:
        return {
            "intent": "ask_advice",
            "amount": None,
            "category": None,
            "description": message
        }
        
    return {
        "intent": "general_chat",
        "amount": None,
        "category": None,
        "description": message
    }

def get_fallback_response(intent_data: dict, context: dict) -> str:
    intent = intent_data.get("intent")
    if intent == "set_budget":
        return f"Budget set to €{intent_data['amount']}. Don't blow it all in one place."
    elif intent == "log_expense":
        return f"Logged €{intent_data['amount']} for {intent_data['category']}. You have €{context['remaining_budget']} left this month."
    elif intent == "ask_advice":
        return f"I'm in fallback mode without my AI brain. You have €{context['remaining_budget']} left. Use your best judgment!"
    else:
        return "I'm just a simple bot right now. Try logging an expense ('I spent 15 on food') or setting a budget ('Set my budget to 2000')."
