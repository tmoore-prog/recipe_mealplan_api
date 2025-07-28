from config import db, ma
from datetime import datetime
from marshmallow.fields import String, DateTime, Integer
from marshmallow import validate


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True, unique=True, nullable=False)
    instructions = db.Column(db.Text)
    prep_time = db.Column(db.Integer, index=True, nullable=False)
    cook_time = db.Column(db.Integer, index=True, nullable=False)
    servings = db.Column(db.Integer, index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(), nullable=False)


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), index=True, unique=True, nullable=False)
    category = db.Column(db.String(20), index=True, nullable=False)
    unit = db.Column(db.String(10), default="Each", nullable=False)


class RecipeSchema(ma.SQLAlchemyAutoSchema):
    name = String(required=True, validate=validate.Length(min=3, max=50))
    prep_time = Integer(required=True, validate=validate.Range(min=0))
    cook_time = Integer(required=True, validate=validate.Range(min=0))
    servings = Integer(required=True, validate=validate.Range(min=1))
    created_at = DateTime(validate=validate.Equal(datetime.now()))

    class Meta:
        model = Recipe
        load_instance = True
        sqla_session = db.session


class IngredientSchema(ma.SQLAlchemyAutoSchema):
    name = String(required=True, validate=validate.Length(min=2, max=25))
    category = String(required=True, validate=validate.Length(min=2, max=20))
    unit = String(validate=validate.Length(min=3, max=10), load_default='Each')

    class Meta:
        model = Ingredient
        load_instance = True
        sqla_session = db.session


recipe_schema = RecipeSchema()
recipes_schema = RecipeSchema(many=True)

ingredient_schema = IngredientSchema()
ingredients_schema = IngredientSchema(many=True)
