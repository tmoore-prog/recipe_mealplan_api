from flask import Blueprint, jsonify, request
from sqlalchemy import select
from models import User, user_schema, user_recipes_schema, user_recipe_schema
from models import Recipe, UserRecipe
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


@users_bp.route('/recipes', methods=['POST'])
@jwt_required()
def add_user_recipe():
    data = request.get_json()
    recipe = db.session.get(Recipe, data['recipe_id'])
    if not recipe:
        return jsonify({"error": f"Recipe id {data['recipe_id']} not found",
                        "status": 404}), 404
    data['user_id'] = current_user.id
    existing = db.session.query(UserRecipe).filter_by(
        user_id=data['user_id'], recipe_id=data['recipe_id']).first()
    if existing:
        return jsonify({"error": "That recipe is already in user collection",
                        "status": 409}), 409
    try:
        user_recipe = user_recipe_schema.load(data)
    except ValidationError as err:
        return jsonify({"error": "Invalid data",
                        "details": err.messages,
                        "status": 400}), 400
    try:
        db.session.add(user_recipe)
        db.session.commit()
        return jsonify(user_recipe_schema.dump(user_recipe)), 201
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"error": "Database error",
                        "details": str(err),
                        "status": 500}), 500


