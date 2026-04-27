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

# Imports datetime so form date strings can be converted into real date objects
from datetime import datetime

# Imports Counter so the dashboard can count the most logged techniques
from collections import Counter

# Imports the Flask tools used for routing, rendering pages, reading forms, redirects, URLs, and messages
from flask import Flask, render_template, request, redirect, url_for, flash

# Imports Flask-Login tools for logging users in/out and checking the current user
from flask_login import login_user, login_required, logout_user, current_user

# Imports or_ so searches can check more than one database field
from sqlalchemy import or_

# Imports the app configuration settings
from config import Config

# Imports the database and login manager objects
from extensions import db, login_manager

# Imports all database models used in this file
from models import User, TrainingLog, Technique, ForumThread, ForumReply

# Imports the function that adds starter techniques to the database
from seed import seed_techniques

# Imports helper function for turning YouTube links into embed links
from utils import youtube_embed_url


# List of categories available for forum threads
FORUM_CATEGORIES = [
    "Technique Help",
    "Training Advice",
    "Competition",
    "Injuries & Recovery",
    "General Discussion",
]


# Function that creates and sets up the Flask application
def create_app():

    # Creates the Flask app object
    app = Flask(__name__)

    # Loads configuration settings from the Config class
    app.config.from_object(Config)

    # Connects the database extension to this app
    db.init_app(app)

    # Connects the login manager extension to this app
    login_manager.init_app(app)

    # Creates an app context so database actions can run during setup
    with app.app_context():

        # Creates database tables if they do not already exist
        db.create_all()

        # Adds starter technique data if the technique table is empty
        seed_techniques()

    # Homepage route
    @app.route("/")
    def index():

        # Counts all techniques in the database
        total_techniques = Technique.query.count()

        # Counts all forum threads in the database
        total_threads = ForumThread.query.count()

        # Counts all registered users in the database
        total_users = User.query.count()

        # Gets the 3 newest forum threads for the homepage
        recent_threads = ForumThread.query.order_by(ForumThread.created_at.desc()).limit(3).all()

        # Renders the homepage and sends the counts/recent threads to the template
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

    # Register route, supports showing the form and submitting it
    @app.route("/register", methods=["GET", "POST"])
    def register():

        # Checks if the user submitted the registration form
        if request.method == "POST":

            # Gets the email from the form, removes spaces, and makes it lowercase
            email = request.form.get("email", "").strip().lower()

            # Gets the password from the form
            password = request.form.get("password", "")

            # Makes sure the user entered both email and password
            if not email or not password:

                # Shows an error message
                flash("Please enter both an email and a password.", "error")

                # Sends the user back to the register page
                return redirect(url_for("register"))

            # Checks if a user with this email already exists
            existing_user = User.query.filter_by(email=email).first()

            # If the email already exists, stop registration
            if existing_user:

                # Shows an error message
                flash("This email is already registered. Please log in instead.", "error")

                # Sends the user to the login page
                return redirect(url_for("login"))

            # Creates a new user object
            user = User(email=email)

            # Hashes the password before saving it
            user.set_password(password)

            # Adds the new user to the database session
            db.session.add(user)

            # Saves the new user permanently
            db.session.commit()

            # Shows a success message
            flash("Account created successfully. Please log in.", "success")

            # Sends the user to the login page
            return redirect(url_for("login"))

        # Shows the register page if the request is GET
        return render_template("register.html")

    # Login route, supports showing the form and submitting it
    @app.route("/login", methods=["GET", "POST"])
    def login():

        # Checks if the login form has been submitted
        if request.method == "POST":

            # Gets and cleans the email from the form
            email = request.form.get("email", "").strip().lower()

            # Gets the password from the form
            password = request.form.get("password", "")

            # Looks for a user with that email
            user = User.query.filter_by(email=email).first()

            # Checks if the user does not exist or the password is wrong
            if user is None or not user.check_password(password):

                # Shows an error message
                flash("Invalid email or password.", "error")

                # Sends user back to login page
                return redirect(url_for("login"))

            # Logs the user in using Flask-Login
            login_user(user)

            # Shows success message
            flash("Logged in successfully.", "success")

            # Sends user to dashboard after login
            return redirect(url_for("dashboard"))

        # Shows login page if the request is GET
        return render_template("login.html")

    # Logout route
    @app.route("/logout")

    # Requires user to be logged in before accessing this route
    @login_required
    def logout():

        # Logs the current user out
        logout_user()

        # Shows confirmation message
        flash("You have been logged out.", "success")

        # Sends user back to homepage
        return redirect(url_for("index"))

    # ---------------------------
    # Dashboard and training logs
    # ---------------------------

    # Dashboard route
    @app.route("/dashboard")

    # Only logged-in users can view the dashboard
    @login_required
    def dashboard():

        # Gets all training logs for the current user, newest first
        logs = (
            TrainingLog.query
            .filter_by(user_id=current_user.id)
            .order_by(TrainingLog.session_date.desc())
            .all()
        )

        # Counts how many sessions the user has logged
        total_sessions = len(logs)

        # Adds up total minutes, using 0 if a duration is missing
        total_minutes = sum(log.duration_minutes or 0 for log in logs)

        # Calculates average session length, or 0 if there are no sessions
        avg_session = round(total_minutes / total_sessions, 1) if total_sessions else 0

        # Creates a counter to track which techniques appear most often
        technique_counter = Counter()

        # Loops through each training log
        for log in logs:

            # Checks if this log has techniques written in it
            if log.techniques:

                # Splits techniques by comma and removes extra spaces
                items = [item.strip() for item in log.techniques.split(",") if item.strip()]

                # Adds those techniques to the counter
                technique_counter.update(items)

        # Gets the most common technique, or fallback text if there is no data
        most_logged_technique = technique_counter.most_common(1)[0][0] if technique_counter else "No data yet"

        # Sends dashboard data to the dashboard template
        return render_template(
            "dashboard.html",
            logs=logs,
            total_sessions=total_sessions,
            total_minutes=total_minutes,
            avg_session=avg_session,
            most_logged_technique=most_logged_technique,
        )

    # Route for adding a new training log
    @app.route("/logs/new", methods=["GET", "POST"])

    # User must be logged in to create a log
    @login_required
    def new_log():

        # Checks if the new log form was submitted
        if request.method == "POST":

            # Gets the date from the form
            session_date_str = request.form.get("session_date", "").strip()

            # Gets the duration from the form
            duration_str = request.form.get("duration_minutes", "").strip()

            # Gets the techniques from the form
            techniques = request.form.get("techniques", "").strip()

            # Gets the notes from the form
            notes = request.form.get("notes", "").strip()

            # Tries to convert the date string into a Python date object
            try:
                session_date = datetime.strptime(session_date_str, "%Y-%m-%d").date()

            # Runs if the date is invalid
            except ValueError:

                # Shows an error message
                flash("Please enter a valid date.", "error")

                # Sends the user back to the new log page
                return redirect(url_for("new_log"))

            # Starts duration as None because it is optional
            duration = None

            # Checks if the user entered a duration
            if duration_str:

                # Tries to convert duration into a number
                try:
                    duration = int(duration_str)

                # Runs if duration is not a valid number
                except ValueError:

                    # Shows an error message
                    flash("Duration must be a number.", "error")

                    # Sends the user back to the new log page
                    return redirect(url_for("new_log"))

            # Creates a new TrainingLog object
            log = TrainingLog(
                session_date=session_date,
                duration_minutes=duration,
                techniques=techniques,
                notes=notes,
                user_id=current_user.id
            )

            # Adds the new log to the database session
            db.session.add(log)

            # Saves the new log permanently
            db.session.commit()

            # Shows success message
            flash("Training log added successfully.", "success")

            # Sends user back to dashboard
            return redirect(url_for("dashboard"))

        # Shows the new log form if request is GET
        return render_template("new_log.html")

    # Route for editing an existing training log
    @app.route("/logs/<int:log_id>/edit", methods=["GET", "POST"])

    # User must be logged in to edit a log
    @login_required
    def edit_log(log_id):

        # Finds the log by ID, or shows 404 if it does not exist
        log = TrainingLog.query.get_or_404(log_id)

        # Makes sure users can only edit their own logs
        if log.user_id != current_user.id:

            # Shows permission error
            flash("You do not have permission to edit this log.", "error")

            # Sends user back to dashboard
            return redirect(url_for("dashboard"))

        # Checks if the edit form was submitted
        if request.method == "POST":

            # Gets updated date from the form
            session_date_str = request.form.get("session_date", "").strip()

            # Gets updated duration from the form
            duration_str = request.form.get("duration_minutes", "").strip()

            # Updates techniques field
            log.techniques = request.form.get("techniques", "").strip()

            # Updates notes field
            log.notes = request.form.get("notes", "").strip()

            # Tries to convert the submitted date into a date object
            try:
                log.session_date = datetime.strptime(session_date_str, "%Y-%m-%d").date()

            # Runs if the date is invalid
            except ValueError:

                # Shows error message
                flash("Please enter a valid date.", "error")

                # Sends user back to the edit page
                return redirect(url_for("edit_log", log_id=log.id))

            # Checks if duration was entered
            if duration_str:

                # Tries to convert duration into an integer
                try:
                    log.duration_minutes = int(duration_str)

                # Runs if duration is not a valid number
                except ValueError:

                    # Shows error message
                    flash("Duration must be a number.", "error")

                    # Sends user back to edit page
                    return redirect(url_for("edit_log", log_id=log.id))

            # If duration is empty, store it as None
            else:
                log.duration_minutes = None

            # Saves changes to the database
            db.session.commit()

            # Shows success message
            flash("Training log updated.", "success")

            # Sends user back to dashboard
            return redirect(url_for("dashboard"))

        # Shows edit form with the current log data
        return render_template("edit_log.html", log=log)

    # Route for deleting a training log
    @app.route("/logs/<int:log_id>/delete", methods=["POST"])

    # User must be logged in to delete a log
    @login_required
    def delete_log(log_id):

        # Finds the log by ID, or shows 404 if it does not exist
        log = TrainingLog.query.get_or_404(log_id)

        # Makes sure users can only delete their own logs
        if log.user_id != current_user.id:

            # Shows permission error
            flash("You do not have permission to delete this log.", "error")

            # Sends user back to dashboard
            return redirect(url_for("dashboard"))

        # Deletes the log from the database session
        db.session.delete(log)

        # Saves the delete action permanently
        db.session.commit()

        # Shows success message
        flash("Training log deleted.", "success")

        # Sends user back to dashboard
        return redirect(url_for("dashboard"))

    # ---------------------------
    # Technique library
    # ---------------------------

    # Route for the technique library page
    @app.route("/techniques")
    def techniques():

        # Gets the search text from the URL
        search_query = request.args.get("q", "").strip()

        # Gets selected category filter from the URL
        category_filter = request.args.get("category", "").strip()

        # Gets selected level filter from the URL
        level_filter = request.args.get("level", "").strip()

        # Starts with all techniques
        query = Technique.query

        # If user searched something, filter techniques by name, description, or category
        if search_query:
            query = query.filter(
                or_(
                    Technique.name.ilike(f"%{search_query}%"),
                    Technique.description.ilike(f"%{search_query}%"),
                    Technique.category.ilike(f"%{search_query}%"),
                )
            )

        # If category filter is selected, only show techniques in that category
        if category_filter:
            query = query.filter(Technique.category == category_filter)

        # If level filter is selected, only show techniques at that level
        if level_filter:
            query = query.filter(Technique.level == level_filter)

        # Orders the final technique list by category, then name
        techniques_list = query.order_by(
            Technique.category.asc(),
            Technique.name.asc()
        ).all()

        # Builds a sorted list of all categories from the database
        categories = sorted({tech.category for tech in Technique.query.all()})

        # Fixed list of possible levels
        levels = ["Beginner", "Intermediate", "Advanced"]

        # Sends technique data and filter values to the template
        return render_template(
            "techniques.html",
            techniques=techniques_list,
            search_query=search_query,
            categories=categories,
            levels=levels,
            category_filter=category_filter,
            level_filter=level_filter,
        )

    # Route for viewing one technique in detail
    @app.route("/techniques/<int:technique_id>")
    def technique_detail(technique_id):

        # Gets the technique by ID, or shows 404 if it does not exist
        technique = Technique.query.get_or_404(technique_id)

        # Converts the normal YouTube URL into an embed URL for iframe use
        embed_url = youtube_embed_url(technique.youtube_url)

        # Gets up to 5 forum threads linked to this technique
        related_threads = (
            ForumThread.query
            .filter_by(technique_id=technique.id)
            .order_by(ForumThread.created_at.desc())
            .limit(5)
            .all()
        )

        # Gets up to 4 other techniques in the same category
        related_techniques = (
            Technique.query
            .filter(
                Technique.category == technique.category,
                Technique.id != technique.id
            )
            .limit(4)
            .all()
        )

        # Sends technique detail data to the template
        return render_template(
            "technique_detail.html",
            technique=technique,
            embed_url=embed_url,
            related_threads=related_threads,
            related_techniques=related_techniques,
        )

    # ---------------------------
    # Forum routes
    # ---------------------------

    # Route for the forum page
    @app.route("/forum")
    def forum():

        # Gets search text from the URL
        search_query = request.args.get("q", "").strip()

        # Gets selected category filter from the URL
        category_filter = request.args.get("category", "").strip()

        # Gets sort option from the URL, defaulting to latest
        sort_by = request.args.get("sort", "latest").strip()

        # Starts with all forum threads
        query = ForumThread.query

        # If user searched something, filter by thread title or body
        if search_query:
            query = query.filter(
                or_(
                    ForumThread.title.ilike(f"%{search_query}%"),
                    ForumThread.body.ilike(f"%{search_query}%")
                )
            )

        # If a category is selected, filter threads by category
        if category_filter:
            query = query.filter(ForumThread.category == category_filter)

        # Gets the filtered threads from the database
        threads = query.all()

        # If selected, sorts threads by highest number of replies
        if sort_by == "most_replies":
            threads = sorted(threads, key=lambda t: len(t.replies), reverse=True)

        # Otherwise sorts by newest thread first
        else:
            threads = sorted(threads, key=lambda t: t.created_at, reverse=True)

        # Sends forum data to the template
        return render_template(
            "forum.html",
            threads=threads,
            categories=FORUM_CATEGORIES,
            search_query=search_query,
            category_filter=category_filter,
            sort_by=sort_by,
        )

    # Route for creating a new forum thread
    @app.route("/forum/new", methods=["GET", "POST"])

    # User must be logged in to create a thread
    @login_required
    def new_thread():

        # Gets all techniques for the optional related technique dropdown
        techniques = Technique.query.order_by(Technique.name.asc()).all()

        # Checks if the new thread form was submitted
        if request.method == "POST":

            # Gets title from form
            title = request.form.get("title", "").strip()

            # Gets category from form
            category = request.form.get("category", "").strip()

            # Gets main post content from form
            body = request.form.get("body", "").strip()

            # Gets optional technique ID from form
            technique_id = request.form.get("technique_id", "").strip()

            # Makes sure required fields are completed
            if not title or not category or not body:

                # Shows error message
                flash("Please complete the title, category, and post content.", "error")

                # Sends user back to new thread form
                return redirect(url_for("new_thread"))

            # Converts technique ID to integer if selected, otherwise stores None
            chosen_technique_id = int(technique_id) if technique_id else None

            # Creates a new forum thread object
            thread = ForumThread(
                title=title,
                category=category,
                body=body,
                user_id=current_user.id,
                technique_id=chosen_technique_id,
            )

            # Adds the new thread to the database session
            db.session.add(thread)

            # Saves the new thread permanently
            db.session.commit()

            # Shows success message
            flash("Discussion thread created successfully.", "success")

            # Sends user to the new thread detail page
            return redirect(url_for("thread_detail", thread_id=thread.id))

        # Shows the new thread form if request is GET
        return render_template(
            "new_thread.html",
            categories=FORUM_CATEGORIES,
            techniques=techniques,
        )

    # Route for viewing a thread and posting replies
    @app.route("/forum/<int:thread_id>", methods=["GET", "POST"])
    def thread_detail(thread_id):

        # Gets the thread by ID, or shows 404 if it does not exist
        thread = ForumThread.query.get_or_404(thread_id)

        # Checks if a reply form was submitted
        if request.method == "POST":

            # If user is not logged in, they cannot reply
            if not current_user.is_authenticated:

                # Shows error message
                flash("Please log in to reply.", "error")

                # Sends user to login page
                return redirect(url_for("login"))

            # Gets reply content from the form
            body = request.form.get("body", "").strip()

            # Prevents empty replies
            if not body:

                # Shows error message
                flash("Reply cannot be empty.", "error")

                # Sends user back to the same thread
                return redirect(url_for("thread_detail", thread_id=thread.id))

            # Creates a new reply object
            reply = ForumReply(
                body=body,
                user_id=current_user.id,
                thread_id=thread.id,
            )

            # Adds the reply to the database session
            db.session.add(reply)

            # Saves the reply permanently
            db.session.commit()

            # Shows success message
            flash("Reply posted successfully.", "success")

            # Reloads the thread page
            return redirect(url_for("thread_detail", thread_id=thread.id))

        # Gets all replies for this thread, oldest first
        replies = ForumReply.query.filter_by(thread_id=thread.id).order_by(ForumReply.created_at.asc()).all()

        # Sends thread and replies to the template
        return render_template(
            "thread_detail.html",
            thread=thread,
            replies=replies,
        )

    # Route for editing a forum thread
    @app.route("/forum/<int:thread_id>/edit", methods=["GET", "POST"])

    # User must be logged in to edit a thread
    @login_required
    def edit_thread(thread_id):

        # Gets the thread by ID, or shows 404 if it does not exist
        thread = ForumThread.query.get_or_404(thread_id)

        # Makes sure users can only edit their own threads
        if thread.user_id != current_user.id:

            # Shows permission error
            flash("You do not have permission to edit this thread.", "error")

            # Sends user back to forum page
            return redirect(url_for("forum"))

        # Gets all techniques for the related technique dropdown
        techniques = Technique.query.order_by(Technique.name.asc()).all()

        # Checks if edit form was submitted
        if request.method == "POST":

            # Updates thread title
            thread.title = request.form.get("title", "").strip()

            # Updates thread category
            thread.category = request.form.get("category", "").strip()

            # Updates thread body
            thread.body = request.form.get("body", "").strip()

            # Gets selected technique ID from form
            technique_id = request.form.get("technique_id", "").strip()

            # Updates linked technique, or sets it to None if blank
            thread.technique_id = int(technique_id) if technique_id else None

            # Makes sure required fields are not empty
            if not thread.title or not thread.category or not thread.body:

                # Shows error message
                flash("Please complete all required fields.", "error")

                # Sends user back to edit form
                return redirect(url_for("edit_thread", thread_id=thread.id))

            # Saves changes to database
            db.session.commit()

            # Shows success message
            flash("Thread updated successfully.", "success")

            # Sends user back to thread detail page
            return redirect(url_for("thread_detail", thread_id=thread.id))

        # Shows edit thread form
        return render_template(
            "edit_thread.html",
            thread=thread,
            categories=FORUM_CATEGORIES,
            techniques=techniques,
        )

    # Route for deleting a forum thread
    @app.route("/forum/<int:thread_id>/delete", methods=["POST"])

    # User must be logged in to delete a thread
    @login_required
    def delete_thread(thread_id):

        # Gets the thread by ID, or shows 404 if it does not exist
        thread = ForumThread.query.get_or_404(thread_id)

        # Makes sure users can only delete their own threads
        if thread.user_id != current_user.id:

            # Shows permission error
            flash("You do not have permission to delete this thread.", "error")

            # Sends user back to forum page
            return redirect(url_for("forum"))

        # Deletes the thread from the database session
        db.session.delete(thread)

        # Saves the delete permanently
        db.session.commit()

        # Shows success message
        flash("Thread deleted successfully.", "success")

        # Sends user back to forum
        return redirect(url_for("forum"))

    # Route for deleting a reply
    @app.route("/replies/<int:reply_id>/delete", methods=["POST"])

    # User must be logged in to delete a reply
    @login_required
    def delete_reply(reply_id):

        # Gets the reply by ID, or shows 404 if it does not exist
        reply = ForumReply.query.get_or_404(reply_id)

        # Makes sure users can only delete their own replies
        if reply.user_id != current_user.id:

            # Shows permission error
            flash("You do not have permission to delete this reply.", "error")

            # Sends user back to forum page
            return redirect(url_for("forum"))

        # Stores the thread ID before deleting the reply, so we can redirect back
        thread_id = reply.thread_id

        # Deletes the reply from the database session
        db.session.delete(reply)

        # Saves the delete permanently
        db.session.commit()

        # Shows success message
        flash("Reply deleted successfully.", "success")

        # Sends user back to the thread the reply belonged to
        return redirect(url_for("thread_detail", thread_id=thread_id))

    # Returns the fully created Flask app
    return app


# Creates the Flask app by calling create_app()
app = create_app()

# Runs the app only when this file is run directly
if __name__ == "__main__":

    # Starts Flask development server with debug mode on
    app.run(debug=True)