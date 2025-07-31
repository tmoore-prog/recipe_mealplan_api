from config import db, ma
from datetime import datetime
from marshmallow.fields import String, DateTime, Integer, Nested, Email
from marshmallow import validate, post_load
from werkzeug.security import generate_password_hash


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True, unique=True, nullable=False)
    instructions = db.Column(db.Text)
    prep_time = db.Column(db.Integer, index=True, nullable=False)
    cook_time = db.Column(db.Integer, index=True, nullable=False)
    servings = db.Column(db.Integer, index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    recipe_ingredients = db.relationship('RecipeIngredient',
                                         back_populates='recipe')
    collected_recipes = db.relationship('UserRecipe', back_populates='recipe')


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), index=True, unique=True, nullable=False)
    category = db.Column(db.String(20), index=True, nullable=False)

    recipe_ingredients = db.relationship('RecipeIngredient',
                                         back_populates='ingredient')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), index=True, unique=True,
                         nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    joined_on = db.Column(db.DateTime, default=datetime.now)

    collected_recipes = db.relationship('UserRecipe', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


class UserRecipe(db.Model):
    __tablename__ = 'user_recipe'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'),
                          primary_key=True)
    user_notes = db.Column(db.Text, nullable=True)
    collected_at = db.Column(db.DateTime, default=datetime.now,
                             nullable=False)

    user = db.relationship('User', back_populates='collected_recipes')
    recipe = db.relationship('Recipe', back_populates='collected_recipes')


class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredient'

    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'),
                          primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'),
                              primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.String(20), nullable=True)

    recipe = db.relationship('Recipe', back_populates='recipe_ingredients')
    ingredient = db.relationship('Ingredient',
                                 back_populates='recipe_ingredients')


class RecipeSchema(ma.SQLAlchemyAutoSchema):
    name = String(required=True, validate=validate.Length(min=3, max=50))
    prep_time = Integer(required=True, validate=validate.Range(min=0))
    cook_time = Integer(required=True, validate=validate.Range(min=0))
    servings = Integer(required=True, validate=validate.Range(min=1))
    created_at = DateTime(validate=validate.Equal(datetime.now()))

    recipe_ingredients = Nested('RecipeIngredientSchema', many=True,
                                dump_only=True)

    class Meta:
        model = Recipe
        load_instance = True
        sqla_session = db.session


class IngredientSchema(ma.SQLAlchemyAutoSchema):
    name = String(required=True, validate=validate.Length(min=2, max=25))
    category = String(required=True, validate=validate.Length(min=2, max=20))

    class Meta:
        model = Ingredient
        load_instance = True
        sqla_session = db.session


class RecipeIngredientSchema(ma.SQLAlchemyAutoSchema):
    quantity = Integer(required=True,
                       validate=validate.Range(min=0, min_inclusive=False))
    unit = String(validate=validate.Length(min=3, max=10),
                  load_default='each')
    notes = String(validate=validate.Length(max=20), allow_none=True)

    ingredient = Nested('IngredientSchema', only=['name', 'category'],
                        dump_only=True)

    class Meta:
        model = RecipeIngredient
        load_instance = True
        sqla_session = db.session
        include_fk = True


class UserRecipeSchema(ma.SQLAlchemyAutoSchema):
    recipe = Nested('RecipeSchema', only=['name', 'recipe_ingredients', 'servings'], dump_only=True)

    class Meta:
        model = UserRecipe
        load_instance = True
        sqla_session = db.session
        include_fk = True


class UserSchema(ma.SQLAlchemyAutoSchema):
    username = String(required=True, validate=validate.Length(min=3,
                                                              max=40))
    password = String(required=True, validate=validate.Length(min=8),
                      load_only=True)
    password_hash = String()
    email = Email(required=True)
    joined_on = DateTime(validate=validate.Equal(datetime.now),
                         dump_only=True)

    collected_recipes = Nested('UserRecipeSchema', many=True, dump_only=True)

    @post_load
    def hash_password(self, data, **kwargs):
        if "password" in data:
            data['password_hash'] = generate_password_hash(data['password'])
            del data['password']
        return data

    class Meta:
        model = User
        load_instance = True
        sqla_session = db.session
        exclude = ['password_hash']


recipe_schema = RecipeSchema()
recipes_schema = RecipeSchema(many=True)

ingredient_schema = IngredientSchema()
ingredients_schema = IngredientSchema(many=True)

recipe_ingredient_schema = RecipeIngredientSchema()
recipe_ingredients_schema = RecipeIngredientSchema(many=True)

user_schema = UserSchema()

user_recipe_schema = UserRecipeSchema()
user_recipes_schema = UserRecipeSchema(many=True)
