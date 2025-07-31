from flask import Blueprint, jsonify, request
from sqlalchemy import select
from models import User, user_schema
from config import db, jwt
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash


auth_bp = Blueprint('authorization', __name__, url_prefix='/api/auth')


@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user.id)


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data['sub']
    return db.session.query(User).filter_by(id=int(identity)).one_or_none()


@auth_bp.route('/register', methods=['POST'])
def register_user():
    try:
        new_user = user_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": "Invalid or missing data",
                        "details": err.messages,
                        "status": 400}), 400
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify(user_schema.dump(new_user)), 201
    except IntegrityError as err:
        db.session.rollback()
        if 'UNIQUE constraint' in str(err):
            return jsonify({"error": "That username or email already exists",
                            "details": str(err),
                            "status": 409}), 409
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"error": "Database error",
                        "details": str(err),
                        "status": 500}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    query = select(User).where(User.username == request.get_json()['username'])
    user = db.session.execute(query).scalar_one_or_none()
    if not user:
        return jsonify({"error": "Username not found",
                        "status": 404}), 404
    password_match = check_password_hash(user.password_hash,
                                         request.get_json()['password'])
    if not password_match:
        return jsonify({"error": "Invalid password",
                        "status": 400}), 400
    access_token = create_access_token(identity=user)
    return jsonify(user=user_schema.dump(user)['username'],
                   access_token=access_token), 200
