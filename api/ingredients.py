from models import Ingredient, ingredient_schema, ingredients_schema
from flask import Blueprint, jsonify, request
from sqlalchemy import select
from config import db
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError


ingredients_bp = Blueprint('ingredients', __name__,
                           url_prefix='/api/ingredients')


@ingredients_bp.route('/', methods=['GET'])
def get_ingredients():
    query = select(Ingredient)
    results = db.session.execute(query)
    ingredients = results.scalars().all()
    return jsonify(ingredients_schema.dump(ingredients)), 200


@ingredients_bp.route('/', methods=['POST'])
def create_ingredient():
    try:
        ingredient = ingredient_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": "Invalid data",
                        "details": err.messages,
                        "status": 400}), 400
    try:
        db.session.add(ingredient)
        db.session.commit()
        return jsonify(ingredient_schema.dump(ingredient)), 201
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"error": "Database error",
                        "details": str(err),
                        "status": 500}), 500


@ingredients_bp.route('/<int:ingredient_id>', methods=['PATCH'])
def update_ingredient(ingredient_id):
    ingredient_to_update = db.session.get(Ingredient, ingredient_id)
    if not ingredient_to_update:
        return jsonify({"error": "Ingredient not found",
                        "status": 404}), 404
    try:
        ingredient_schema.load(request.get_json(),
                               instance=ingredient_to_update, partial=True)
    except ValidationError as err:
        return jsonify({"error": "Invalid data",
                        "details": err.messages,
                        "status": 400}), 400
    try:
        db.session.commit()
        return jsonify(ingredient_schema.dump(ingredient_to_update)), 200
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"error": "Database error",
                        "details": str(err),
                        "status": 500}), 500


@ingredients_bp.route('/<int:ingredient_id>', methods=['GET'])
def get_ingredient_by_id(ingredient_id):
    ingredient = db.session.get(Ingredient, ingredient_id)
    if not ingredient:
        return jsonify({"error": f"Ingredient with id:{ingredient_id} "
                        "not found",
                        "status": 404}), 404
    return jsonify(ingredient_schema.dump(ingredient)), 200


@ingredients_bp.route('/<int:ingredient_id>', methods=['DELETE'])
def delete_ingredient(ingredient_id):
    ingredient_to_delete = db.session.get(Ingredient, ingredient_id)
    if not ingredient_to_delete:
        return jsonify({"error": f"Ingredient id {ingredient_id} not found",
                        "status": 404}), 404
    try:
        db.session.delete(ingredient_to_delete)
        db.session.commit()
        return jsonify({"message": "Ingredient successfully deleted"}), 200
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"error": "Database error",
                        "details": str(err),
                        "status": 500}), 500
