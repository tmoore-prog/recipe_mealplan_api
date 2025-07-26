from config import db, ma
from datetime import datetime


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True)
    instructions = db.Column(db.Text)
    prep_time = db.Column(db.Integer, index=True)
    cook_time = db.Column(db.Integer, index=True)
    servings = db.Column(db.Integer, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now())


class RecipeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Recipe
        load_instance = True
        sqla_session = db.session


recipe_schema = RecipeSchema()
recipes_schema = RecipeSchema(many=True)
