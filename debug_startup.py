
import sys
import os

print("--- DEBUG STARTUP ---")
try:
    print("1. Importing utils.time_utils...")
    from backend.utils import time_utils
    print("   Success.")
except ImportError:
    print("   FAILED to import backend.utils.time_utils. Trying 'utils.time_utils'...")
    try:
        from utils import time_utils
        print("   Success (as utils).")
    except Exception as e:
        print(f"   CRITICAL ERROR importing utils: {e}")
except Exception as e:
    print(f"   CRITICAL ERROR importing backend.utils: {e}")

try:
    print("2. Importing engine.scheduler...")
    from backend.engine import scheduler
    print("   Success.")
except ImportError:
    print("   FAILED to import backend.engine.scheduler. Trying 'engine.scheduler'...")
    try:
        from engine import scheduler
        print("   Success (as engine).")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"   CRITICAL ERROR importing engine: {e}")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"   CRITICAL ERROR importing backend.engine: {e}")

print("--- DEBUG END ---")
