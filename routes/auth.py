"""
routes/auth.py
--------------
Handles user registration, login, and logout.

A Blueprint is a mini Flask app you can plug into the main app.
This one has the URL prefix "" (no prefix) so URLs are /register, /login, /logout.
"""

from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import check_password_hash, generate_password_hash
from pymongo.errors import PyMongoError

from models.user import User, create_user, find_user_by_email, find_user_by_username

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # If already logged in, go to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        # --- Server-side validation ---
        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not email or "@" not in email:
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if not errors:
            db = current_app.db
            try:
                if find_user_by_email(db, email):
                    errors.append("An account with that email already exists.")
                if find_user_by_username(db, username):
                    errors.append("That username is already taken.")
            except PyMongoError as db_err:
                current_app.logger.error(f"Database error during registration check: {db_err}")
                flash("Database connection error: Could not reach MongoDB Atlas. Please verify that your network access (0.0.0.0/0) is configured and MONGO_URI is active.", "danger")
                return render_template("auth/register.html", username=username, email=email), 503

        if errors:
            for err in errors:
                flash(err, "danger")
            # Re-render the form with the values the user typed
            return render_template("auth/register.html",
                                   username=username, email=email)

        # --- All good — create the user ---
        hashed = generate_password_hash(password).decode("utf-8")
        db = current_app.db
        try:
            create_user(db, username, email, hashed)
        except PyMongoError as db_err:
            current_app.logger.error(f"Database error creating user: {db_err}")
            flash("Database error: Could not save your account to the database. Please try again.", "danger")
            return render_template("auth/register.html", username=username, email=email), 503

        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        db = current_app.db
        try:
            user_doc = find_user_by_email(db, email)
        except PyMongoError as db_err:
            current_app.logger.error(f"Database error during login: {db_err}")
            flash("Database connection error: Could not connect to MongoDB Atlas. Please ensure network access (0.0.0.0/0) is enabled and MONGO_URI is configured.", "danger")
            return render_template("auth/login.html", email=email), 503

        if not user_doc or not check_password_hash(user_doc["password_hash"], password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", email=email)

        user = User(user_doc)
        login_user(user, remember=remember)
        flash(f"Welcome back, {user.username}!", "success")

        # If the user was redirected here from a protected page, send them back
        next_page = request.args.get("next")
        return redirect(next_page or url_for("dashboard.index"))

    return render_template("auth/login.html")


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
