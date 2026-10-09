"""Dev/VM entry point: `flask --app wsgi run` or `python wsgi.py`.

Not for production anywhere outside the isolated CTF VM.
"""
from forgotten_admin import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
