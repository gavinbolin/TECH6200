from app import app

if __name__ == "__main__":
    # For Windows development, use Waitress
    try:
        from waitress import serve
        print("Starting server with Waitress on http://localhost:8000")
        serve(app, host='0.0.0.0', port=8000)
    except ImportError:
        # Fallback to Flask development server (only in development)
        import os
        debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
        print(f"Waitress not available, using Flask development server (debug={debug})")
        app.run(debug=debug)
