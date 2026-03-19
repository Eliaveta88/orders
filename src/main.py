"""ASGI application entry point for Granian."""

from src.configuration.app import App

app = App().app
