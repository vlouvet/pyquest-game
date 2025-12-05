#!/usr/bin/env python3
"""
PyQuest Game - Run Script

This script runs the Flask development server.
For production, use a WSGI server like gunicorn instead.
"""

from pq_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
