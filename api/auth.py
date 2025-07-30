from flask import Blueprint, jsonify, request
from sqlalchemy import select
from models import User, user_schema
from models import Ingredient, ingredient_schema, ingredients_schema
from models import RecipeIngredient, recipe_ingredient_schema, \
                   recipe_ingredients_schema
from config import db
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
#from flask_jwt_extended import 


auth_bp = Blueprint('authorization', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register_user():
    new_user = user_schema.load(request.get_json())
    db.session.add(new_user)
    db.session.commit()
    return user_schema.dump(new_user)
