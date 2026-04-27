"""
Database models for MatGuide.

This project uses SQLAlchemy to define the data structure of the app.
The main models are:
- User
- TrainingLog
- Technique
- ForumThread
- ForumReply

This demonstrates structured system design and relational data modelling.
"""

# Imports datetime for timestamps (e.g. when threads/replies are created)
# Imports date for default training log date
from datetime import datetime, date

# UserMixin gives built-in login functionality (like is_authenticated)
from flask_login import UserMixin

# These functions are used to hash and verify passwords securely
from werkzeug.security import generate_password_hash, check_password_hash

# Imports database and login manager from extensions file
from extensions import db, login_manager


# ---------------------------
# User model
# ---------------------------
class User(UserMixin, db.Model):
    """
    User model for account creation and authentication.
    """

    # Unique ID for each user (primary key)
    id = db.Column(db.Integer, primary_key=True)

    # User email (must be unique, cannot be empty, indexed for faster lookup)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)

    # Stores hashed password (NOT plain text)
    password_hash = db.Column(db.String(255), nullable=False)

    # Relationship: one user can have many training logs
    logs = db.relationship("TrainingLog", backref="user", lazy=True, cascade="all, delete-orphan")

    # Relationship: one user can create many forum threads
    threads = db.relationship("ForumThread", backref="author", lazy=True, cascade="all, delete-orphan")

    # Relationship: one user can create many replies
    replies = db.relationship("ForumReply", backref="author", lazy=True, cascade="all, delete-orphan")

    # Function to set (hash) a password before storing it
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    # Function to check if a password matches the stored hash
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


# This tells Flask-Login how to load a user from the session
@login_manager.user_loader
def load_user(user_id):

    # Looks up the user by ID and returns it
    return User.query.get(int(user_id))


# ---------------------------
# Training Log model
# ---------------------------
class TrainingLog(db.Model):
    """
    Stores a user's training session entry.
    """

    # Unique ID for each log
    id = db.Column(db.Integer, primary_key=True)

    # Date of the training session (defaults to today's date)
    session_date = db.Column(db.Date, nullable=False, default=date.today)

    # Duration in minutes (optional)
    duration_minutes = db.Column(db.Integer, nullable=True)

    # Techniques practiced (stored as a comma-separated string)
    techniques = db.Column(db.String(500), nullable=True)

    # Additional notes about the session
    notes = db.Column(db.Text, nullable=True)

    # Foreign key linking this log to a user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


# ---------------------------
# Technique model
# ---------------------------
class Technique(db.Model):
    """
    Stores BJJ techniques with category, level, description, and optional video.
    """

    # Unique ID for each technique
    id = db.Column(db.Integer, primary_key=True)

    # Name of the technique (must be unique)
    name = db.Column(db.String(120), unique=True, nullable=False)

    # Category (e.g. escapes, sweeps, submissions)
    category = db.Column(db.String(120), nullable=False)

    # Difficulty level (Beginner, Intermediate, Advanced)
    level = db.Column(db.String(50), nullable=False)

    # Description explaining the technique
    description = db.Column(db.Text, nullable=False)

    # Optional YouTube link for instructional video
    youtube_url = db.Column(db.String(500), nullable=True)

    # Relationship: one technique can be linked to many forum threads
    threads = db.relationship("ForumThread", backref="related_technique", lazy=True)


# ---------------------------
# Forum Thread model
# ---------------------------
class ForumThread(db.Model):
    """
    Stores a public discussion thread.
    """

    # Unique ID for each thread
    id = db.Column(db.Integer, primary_key=True)

    # Title of the thread
    title = db.Column(db.String(200), nullable=False)

    # Category of the discussion
    category = db.Column(db.String(100), nullable=False)

    # Main body/content of the thread
    body = db.Column(db.Text, nullable=False)

    # Timestamp when thread was created (defaults to current time)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Foreign key linking thread to the user who created it
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Optional link to a technique so forum and technique library are integrated
    technique_id = db.Column(db.Integer, db.ForeignKey("technique.id"), nullable=True)

    # Relationship: one thread can have many replies
    replies = db.relationship("ForumReply", backref="thread", lazy=True, cascade="all, delete-orphan")


# ---------------------------
# Forum Reply model
# ---------------------------
class ForumReply(db.Model):
    """
    Stores replies inside a forum thread.
    """

    # Unique ID for each reply
    id = db.Column(db.Integer, primary_key=True)

    # Content of the reply
    body = db.Column(db.Text, nullable=False)

    # Timestamp when reply was created
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Foreign key linking reply to the user who created it
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Foreign key linking reply to its thread
    thread_id = db.Column(db.Integer, db.ForeignKey("forum_thread.id"), nullable=False)