import sys
import os
from dotenv import load_dotenv

load_dotenv()

from services.sync_service import initial_sync

user_id = "20593336-ce85-4023-ae96-0c4a183b624c"

print(f"Testing sync for user: {user_id}")
try:
    result = initial_sync(user_id)
    print("Sync Success:", result)
except Exception as e:
    import traceback
    print("SYNC FAILED:")
    traceback.print_exc()
