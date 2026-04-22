"""
Main Flask application file for MatGuide.

This file:
- creates the Flask app
- connects the database
- handles authentication
- handles training logs
- handles the technique library
- handles the public forum
"""

from datetime import datetime
from collections import Counter

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user

from config import Config
from extensions import db, login_manager
from models import User, TrainingLog, Technique, ForumThread, ForumReply
from seed import seed_techniques
from utils import youtube_embed_url


FORUM_CATEGORIES = [
    "Technique Help",
    "Training Advice",
    "Competition",
    "Injuries & Recovery",
    "General Discussion",
]


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()
        seed_techniques()

    @app.route("/")
    def index():
        total_techniques = Technique.query.count()
        total_threads = ForumThread.query.count()
        total_users = User.query.count()

        recent_threads = ForumThread.query.order_by(ForumThread.created_at.desc()).limit(3).all()

        return render_template(
            "index.html",
            total_techniques=total_techniques,
            total_threads=total_threads,
            total_users=total_users,
            recent_threads=recent_threads,
        )

    # ---------------------------
    # Authentication routes
    # ---------------------------

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not email or not password:
                flash("Please enter both an email and a password.", "error")
                return redirect(url_for("register"))

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash("This email is already registered. Please log in instead.", "error")
                return redirect(url_for("login"))

            user = User(email=email)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            user = User.query.filter_by(email=email).first()

            if user is None or not user.check_password(password):
                flash("Invalid email or password.", "error")
                return redirect(url_for("login"))

            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

    # ---------------------------
    # Dashboard and training logs
    # ---------------------------

    @app.route("/dashboard")
    @login_required
    def dashboard():
        logs = (
            TrainingLog.query
            .filter_by(user_id=current_user.id)
            .order_by(TrainingLog.session_date.desc())
            .all()
        )

        total_sessions = len(logs)
        total_minutes = sum(log.duration_minutes or 0 for log in logs)
        avg_session = round(total_minutes / total_sessions, 1) if total_sessions else 0

        # Work out most logged technique by splitting comma-separated technique text
        technique_counter = Counter()
        for log in logs:
            if log.techniques:
                items = [item.strip() for item in log.techniques.split(",") if item.strip()]
                technique_counter.update(items)

        most_logged_technique = technique_counter.most_common(1)[0][0] if technique_counter else "No data yet"

        return render_template(
            "dashboard.html",
            logs=logs,
            total_sessions=total_sessions,
            total_minutes=total_minutes,
            avg_session=avg_session,
            most_logged_technique=most_logged_technique,
        )

    @app.route("/logs/new", methods=["GET", "POST"])
    @login_required
    def new_log():
        if request.method == "POST":
            session_date_str = request.form.get("session_date", "").strip()
            duration_str = request.form.get("duration_minutes", "").strip()
            techniques = request.form.get("techniques", "").strip()
            notes = request.form.get("notes", "").strip()

            try:
                session_date = datetime.strptime(session_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Please enter a valid date.", "error")
                return redirect(url_for("new_log"))

            duration = None
            if duration_str:
                try:
                    duration = int(duration_str)
                except ValueError:
                    flash("Duration must be a number.", "error")
                    return redirect(url_for("new_log"))

            log = TrainingLog(
                session_date=session_date,
                duration_minutes=duration,
                techniques=techniques,
                notes=notes,
                user_id=current_user.id
            )

            db.session.add(log)
            db.session.commit()

            flash("Training log added successfully.", "success")
            return redirect(url_for("dashboard"))

        return render_template("new_log.html")

    @app.route("/logs/<int:log_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_log(log_id):
        log = TrainingLog.query.get_or_404(log_id)

        if log.user_id != current_user.id:
            flash("You do not have permission to edit this log.", "error")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            session_date_str = request.form.get("session_date", "").strip()
            duration_str = request.form.get("duration_minutes", "").strip()
            log.techniques = request.form.get("techniques", "").strip()
            log.notes = request.form.get("notes", "").strip()

            try:
                log.session_date = datetime.strptime(session_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Please enter a valid date.", "error")
                return redirect(url_for("edit_log", log_id=log.id))

            if duration_str:
                try:
                    log.duration_minutes = int(duration_str)
                except ValueError:
                    flash("Duration must be a number.", "error")
                    return redirect(url_for("edit_log", log_id=log.id))
            else:
                log.duration_minutes = None

            db.session.commit()
            flash("Training log updated.", "success")
            return redirect(url_for("dashboard"))

        return render_template("edit_log.html", log=log)

    @app.route("/logs/<int:log_id>/delete", methods=["POST"])
    @login_required
    def delete_log(log_id):
        log = TrainingLog.query.get_or_404(log_id)

        if log.user_id != current_user.id:
            flash("You do not have permission to delete this log.", "error")
            return redirect(url_for("dashboard"))

        db.session.delete(log)
        db.session.commit()
        flash("Training log deleted.", "success")
        return redirect(url_for("dashboard"))

    # ---------------------------
    # Technique library
    # ---------------------------

    @app.route("/techniques")
    def techniques():
        search_query = request.args.get("q", "").strip()
        category_filter = request.args.get("category", "").strip()
        level_filter = request.args.get("level", "").strip()

        query = Technique.query

        if search_query:
            query = query.filter(Technique.name.ilike(f"%{search_query}%"))

        if category_filter:
            query = query.filter(Technique.category == category_filter)

        if level_filter:
            query = query.filter(Technique.level == level_filter)

        techniques_list = query.order_by(Technique.category.asc(), Technique.name.asc()).all()

        categories = sorted({tech.category for tech in Technique.query.all()})
        levels = ["Beginner", "Intermediate", "Advanced"]

        return render_template(
            "techniques.html",
            techniques=techniques_list,
            search_query=search_query,
            categories=categories,
            levels=levels,
            category_filter=category_filter,
            level_filter=level_filter,
        )

    @app.route("/techniques/<int:technique_id>")
    def technique_detail(technique_id):
        technique = Technique.query.get_or_404(technique_id)
        embed_url = youtube_embed_url(technique.youtube_url)

        related_threads = (
            ForumThread.query
            .filter_by(technique_id=technique.id)
            .order_by(ForumThread.created_at.desc())
            .limit(5)
            .all()
        )

        return render_template(
            "technique_detail.html",
            technique=technique,
            embed_url=embed_url,
            related_threads=related_threads,
        )

    # ---------------------------
    # Forum routes
    # ---------------------------

    @app.route("/forum")
    def forum():
        search_query = request.args.get("q", "").strip()
        category_filter = request.args.get("category", "").strip()

        query = ForumThread.query

        if search_query:
            query = query.filter(ForumThread.title.ilike(f"%{search_query}%"))

        if category_filter:
            query = query.filter(ForumThread.category == category_filter)

        threads = query.order_by(ForumThread.created_at.desc()).all()

        return render_template(
            "forum.html",
            threads=threads,
            categories=FORUM_CATEGORIES,
            search_query=search_query,
            category_filter=category_filter,
        )

    @app.route("/forum/new", methods=["GET", "POST"])
    @login_required
    def new_thread():
        techniques = Technique.query.order_by(Technique.name.asc()).all()

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            category = request.form.get("category", "").strip()
            body = request.form.get("body", "").strip()
            technique_id = request.form.get("technique_id", "").strip()

            if not title or not category or not body:
                flash("Please complete the title, category, and post content.", "error")
                return redirect(url_for("new_thread"))

            chosen_technique_id = int(technique_id) if technique_id else None

            thread = ForumThread(
                title=title,
                category=category,
                body=body,
                user_id=current_user.id,
                technique_id=chosen_technique_id,
            )

            db.session.add(thread)
            db.session.commit()

            flash("Discussion thread created successfully.", "success")
            return redirect(url_for("thread_detail", thread_id=thread.id))

        return render_template(
            "new_thread.html",
            categories=FORUM_CATEGORIES,
            techniques=techniques,
        )

    @app.route("/forum/<int:thread_id>", methods=["GET", "POST"])
    def thread_detail(thread_id):
        thread = ForumThread.query.get_or_404(thread_id)

        if request.method == "POST":
            if not current_user.is_authenticated:
                flash("Please log in to reply.", "error")
                return redirect(url_for("login"))

            body = request.form.get("body", "").strip()
            if not body:
                flash("Reply cannot be empty.", "error")
                return redirect(url_for("thread_detail", thread_id=thread.id))

            reply = ForumReply(
                body=body,
                user_id=current_user.id,
                thread_id=thread.id,
            )
            db.session.add(reply)
            db.session.commit()

            flash("Reply posted successfully.", "success")
            return redirect(url_for("thread_detail", thread_id=thread.id))

        replies = ForumReply.query.filter_by(thread_id=thread.id).order_by(ForumReply.created_at.asc()).all()

        return render_template(
            "thread_detail.html",
            thread=thread,
            replies=replies,
        )

    @app.route("/forum/<int:thread_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_thread(thread_id):
        thread = ForumThread.query.get_or_404(thread_id)

        if thread.user_id != current_user.id:
            flash("You do not have permission to edit this thread.", "error")
            return redirect(url_for("forum"))

        techniques = Technique.query.order_by(Technique.name.asc()).all()

        if request.method == "POST":
            thread.title = request.form.get("title", "").strip()
            thread.category = request.form.get("category", "").strip()
            thread.body = request.form.get("body", "").strip()
            technique_id = request.form.get("technique_id", "").strip()
            thread.technique_id = int(technique_id) if technique_id else None

            if not thread.title or not thread.category or not thread.body:
                flash("Please complete all required fields.", "error")
                return redirect(url_for("edit_thread", thread_id=thread.id))

            db.session.commit()
            flash("Thread updated successfully.", "success")
            return redirect(url_for("thread_detail", thread_id=thread.id))

        return render_template(
            "edit_thread.html",
            thread=thread,
            categories=FORUM_CATEGORIES,
            techniques=techniques,
        )

    @app.route("/forum/<int:thread_id>/delete", methods=["POST"])
    @login_required
    def delete_thread(thread_id):
        thread = ForumThread.query.get_or_404(thread_id)

        if thread.user_id != current_user.id:
            flash("You do not have permission to delete this thread.", "error")
            return redirect(url_for("forum"))

        db.session.delete(thread)
        db.session.commit()
        flash("Thread deleted successfully.", "success")
        return redirect(url_for("forum"))

    @app.route("/replies/<int:reply_id>/delete", methods=["POST"])
    @login_required
    def delete_reply(reply_id):
        reply = ForumReply.query.get_or_404(reply_id)

        if reply.user_id != current_user.id:
            flash("You do not have permission to delete this reply.", "error")
            return redirect(url_for("forum"))

        thread_id = reply.thread_id
        db.session.delete(reply)
        db.session.commit()
        flash("Reply deleted successfully.", "success")
        return redirect(url_for("thread_detail", thread_id=thread_id))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)