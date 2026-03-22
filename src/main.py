"""ASGI application entry point for Granian.

Browser CORS is configured on the FastAPI app in ``src/configuration/app.py``
(``CORSMiddleware``), not in this file.
"""

from src.configuration.app import App

app = App().app
