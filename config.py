from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_type='development'):
    app = Flask(__name__)

    if config_type == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True

    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = "super-secret"  # Change

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from api.recipes import recipes_bp
    from api.ingredients import ingredients_bp
    from api.auth import auth_bp
    from api.users import users_bp

    app.register_blueprint(recipes_bp)
    app.register_blueprint(ingredients_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)

    return app
