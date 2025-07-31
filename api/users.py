from flask import Blueprint, jsonify, request
from sqlalchemy import select
from models import User, user_schema, user_recipes_schema
from config import db, jwt
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_jwt_extended import create_access_token, jwt_required
from flask_jwt_extended import current_user
from werkzeug.security import check_password_hash


users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('/recipes', methods=['GET'])
@jwt_required()
def get_user_recipes():
    return jsonify(user_recipes_schema.dump(current_user.collected_recipes)), 200