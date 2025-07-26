from flask import Blueprint, jsonify
from sqlalchemy import select
from models import Recipe
from config import db

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/recipes', methods=['GET'])
def get_recipes():
    query = select(Recipe)
    result = db.session.execute(query)
    recipes = result.scalars.all()
    return jsonify(recipes), 200
