import os
import sys

# Tambahkan direktori root backend ke path pencarian modul Python
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app

# ASGI Middleware untuk memastikan path routing Vercel selalu sinkron dengan FastAPI
class VercelPathMiddleware:
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            headers = dict(scope.get("headers", []))
            # Vercel menyematkan original path pada x-matched-path
            matched_path = headers.get(b"x-matched-path")
            if matched_path:
                raw_path = matched_path.decode("utf-8")
                # Hapus query string jika ada pada matched_path
                scope["path"] = raw_path.split("?")[0]
            elif scope.get("path", "").startswith("/api/index.py"):
                new_path = scope["path"][len("/api/index.py"):]
                scope["path"] = new_path if new_path else "/"
        await self.asgi_app(scope, receive, send)

# Ekspor handler dan app untuk kompatibilitas penuh Vercel Python runtime
handler = VercelPathMiddleware(app)
app = handler
