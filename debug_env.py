
import sys
import os

print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    import backend
    print(f"Backend path: {backend.__file__}")
except ImportError as e:
    print(f"Import backend failed: {e}")

try:
    import engine
    print(f"Engine path: {engine.__file__}")
except ImportError as e:
    print(f"Import engine failed: {e}")

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
print("Added backend to path.")

try:
    import engine
    print(f"Engine path after add: {engine.__file__}")
    import engine.timetabling_engine
    print("Import engine.timetabling_engine success")
except ImportError as e:
    print(f"Import engine after add failed: {e}")
except Exception as e:
    print(f"Other error: {e}")
