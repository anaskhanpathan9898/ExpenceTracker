"""
app.py
------
The Flask application factory and entry point.

"Application factory" means we create and configure the Flask app inside a
function (create_app). This makes the app easier to test and avoids circular
import problems between modules.
"""

import os
from flask import Flask, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from pymongo import MongoClient
from bson import ObjectId

from config import Config

# ---------------------------------------------------------------------------
# Global extension instances (not yet tied to any app)
# ---------------------------------------------------------------------------
bcrypt = Bcrypt()
login_manager = LoginManager()


def create_app():
    """Create, configure, and return the Flask application."""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(base_dir, "static")

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)

    # -----------------------------------------------------------------------
    # Initialise extensions with this app instance
    # -----------------------------------------------------------------------
    bcrypt.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"          # redirect here if not logged in
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # -----------------------------------------------------------------------
    # MongoDB connection — stored on app so routes can reach it via
    # current_app.db
    # -----------------------------------------------------------------------
    client = MongoClient(app.config["MONGO_URI"])
    app.db = client[app.config["MONGO_DBNAME"]]

    # -----------------------------------------------------------------------
    # Register the user_loader HERE (inside create_app, after init_app)
    # so login_manager is already bound to the app before the decorator runs.
    # This avoids the "Missing user_loader" error caused by registering the
    # loader at module-level before init_app() is called.
    # -----------------------------------------------------------------------
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        user_doc = app.db.users.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            return User(user_doc)
        return None

    # -----------------------------------------------------------------------
    # Register Blueprints (each blueprint = one group of related routes)
    # -----------------------------------------------------------------------
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.transactions import transactions_bp
    from routes.budget import budget_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budget_bp)

    # -----------------------------------------------------------------------
    # Root route — redirect "/" to dashboard or login
    # -----------------------------------------------------------------------
    @app.route("/")
    def index():
        return redirect(url_for("dashboard.index"))

    @app.route("/favicon.ico")
    def favicon():
        return app.send_static_file("images/favicon.svg")

    return app


# ---------------------------------------------------------------------------
# Module-level WSGI application instance (required for Vercel and WSGI servers)
# ---------------------------------------------------------------------------
app = create_app()


# ---------------------------------------------------------------------------
# Run the development server when this file is executed directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # debug=True gives helpful error pages and auto-reloads on file changes
    app.run(debug=True, port=5000)
