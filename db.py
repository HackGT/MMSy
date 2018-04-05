from flask import g, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = SQLAlchemy()
        db.init_app(current_app)
        g._database = db
    return db

def get_migrate():
    return Migrate(current_app, get_db())

db = get_db()
migrate = get_migrate()
