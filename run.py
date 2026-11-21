# run.py
from app import create_app, db
from app.models import User, Home, Donation # Add other models as needed

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Provides a convenient context for the `flask shell` command."""
    return {'db': db, 'User': User, 'Home': Home, 'Donation': Donation}

if __name__ == '__main__':
    app.run(debug=True)
