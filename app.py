"""
Main application runner.
Uses the application factory pattern to create and run the Flask instance.
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Default development server host and port
    # use_reloader=False prevents Windows subprocess DLL initialization conflicts with PyTorch/shm.dll
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True, use_reloader=False)
