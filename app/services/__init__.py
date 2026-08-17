"""Business logic layer.

Routers stay thin: they parse requests, call a service, render a response.
Future agent features plug in here as additional service modules so they can be
called from routes, background jobs or tests without touching HTTP concerns.
"""
