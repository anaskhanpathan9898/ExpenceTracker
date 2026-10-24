"""
app.py
------
The Flask application factory and entry point.

"Application factory" means we create and configure the Flask app inside a
function (create_app). This makes the app easier to test and avoids circular
import problems between modules.
"""

import os
from flask import Flask, redirect, url_for, jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from pymongo import MongoClient
from pymongo.errors import PyMongoError
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

    # Multi-path template resolution for local, nested, and serverless environments
    template_candidates = [
        os.path.join(base_dir, "templates"),
        os.path.join(base_dir, "api", "templates"),
        os.path.join(os.path.dirname(base_dir), "templates"),
        os.path.abspath("templates"),
        os.path.join(os.getcwd(), "templates"),
        os.path.join(os.getcwd(), "api", "templates"),
        "/var/task/templates",
        "/var/task/api/templates",
    ]
    valid_template_dirs = [d for d in template_candidates if os.path.isdir(d)]
    template_dir = valid_template_dirs[0] if valid_template_dirs else os.path.join(base_dir, "templates")

    static_candidates = [
        os.path.join(base_dir, "public", "static"),
        os.path.join(base_dir, "static"),
        os.path.join(base_dir, "api", "static"),
        os.path.abspath("static"),
        os.path.join(os.getcwd(), "public", "static"),
        os.path.join(os.getcwd(), "static"),
        "/var/task/public/static",
        "/var/task/static",
    ]
    valid_static_dirs = [d for d in static_candidates if os.path.isdir(d)]
    static_dir = valid_static_dirs[0] if valid_static_dirs else os.path.join(base_dir, "static")

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)

    # Search all candidate template directories
    if valid_template_dirs:
        import jinja2
        app.jinja_loader = jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(d) for d in valid_template_dirs
        ])

    # Multi-directory static file resolver for serverless environments
    from flask import send_from_directory

    def custom_static(filename):
        for s_dir in valid_static_dirs:
            file_path = os.path.join(s_dir, filename)
            if os.path.isfile(file_path):
                return send_from_directory(s_dir, filename)
        return app.send_static_file(filename)

    app.view_functions['static'] = custom_static

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
    # serverSelectionTimeoutMS=5000 prevents long gateway timeouts in serverless
    # -----------------------------------------------------------------------
    client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=5000)
    app.db = client[app.config["MONGO_DBNAME"]]

    # -----------------------------------------------------------------------
    # Register the user_loader HERE (inside create_app, after init_app)
    # so login_manager is already bound to the app before the decorator runs.
    # Wrapped in try/except so unreachable DB never crashes session checking.
    # -----------------------------------------------------------------------
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user_doc = app.db.users.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                return User(user_doc)
        except Exception:
            return None
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

    # -----------------------------------------------------------------------
    # Production Health & Database Connectivity Diagnostic Endpoint
    # (Safe for public inspection: never reveals credentials, passwords, or full URIs)
    # -----------------------------------------------------------------------
    @app.route("/api/health")
    def health_check():
        uri = app.config.get("MONGO_URI", "")
        is_localhost = "localhost" in uri or "127.0.0.1" in uri
        is_atlas = uri.startswith("mongodb+srv://")
        has_secret_key = bool(app.config.get("SECRET_KEY") and app.config.get("SECRET_KEY") != "fallback-dev-key")

        db_connected = False
        error_info = None
        try:
            # Fast ping with 2-second timeout to check live reachability
            test_client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            test_client.admin.command("ping")
            db_connected = True
        except Exception as exc:
            exc_str = str(exc)
            if "Authentication failed" in exc_str or "bad auth" in exc_str:
                error_info = "Authentication failed: Database username or password in MONGO_URI is invalid."
            elif "ServerSelectionTimeoutError" in type(exc).__name__ or "timeout" in exc_str.lower():
                if is_localhost:
                    error_info = "Localhost connection attempted from cloud: MONGO_URI environment variable is missing in Vercel or deployment was not redeployed after adding it."
                else:
                    error_info = "Connection timed out: Check MongoDB Atlas Network Access (0.0.0.0/0 must be allowed) and cluster state."
            else:
                error_info = f"{type(exc).__name__}: {exc_str.split('@')[-1] if '@' in exc_str else 'Connection error'}"

        return jsonify({
            "status": "healthy" if db_connected else "degraded",
            "database_connected": db_connected,
            "is_atlas_uri": is_atlas,
            "is_localhost_uri": is_localhost,
            "has_production_secret_key": has_secret_key,
            "database_name": app.config.get("MONGO_DBNAME", "unknown"),
            "diagnosis": error_info or "Database connected successfully"
        }), (200 if db_connected else 503)

    # -----------------------------------------------------------------------
    # Global Error Handlers (Ensure application NEVER returns a blank screen)
    # -----------------------------------------------------------------------
    @app.errorhandler(PyMongoError)
    def handle_database_error(e):
        try:
            return render_template(
                "errors/500.html",
                error="Database Connection Error: Unable to reach MongoDB. Please check your Atlas connection string and network whitelist (0.0.0.0/0)."
            ), 503
        except Exception:
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Database Connection Notice — Expense Tracker</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 32px; max-width: 520px; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.4); text-align: center; }}
    .badge {{ display: inline-block; background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; margin-bottom: 16px; }}
    h1 {{ font-size: 22px; margin-bottom: 12px; color: #f1f5f9; }}
    p {{ color: #94a3b8; font-size: 15px; line-height: 1.6; margin-bottom: 24px; }}
    a.btn {{ display: inline-block; background: #6366f1; color: #ffffff; text-decoration: none; font-weight: 600; padding: 10px 24px; border-radius: 8px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">503 Database Notice</div>
    <h1>Database Connection Notice</h1>
    <p>Unable to connect to MongoDB. Please ensure your cloud database credentials (MONGO_URI) and network access (0.0.0.0/0) are active in MongoDB Atlas.</p>
    <a href="/login" class="btn">Return to Login</a>
  </div>
</body>
</html>""", 503

    @app.errorhandler(500)
    def server_error(e):
        try:
            return render_template("errors/500.html", error=str(e)), 500
        except Exception:
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Application Notice — Expense Tracker</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 32px; max-width: 520px; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.4); text-align: center; }}
    .badge {{ display: inline-block; background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; margin-bottom: 16px; }}
    h1 {{ font-size: 22px; margin-bottom: 12px; color: #f1f5f9; }}
    p {{ color: #94a3b8; font-size: 15px; line-height: 1.6; margin-bottom: 24px; }}
    a.btn {{ display: inline-block; background: #6366f1; color: #ffffff; text-decoration: none; font-weight: 600; padding: 10px 24px; border-radius: 8px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">500 Server Notice</div>
    <h1>Application Notice</h1>
    <p>The application encountered an initialization or database condition. Please verify that your MongoDB connection string (MONGO_URI) and SECRET_KEY are configured in Vercel Project Settings.</p>
    <a href="/login" class="btn">Go to Login</a>
  </div>
</body>
</html>""", 500

    @app.errorhandler(404)
    def page_not_found(e):
        try:
            return render_template("errors/404.html", error=str(e)), 404
        except Exception:
            return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Page Not Found — Expense Tracker</title>
  <style>
    body { font-family: sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding: 60px 20px; }
    .card { background: #1e293b; max-width: 480px; margin: 0 auto; padding: 30px; border-radius: 12px; border: 1px solid #334155; }
    a { color: #818cf8; text-decoration: none; font-weight: bold; }
  </style>
</head>
<body>
  <div class="card">
    <h2>404 — Page Not Found</h2>
    <p>The requested page was not found.</p>
    <p><a href="/login">Return to Login</a></p>
  </div>
</body>
</html>""", 404

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
