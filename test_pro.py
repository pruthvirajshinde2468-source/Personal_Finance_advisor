import os
from dotenv import load_dotenv
load_dotenv()
import ai

try:
    print("Testing generate_response with 2.5-pro...")
    res = ai.generate_response("And today I spent 7 euros on groceries", {}, {"intent": "log_expense"})
    print("Result:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
