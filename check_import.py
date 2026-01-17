import sys
import os
sys.path.append(os.getcwd())
try:
    from backend.api.main import app
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
