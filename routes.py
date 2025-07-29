from flask import Blueprint, jsonify, request
from sqlalchemy import select
from models import Recipe, recipe_schema, recipes_schema
from models import Ingredient, ingredient_schema, ingredients_schema
from models import RecipeIngredient, recipe_ingredient_schema, \
                   recipe_ingredients_schema
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


@api_bp.route('/api/ingredients', methods=['GET'])
def get_ingredients():
    query = select(Ingredient)
    results = db.session.execute(query)
    ingredients = results.scalars().all()
    return jsonify(ingredients_schema.dump(ingredients)), 200


@api_bp.route('/api/ingredients', methods=['POST'])
def create_ingredient():
    try:
        ingredient = ingredient_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": "Invalid data",
                        "details": err.messages,
                        "status": 400}), 400
    db.session.add(ingredient)
    db.session.commit()
    return jsonify(ingredient_schema.dump(ingredient)), 201


@api_bp.route('/api/ingredients/<int:ingredient_id>', methods=['PATCH'])
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
    db.session.commit()
    return jsonify(ingredient_schema.dump(ingredient_to_update)), 200


@api_bp.route('/api/ingredients/<int:ingredient_id>', methods=['GET'])
def get_ingredient_by_id(ingredient_id):
    ingredient = db.session.get(Ingredient, ingredient_id)
    if not ingredient:
        return jsonify({"error": f"Ingredient with id:{ingredient_id} not found",
                        "status": 404}), 404
    return jsonify(ingredient_schema.dump(ingredient)), 200


@api_bp.route('/api/ingredients/<int:ingredient_id>', methods=['DELETE'])
def delete_ingredient(ingredient_id):
    ingredient_to_delete = db.session.get(Ingredient, ingredient_id)
    if not ingredient_to_delete:
        return jsonify({"error": f"Ingredient id {ingredient_id} not found",
                        "status": 404}), 404
    db.session.delete(ingredient_to_delete)
    db.session.commit()
    return jsonify({"message": "Ingredient successfully deleted"}), 200


@api_bp.route('/api/recipes/<int:recipe_id>/ingredients', methods=['GET'])
def get_ingredients_by_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if not recipe:
        return jsonify({"error": f"Recipe id {recipe_id} not found",
                        "status": 404}), 404
    return jsonify(recipe_ingredients_schema.dump(recipe.recipe_ingredients)), 200


@api_bp.route('/api/recipes/<int:recipe_id>/ingredients', methods=['POST'])
def add_ingredient_to_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if not recipe:
        return jsonify({"error": f"Recipe id {recipe_id} not found",
                        "status": 404}), 404
    data = request.get_json()
    data['recipe_id'] = recipe_id
    ingredient = db.session.get(Ingredient, data['ingredient_id'])
    if not ingredient:
        return jsonify({"error": "Ingredient id "
                        f"{data['ingredient_id']} not found",
                        "status": 404}), 404
    existing = db.session.query(RecipeIngredient).filter_by(
               recipe_id=recipe_id,
               ingredient_id=data['ingredient_id']).first()
    if existing:
        return jsonify({"error": f"Recipe id {recipe_id} already contains "
                        "this ingredient",
                        "status": 409}), 409
    try:
        recipe_ingredient = recipe_ingredient_schema.load(data)
    except ValidationError as err:
        return jsonify({"error": "Invalid data", "details": err.messages,
                        "status": 400}), 400
    try:
        db.session.add(recipe_ingredient)
        db.session.commit()
        return jsonify(recipe_ingredient_schema.dump(recipe_ingredient)), 201
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({"error": "Table contraint not met",
                        "details": str(err),
                        "status": 400}), 400
