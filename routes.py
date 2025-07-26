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


@api_bp.route('/api/recipes', methods=['POST'])
def add_recipe():
    try:
        recipe = recipe_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": "Bad data", "details": err.messages,
                        "status": 400}), 400
    try:
        db.session.add(recipe)
        db.session.commit()
        return jsonify(recipe_schema.dump(recipe)), 201
    except IntegrityError as err:
        return jsonify({"error": "Unique constraint error",
                        "details": str(err),
                        "status": 400}), 400
