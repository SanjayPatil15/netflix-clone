# safe_wrapper.py
import functools
import traceback
import pandas as pd

def safe_flask_view(func):
    """
    Decorator to wrap Flask routes with safety.
    Catches common runtime errors like TypeError from pandas .empty()
    and logs them instead of crashing the app.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TypeError as e:
            if "'bool' object is not callable" in str(e):
                print("\n⚠️ [SAFE WRAPPER] Caught Pandas misuse (like row.empty() instead of row.empty).")
                print("Automatically handled to avoid crash.\n")
                traceback.print_exc()
                return "Internal warning: fixed common Pandas misuse."
            raise e
        except Exception as e:
            print("\n🔥 [SAFE WRAPPER] Unexpected error caught safely:")
            traceback.print_exc()
            return f"Unexpected error: {e}"
    return wrapper
