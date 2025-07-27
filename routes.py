from flask import Blueprint, jsonify, request
from sqlalchemy import select
from models import Recipe, recipe_schema, recipes_schema
from config import db
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/recipes', methods=['GET'])
def get_recipes():
    query = select(Recipe)
    result = db.session.execute(query)
    recipes = result.scalars().all()
    return jsonify(recipes_schema.dump(recipes)), 200


@api_bp.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if recipe:
        return jsonify(recipe_schema.dump(recipe)), 200
    else:
        return jsonify({"error": "Recipe not found", "status": 404}), 404


@api_bp.route('/api/recipes', methods=['POST'])
def add_recipe():
    try:
        raw_recipe = request.get_json()
        allowed_fields = ['name', 'instructions', 'prep_time', 'cook_time',
                          'servings']
        filtered_recipe = {k: v for k, v in raw_recipe.items()
                           if k in allowed_fields}
        recipe = recipe_schema.load(filtered_recipe)
    except ValidationError as err:
        return jsonify({"error": "Invalid data", "details": err.messages,
                        "status": 400}), 400

    try:
        db.session.add(recipe)
        db.session.commit()
        return jsonify(recipe_schema.dump(recipe)), 201
    except IntegrityError as err:
        return jsonify({"error": "Unique constraint error",
                        "details": str(err),
                        "status": 400}), 400


@api_bp.route('/api/recipes/<int:recipe_id>', methods=["PATCH"])
def update_recipe(recipe_id):
    recipe_to_update = db.session.get(Recipe, recipe_id)

    if not recipe_to_update:
        return jsonify({"error": f"Recipe with id {recipe_id} not found",
                       "status": 404}), 404

    try:
        recipe_schema.load(request.get_json(), instance=recipe_to_update,
                           partial=True)
    except ValidationError as err:
        return jsonify({"error": "Invalid data",
                        "details": err.messages, "status": 400}), 400

    try:
        db.session.commit()
        return jsonify(recipe_schema.dump(recipe_to_update)), 200
    except IntegrityError as err:
        return jsonify({"error": "Unique constraint error",
                        "details": str(err),
                        "status": 400}), 400


@api_bp.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    recipe_to_delete = db.session.get(Recipe, recipe_id)
    if not recipe_to_delete:
        return jsonify({"error": f"Recipe with id {recipe_id} not found",
                       "status": 404}), 404

    db.session.delete(recipe_to_delete)
    db.session.commit()
    return jsonify({"message": "Recipe successfully deleted"}), 200
