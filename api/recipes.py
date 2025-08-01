from models import Recipe, recipe_schema, recipes_schema
from models import Ingredient
from models import RecipeIngredient, recipe_ingredient_schema, \
                   recipe_ingredients_schema
from sqlalchemy import select
from flask import Blueprint, jsonify, request
from config import db
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


recipes_bp = Blueprint('recipes', __name__, url_prefix='/api/recipes')


@recipes_bp.route('/', methods=['GET'])
def get_recipes():
    query = select(Recipe)
    result = db.session.execute(query)
    recipes = result.scalars().all()
    return jsonify(recipes_schema.dump(recipes)), 200


@recipes_bp.route('/<int:recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if recipe:
        return jsonify(recipe_schema.dump(recipe)), 200
    else:
        return jsonify({"error": "Recipe not found", "status": 404}), 404


@recipes_bp.route('/', methods=['POST'])
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


@recipes_bp.route('/<int:recipe_id>', methods=["PATCH"])
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
        db.session.rollback()
        return jsonify({"error": "Unique constraint error",
                        "details": str(err),
                        "status": 400}), 400
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"error": "Database error",
                        "details": str(err),
                        "status": 500}), 500


@recipes_bp.route('/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    recipe_to_delete = db.session.get(Recipe, recipe_id)
    if not recipe_to_delete:
        return jsonify({"error": f"Recipe with id {recipe_id} not found",
                       "status": 404}), 404
    try:
        db.session.delete(recipe_to_delete)
        db.session.commit()
        return jsonify({"message": "Recipe successfully deleted"}), 200
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"error": "Database error",
                        "details": str(err),
                        "status": 500}), 500


@recipes_bp.route('/<int:recipe_id>/ingredients', methods=['GET'])
def get_ingredients_by_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if not recipe:
        return jsonify({"error": f"Recipe id {recipe_id} not found",
                        "status": 404}), 404
    return jsonify(recipe_ingredients_schema.dump
                   (recipe.recipe_ingredients)), 200


@recipes_bp.route('/<int:recipe_id>/ingredients', methods=['POST'])
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
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"error": "Database error",
                        "details": str(err),
                        "status": 500}), 500


@recipes_bp.route('/<int:recipe_id>/ingredients/<int:ingredient_id>',
                  methods=['GET'])
def get_specific_recipe_ingredient(recipe_id, ingredient_id):
    recipe_ingredient = db.session.get(RecipeIngredient,
                                       (recipe_id, ingredient_id))
    if not recipe_ingredient:
        return jsonify({"error": f"Ingredient id {ingredient_id} not found "
                        f"for recipe id {recipe_id}",
                        "status": 404}), 404
    return jsonify(recipe_ingredient_schema.dump(recipe_ingredient)), 200


@recipes_bp.route('/<int:recipe_id>/ingredients/<int:ingredient_id>',
                  methods=['DELETE'])
def remove_recipe_ingredient(recipe_id, ingredient_id):
    recipe_ingredient = db.session.get(RecipeIngredient,
                                       (recipe_id, ingredient_id))
    if not recipe_ingredient:
        return jsonify({"error": f"Ingredient id {ingredient_id} "
                        f"not found for recipe id {recipe_id}",
                        "status": 404}), 404
    try:
        db.session.delete(recipe_ingredient)
        db.session.commit()
        return jsonify({"message": f"Ingredient id {ingredient_id} "
                        f"successfully deleted from recipe id {recipe_id}",
                        "status": 200}), 200
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"error": "Database error",
                        "details": str(err),
                        "status": 500}), 500


@recipes_bp.route('/<int:recipe_id>/ingredients/<int:ingredient_id>',
                  methods=['PATCH'])
def update_recipe_ingredient(recipe_id, ingredient_id):
    recipe_ingredient = db.session.get(RecipeIngredient,
                                       (recipe_id, ingredient_id))
    if not recipe_ingredient:
        return jsonify({"error": f"Ingredient id {ingredient_id} "
                        f"not found for recipe id {recipe_id}",
                        "status": 404}), 404
    data = request.get_json()
    allowed_fields = ['unit', 'notes', 'quantity']
    filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
    try:
        recipe_ingredient_schema.load(filtered_data,
                                      instance=recipe_ingredient,
                                      partial=True)
    except ValidationError as err:
        return jsonify({"error": "Invalid data",
                        "details": err.messages,
                        "status": 400}), 400
    try:
        db.session.commit()
        return jsonify(recipe_ingredient_schema.dump(recipe_ingredient)), 200
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"error": "Database error",
                        "details": str(err),
                        "status": 500}), 500


@recipes_bp.route('/<int:recipe_id>/ingredients/bulk', methods=['POST'])
def add_multiple_ingredients_to_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if not recipe:
        return jsonify({"error": f"Recipe id {recipe_id} not found",
                        "status": 404}), 404
    data = request.get_json()
    recipe_ingredients = []
    if not data or not isinstance(data, list):
        return jsonify({"error": "Expected ingredients array in request body",
                        "status": 400}), 400
    for datum in data:
        ingredient = db.session.get(Ingredient, datum['ingredient_id'])
        if not ingredient:
            return jsonify({"error": f"Ingredient id {datum['ingredient_id']} "
                            "not found",
                            "status": 404}), 404
        datum['recipe_id'] = recipe_id
        try:
            ri = recipe_ingredient_schema.load(datum)
        except ValidationError as err:
            return jsonify({"error": "Invalid data",
                            "details": err.messages,
                            "status": 400}), 400
        db.session.add(ri)
        recipe_ingredients.append(ri)
    try:
        db.session.commit()
        return jsonify(recipe_ingredients_schema.dump(recipe_ingredients)), 201
    except SQLAlchemyError as err:
        db.session.rollback()
        return jsonify({"error": "Database error",
                        "details": str(err),
                        "status": 500}), 500
