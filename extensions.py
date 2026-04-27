"""
This file stores Flask extensions so they can be imported cleanly
across the whole project.
"""

# Imports SQLAlchemy which is used to interact with the database (tables, queries, etc.)
from flask_sqlalchemy import SQLAlchemy

# Imports LoginManager which handles user login sessions
from flask_login import LoginManager

# Creates a database object that will be linked to the Flask app later
db = SQLAlchemy()

# Creates a login manager object that controls authentication (login/logout)
login_manager = LoginManager()

# If a user tries to access a protected page without logging in,
# Flask-Login will automatically redirect them to the "login" route
login_manager.login_view = "login"