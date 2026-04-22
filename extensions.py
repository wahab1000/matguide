"""
This file stores Flask extensions so they can be imported cleanly
across the whole project.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Database object used across the app
db = SQLAlchemy()

# Login manager used for user sessions
login_manager = LoginManager()

# If a user tries to access a protected page without logging in,
# Flask-Login sends them to this route.
login_manager.login_view = "login"