import os
import sys
import traceback

backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

log_file = os.path.join(backend_dir, "server.log")
log_fp = open(log_file, "a", encoding="utf-8", buffering=1)
sys.stdout = log_fp
sys.stderr = log_fp

try:
    print(f"\n[BACKGROUND SERVICE] Menginisialisasi Uvicorn di http://127.0.0.1:8000 ...", file=log_fp)
    import uvicorn
    from app import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
except Exception as e:
    print(f"[ERROR] {e}", file=log_fp)
    traceback.print_exc(file=log_fp)
