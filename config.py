from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()

def create_app(config_type='development'):
    app = Flask(__name__)

    if config_type == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True

    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    ma.init_app(app)

    from routes import api_bp
    app.register_blueprint((api_bp))

    return app
