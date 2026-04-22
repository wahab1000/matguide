"""
Application configuration.

This file keeps settings in one place so the app is easier to maintain.
For this project we are using SQLite locally because it is simple and
good for a student web app MVP.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Secret key is used by Flask to protect sessions and flash messages.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-this-later")

    # SQLite database stored in the project folder.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "matguide.db")
    )

    # Disables an unnecessary SQLAlchemy warning / overhead feature.
    SQLALCHEMY_TRACK_MODIFICATIONS = False