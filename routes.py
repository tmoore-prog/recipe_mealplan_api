from flask import Blueprint, jsonify, request
from sqlalchemy import select
from models import Recipe
from models import Ingredient, ingredient_schema, ingredients_schema
from models import RecipeIngredient, recipe_ingredient_schema, \
                   recipe_ingredients_schema
from config import db
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

auth_bp = Blueprint('authorization', __name__, url_prefix='/api/auth')
