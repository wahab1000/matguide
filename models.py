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

from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager


class User(UserMixin, db.Model):
    """
    User model for account creation and authentication.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    logs = db.relationship("TrainingLog", backref="user", lazy=True, cascade="all, delete-orphan")
    threads = db.relationship("ForumThread", backref="author", lazy=True, cascade="all, delete-orphan")
    replies = db.relationship("ForumReply", backref="author", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class TrainingLog(db.Model):
    """
    Stores a user's training session entry.
    """
    id = db.Column(db.Integer, primary_key=True)
    session_date = db.Column(db.Date, nullable=False, default=date.today)
    duration_minutes = db.Column(db.Integer, nullable=True)
    techniques = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Technique(db.Model):
    """
    Stores BJJ techniques with category, level, description, and optional video.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    category = db.Column(db.String(120), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    youtube_url = db.Column(db.String(500), nullable=True)

    threads = db.relationship("ForumThread", backref="related_technique", lazy=True)


class ForumThread(db.Model):
    """
    Stores a public discussion thread.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Optional link to a technique so forum and technique library are integrated
    technique_id = db.Column(db.Integer, db.ForeignKey("technique.id"), nullable=True)

    replies = db.relationship("ForumReply", backref="thread", lazy=True, cascade="all, delete-orphan")


class ForumReply(db.Model):
    """
    Stores replies inside a forum thread.
    """
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey("forum_thread.id"), nullable=False)