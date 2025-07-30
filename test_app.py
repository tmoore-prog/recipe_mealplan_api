import pytest
import json
from config import create_app, db
from datetime import datetime, timedelta
from models import recipe_schema, ingredient_schema, recipe_ingredient_schema


@pytest.fixture
def client():
    test_app = create_app(config_type='testing')

    with test_app.test_client() as client:
        with test_app.app_context():
            db.create_all()

            yield client

            db.session.remove()
            db.drop_all()


# Restructure? Bulky and unneeded?
@pytest.fixture
def preload_client():
    test_app = create_app(config_type='testing')

    with test_app.test_client() as client:
        with test_app.app_context():
            db.create_all()

            recipes = [
                {"name": "Test 1", "instructions": "Test, test, test",
                 "prep_time": 20, "cook_time": 20, "servings": 2},
                {"name": "Test 2", "instructions": "Test, test, test",
                 "prep_time": 20, "cook_time": 20, "servings": 2},
                {"name": "Test 3", "instructions": "Test, test, test",
                 "prep_time": 20, "cook_time": 20, "servings": 2}
            ]
            for recipe in recipes:
                data = recipe_schema.load(recipe)
                db.session.add(data)
                db.session.commit()
            ingredients = [
                {"name": "Ingredient 1", "category": "food"},
                {"name": "Ingredient 2", "category": "food"},
                {"name": "Ingredient 3", "category": "food"},
                {"name": "Ingredient 4", "category": "food"},
                {"name": "Ingredient 5", "category": "food"}
            ]
            for ingredient in ingredients:
                data = ingredient_schema.load(ingredient)
                db.session.add(data)
                db.session.commit()
            recipe_ingredients = [
                {"recipe_id": 1, "ingredient_id": 1, "quantity": 2,
                 "unit": "cups", "notes": "level cups"},
                {"recipe_id": 1, "ingredient_id": 2, "quantity": 3,
                 "unit": "tbsps", "notes": "diced"},
                {"recipe_id": 1, "ingredient_id": 3, "quantity": 1,
                 "unit": "Each", "notes": "peeled"},
                {"recipe_id": 2, "ingredient_id": 4, "quantity": 2,
                 "unit": "tsps", "notes": None},
                {"recipe_id": 3, "ingredient_id": 5, "quantity": 1,
                 "unit": "each", "notes": "whole"}
            ]
            for recipeingred in recipe_ingredients:
                data = recipe_ingredient_schema.load(recipeingred)
                db.session.add(data)
                db.session.commit()

            yield client

            db.session.remove()
            db.drop_all()


def test_get_empty_recipes_list(client):
    response = client.get('/api/recipes/')
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_recipe_returns_created_recipe(client):
    data = {
        "name": "Test Recipe",
        "instructions": "Test instructions",
        "prep_time": 30,
        "cook_time": 20,
        "servings": 2
    }
    response = client.post('/api/recipes/', data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 201
    response = client.get('/api/recipes/')
    assert response.status_code == 200
    data = response.get_json()
    assert data[0]['name'] == "Test Recipe"


def test_recipe_bad_integer_data(client):
    test_cases = [
        {"prep_time": "thirty"},
        {"cook_time": "Twenty"},
        {"servings": "Two"}
    ]

    for case in test_cases:
        data = {
            "name": "Test Recipe",
            "instructions": "Test instructions",
            "prep_time": 30,
            "cook_time": 20,
            "servings": 2,
            **case
        }
        response = client.post('/api/recipes/', data=json.dumps(data),
                               content_type='application/json')
        assert response.status_code == 400


def test_add_same_name_recipe(client):
    data = [{
        "name": "Test Recipe",
        "instructions": "Test instructions",
        "prep_time": 30,
        "cook_time": 20,
        "servings": 2
        },
        {
        "name": "Test Recipe",
        "instructions": "Test instructions 2",
        "prep_time": 45,
        "cook_time": 20,
        "servings": 3
    }]
    client.post('/api/recipes/', data=json.dumps(data[0]),
                content_type='application/json')
    response = client.post('/api/recipes/', data=json.dumps(data[1]),
                           content_type='application/json')
    assert response.status_code == 400


def test_add_name_empty(client):
    data = {
        "name": "",
        "instructions": "Test instructions",
        "prep_time": 30,
        "cook_time": 20,
        "servings": 2
    }
    response = client.post('/api/recipes/', data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "Invalid data"


def test_add_negative_integer_data(client):
    test_cases = [
        {"prep_time": -20},
        {"cook_time": -20},
        {"servings": -5}
    ]
    for case in test_cases:
        data = {
            "name": "Test Recipe",
            "instructions": "Test instructions",
            "prep_time": 30,
            "cook_time": 20,
            "servings": 2,
            **case
        }
        response = client.post('/api/recipes/', data=json.dumps(data),
                               content_type='application/json')
        assert response.status_code == 400


def test_user_cannot_override_created_at(client):
    current_time = datetime.now()
    subtract_time = timedelta(hours=25, minutes=25)
    test_time = current_time - subtract_time
    data = {
        "name": "Test Recipe",
        "instructions": "Test instructions",
        "prep_time": 30,
        "cook_time": 20,
        "servings": 2,
        "created_at": test_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    response = client.post('/api/recipes/', data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 201


def test_created_at_auto_populates(client):
    data = {
        "name": "Test Recipe",
        "instructions": "Test instructions",
        "prep_time": 30,
        "cook_time": 20,
        "servings": 2
    }
    response = client.post('/api/recipes/', data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 201

    data = response.get_json()
    create_time = datetime.fromisoformat(data['created_at'])

    assert create_time


def test_patch_recipe(client):
    data = {
        "name": "Test Recipe",
        "instructions": "Test instructions",
        "prep_time": 30,
        "cook_time": 20,
        "servings": 2
    }
    client.post('/api/recipes/', data=json.dumps(data),
                content_type='application/json')
    update = {"servings": 4}
    response = client.patch('/api/recipes/1', data=json.dumps(update),
                            content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['servings'] == 4


def test_get_recipe_by_id(client):
    data = {
        "name": "Test Recipe",
        "instructions": "Test instructions",
        "prep_time": 30,
        "cook_time": 20,
        "servings": 2
    }
    create_response = client.post('/api/recipes/', data=json.dumps(data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    response = client.get(f'/api/recipes/{recipe_id}')
    assert response.status_code == 200


def test_delete_recipe_by_id(client):
    data = {
        "name": "Test Recipe",
        "instructions": "Test instructions",
        "prep_time": 30,
        "cook_time": 20,
        "servings": 2
    }
    create_response = client.post('/api/recipes/', data=json.dumps(data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    response = client.delete(f'/api/recipes/{recipe_id}')
    assert response.status_code == 200
    check = client.get(f'/api/recipes/{recipe_id}')
    assert check.status_code == 404


def test_get_empty_ingredients_list(client):
    response = client.get('/api/ingredients/')
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_ingredient_returns_created_ingredient(client):
    data = {
        "name": "Test ingredient",
        "category": "Test cat."
    }
    create_response = client.post('/api/ingredients/', data=json.dumps(data),
                                  content_type='application/json')
    assert create_response.status_code == 201
    response = client.get('/api/ingredients/')
    assert response.status_code == 200
    data = response.get_json()
    assert data[0]['id'] == 1


def test_get_multiple_ingredients(client):
    data = [
        {
            "name": "Test ingredient 1",
            "category": "Test"
        },
        {
            "name": "Test ingredient 2",
            "category": "Test"
        }
    ]
    for datum in data:
        client.post('/api/ingredients/', data=json.dumps(datum),
                    content_type='application/json')
    response = client.get('/api/ingredients/')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2


def test_create_ingredient_empty_name(client):
    data = {
        "name": "",
        "category": "Test cat."
    }
    create_response = client.post('/api/ingredients/', data=json.dumps(data),
                                  content_type='application/json')
    assert create_response.status_code == 400


def test_create_ingredient_empty_category(client):
    data = {
        "name": "Test ingredient",
        "category": ""
    }
    create_response = client.post('/api/ingredients/', data=json.dumps(data),
                                  content_type='application/json')
    assert create_response.status_code == 400


def test_update_ingredient(client):
    data = {
        "name": "Test ingredient",
        "category": "Test cat."
    }
    create_response = client.post('/api/ingredients/', data=json.dumps(data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    update = {"category": "food"}
    update_response = client.patch(f'/api/ingredients/{ingredient_id}',
                                   data=json.dumps(update),
                                   content_type='application/json')
    assert update_response.status_code == 200


def test_update_nonexistent_ingredient(client):
    update = {"category": "food"}
    response = client.patch('/api/ingredients/1', data=json.dumps(update),
                            content_type='application/json')
    assert response.status_code == 404


def test_update_with_invalid_data(client):
    data = {
        "name": "Test ingredient",
        "category": "Test cat."
    }
    create_response = client.post('/api/ingredients/', data=json.dumps(data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    update = {"category": ""}
    update_response = client.patch(f'/api/ingredients/{ingredient_id}',
                                   data=json.dumps(update),
                                   content_type='application/json'
                                   )
    assert update_response.status_code == 400


def test_get_ingredient_by_id(client):
    data = {
        "name": "Test ingredient",
        "category": "Test cat."
    }
    create_response = client.post('/api/ingredients/', data=json.dumps(data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    get_response = client.get(f'/api/ingredients/{ingredient_id}')
    assert get_response.status_code == 200


def test_get_non_existent_ingredient(client):
    response = client.get('/api/ingredients/100')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Ingredient with id:100 not found"


def test_delete_ingredient(client):
    data = {
        "name": "Test ingredient",
        "category": "Test cat."
    }
    create_response = client.post('/api/ingredients/', data=json.dumps(data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    response = client.delete(f'/api/ingredients/{ingredient_id}')
    assert response.status_code == 200
    get_response = client.get(f'/api/ingredients/{ingredient_id}')
    assert get_response.status_code == 404


def test_delete_non_existent_ingredient(client):
    response = client.delete('/api/ingredients/100')
    assert response.status_code == 404


# Restructure preload client?
def test_get_ingredients_by_recipe(preload_client):
    recipe_id = 1
    response = preload_client.get(f'/api/recipes/{recipe_id}/ingredients')
    assert response.status_code == 200
    data = response.get_json()
    assert data[0]['quantity'] == 2
    assert data[1]['notes'] == "diced"
    assert data[2]['ingredient']['name'] == "Ingredient 3"


def test_add_ingredient_to_recipe(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_data = {
        "name": "Test ingredient",
        "category": "Test cat"
    }
    create_response = client.post('/api/ingredients/',
                                  data=json.dumps(ingredient_data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    ri_data = {
        "ingredient_id": ingredient_id,
        "quantity": 2,
        "unit": "cups",
        "notes": "diced"
    }
    response = client.post(f'/api/recipes/{recipe_id}/ingredients',
                           data=json.dumps(ri_data),
                           content_type='application/json')
    assert response.status_code == 201


def test_add_ingredient_to_non_existent_recipe(client):
    recipe_id = 35
    ingredient_data = {
        "name": "Test ingredient",
        "category": "Test cat"
    }
    create_response = client.post('/api/ingredients/',
                                  data=json.dumps(ingredient_data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    ri_data = {
        "ingredient_id": ingredient_id,
        "quantity": 2,
        "unit": "cups",
        "notes": "diced"
    }
    response = client.post(f'/api/recipes/{recipe_id}/ingredients',
                           data=json.dumps(ri_data),
                           content_type='application/json')
    assert response.status_code == 404


def test_add_non_existent_ingredient_to_recipe(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_id = 55
    ri_data = {
        "ingredient_id": ingredient_id,
        "quantity": 2,
        "unit": "cups",
        "notes": "diced"
    }
    response = client.post(f'/api/recipes/{recipe_id}/ingredients',
                           data=json.dumps(ri_data),
                           content_type='application/json')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Ingredient id 55 not found"


# ri stands for Recipe Ingredient
def test_add_ingredient_to_recipe_invalid_ri_data(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_data = {
        "name": "Test ingredient",
        "category": "Test cat"
    }
    create_response = client.post('/api/ingredients/',
                                  data=json.dumps(ingredient_data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    ri_data_cases = [
        {"ingredient_id": ingredient_id, "unit": "cups", "notes": "diced"},
        {"ingredient_id": ingredient_id, "quantity": 2,
         "unit": "this is well over limit",
         "notes": "diced"},
        {"ingredient_id": ingredient_id, "quantity": 2, "unit": "cups",
         "notes": "this is over twenty characters"}
    ]
    for case in ri_data_cases:
        response = client.post(f'/api/recipes/{recipe_id}/ingredients',
                               data=json.dumps(case),
                               content_type='application/json')
        assert response.status_code == 400


def test_add_same_ingredient_to_recipe_twice(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_data = {
        "name": "Test ingredient",
        "category": "Test cat"
    }
    create_response = client.post('/api/ingredients/',
                                  data=json.dumps(ingredient_data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    ri_data = {
        "ingredient_id": ingredient_id,
        "quantity": 2,
        "unit": "cups",
        "notes": "diced"
    }
    client.post(f'/api/recipes/{recipe_id}/ingredients',
                data=json.dumps(ri_data),
                content_type='application/json')
    response = client.post(f'/api/recipes/{recipe_id}/ingredients',
                           data=json.dumps(ri_data),
                           content_type='application/json')
    assert response.status_code == 409


def test_get_specific_recipe_ingredient(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_data = {
        "name": "Test ingredient",
        "category": "Test cat"
    }
    create_response = client.post('/api/ingredients/',
                                  data=json.dumps(ingredient_data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    ri_data = {
        "ingredient_id": ingredient_id,
        "quantity": 2,
        "unit": "cups",
        "notes": "diced"
    }
    client.post(f'/api/recipes/{recipe_id}/ingredients',
                data=json.dumps(ri_data),
                content_type='application/json')
    response = client.get(f'/api/recipes/{recipe_id}/ingredients/{ingredient_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['ingredient']['name'] == "Test ingredient"


def test_get_non_existent_recipe_ingredient(client):
    recipe_id = 38
    ingredient_id = 31
    response = client.get(f'/api/recipes/{recipe_id}/ingredients/{ingredient_id}')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Ingredient id 31 not found for recipe id 38"


def test_remove_ingredient_from_recipe(client):
    # Set up test data
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_data = {
        "name": "Test ingredient",
        "category": "Test cat"
    }
    create_response = client.post('/api/ingredients/',
                                  data=json.dumps(ingredient_data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    ri_data = {
        "ingredient_id": ingredient_id,
        "quantity": 2,
        "unit": "cups",
        "notes": "diced"
    }
    client.post(f'/api/recipes/{recipe_id}/ingredients',
                data=json.dumps(ri_data),
                content_type='application/json')

    # Delete test recipe ingredient
    delete_response = client.delete(f'/api/recipes/{recipe_id}/ingredients'
                                    f'/{ingredient_id}')
    assert delete_response.status_code == 200
    get_response = client.get(f'/api/recipes/{recipe_id}/ingredients/'
                              f'{ingredient_id}')
    assert get_response.status_code == 404


def test_remove_non_existent_recipe_ingredient(client):
    recipe_id = 1
    ingredient_id = 1
    delete_response = client.delete(f'/api/recipes/{recipe_id}/ingredients'
                                    f'/{ingredient_id}')
    assert delete_response.status_code == 404


def test_update_recipe_ingredient(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_data = {
        "name": "Test ingredient",
        "category": "Test cat"
    }
    create_response = client.post('/api/ingredients/',
                                  data=json.dumps(ingredient_data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    ri_data = {
        "ingredient_id": ingredient_id,
        "quantity": 2,
        "unit": "cups",
        "notes": "diced"
    }
    client.post(f'/api/recipes/{recipe_id}/ingredients',
                data=json.dumps(ri_data),
                content_type='application/json')
    update_data_cases = [
        {"quantity": 4},
        {"unit": "tbsp"},
        {"notes": "minced"}
    ]
    for data in update_data_cases:
        response = client.patch(f'/api/recipes/{recipe_id}/ingredients'
                                f'/{ingredient_id}', data=json.dumps(data),
                                content_type='application/json')
        assert response.status_code == 200


def test_update_ri_blocks_updating_ids(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_data = {
        "name": "Test ingredient",
        "category": "Test cat"
    }
    create_response = client.post('/api/ingredients/',
                                  data=json.dumps(ingredient_data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    ri_data = {
        "ingredient_id": ingredient_id,
        "quantity": 2,
        "unit": "cups",
        "notes": "diced"
    }
    client.post(f'/api/recipes/{recipe_id}/ingredients',
                data=json.dumps(ri_data),
                content_type='application/json')
    update_data_cases = [
        {"recipe_id": 4, "unit": "grams"},
        {"ingredient_id": 5, "unit": "grams"}
    ]
    for data in update_data_cases:
        response = client.patch(f'/api/recipes/{recipe_id}/ingredients'
                                f'/{ingredient_id}', data=json.dumps(data),
                                content_type='application/json')
        data = response.get_json()
        assert data['recipe_id'] == 1
        assert data['ingredient_id'] == 1
        assert data['unit'] == "grams"


def test_update_non_existent_recipe_ingredient(client):
    data = {"unit": "cups"}
    recipe_id = 1
    ingredient_id = 1
    response = client.patch(f'/api/recipes/{recipe_id}/ingredients'
                            f'/{ingredient_id}', data=json.dumps(data),
                            content_type='application/json')
    assert response.status_code == 404


def test_update_ri_with_bad_data(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_data = {
        "name": "Test ingredient",
        "category": "Test cat"
    }
    create_response = client.post('/api/ingredients/',
                                  data=json.dumps(ingredient_data),
                                  content_type='application/json')
    ingredient_id = create_response.get_json()['id']
    ri_data = {
        "ingredient_id": ingredient_id,
        "quantity": 2,
        "unit": "cups",
        "notes": "diced"
    }
    client.post(f'/api/recipes/{recipe_id}/ingredients',
                data=json.dumps(ri_data),
                content_type='application/json')

    data_cases = [
        {"quantity": "Three"},
        {"unit": 2},
        {"notes": {}}
    ]
    for data in data_cases:
        response = client.patch(f'/api/recipes/{recipe_id}/ingredients'
                                f'/{ingredient_id}', data=json.dumps(data),
                                content_type='application/json')
        assert response.status_code == 400


def test_add_multiple_ingredients_to_recipe(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_data = [
        {"name": "Test ingredient",
         "category": "Test cat"},
        {"name": "Test ingredient 2",
         "category": "Test cat"},
        {"name": "Test ingredient 3",
         "category": "Test cat"}
    ]
    ingredient_ids = []
    for ingredient in ingredient_data:
        create_response = client.post('/api/ingredients/',
                                      data=json.dumps(ingredient),
                                      content_type='application/json')
        ingredient_id = create_response.get_json()['id']
        ingredient_ids.append(ingredient_id)
    ri_data = []
    for ingredient_id in ingredient_ids:
        ri_dict = {"ingredient_id": ingredient_id,
                   "quantity": 1,
                   "unit": "each",
                   "notes": "Test"}
        ri_data.append(ri_dict)
    response = client.post(f'/api/recipes/{recipe_id}/ingredients/bulk',
                           data=json.dumps(ri_data),
                           content_type='application/json')
    assert response.status_code == 201
    data = response.get_json()
    assert len(data) == 3


def test_add_multiple_ingredients_to_nonexistent_recipe(client):
    ingredient_data = [
        {"name": "Test ingredient",
         "category": "Test cat"},
        {"name": "Test ingredient 2",
         "category": "Test cat"},
        {"name": "Test ingredient 3",
         "category": "Test cat"}
    ]
    ingredient_ids = []
    for ingredient in ingredient_data:
        create_response = client.post('/api/ingredients/',
                                      data=json.dumps(ingredient),
                                      content_type='application/json')
        ingredient_id = create_response.get_json()['id']
        ingredient_ids.append(ingredient_id)
    ri_data = []
    for ingredient_id in ingredient_ids:
        ri_dict = {"ingredient_id": ingredient_id,
                   "quantity": 1,
                   "unit": "each",
                   "notes": "Test"}
        ri_data.append(ri_dict)
    response = client.post('/api/recipes/123/ingredients/bulk',
                           data=json.dumps(ri_data),
                           content_type='application/json')
    assert response.status_code == 404


def test_add_multiple_non_existent_ingredients_to_recipe(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_ids = [1, 2, 3]
    ri_data = []
    for ingredient_id in ingredient_ids:
        ri_dict = {"ingredient_id": ingredient_id,
                   "quantity": 1,
                   "unit": "each",
                   "notes": "Test"}
        ri_data.append(ri_dict)
    response = client.post(f'/api/recipes/{recipe_id}/ingredients/bulk',
                           data=json.dumps(ri_data),
                           content_type='application/json')
    assert response.status_code == 404


def test_add_multiple_bad_formatted_ingredients_to_recipe(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_data = [
        {"name": "Test ingredient",
         "category": "Test cat"},
        {"name": "Test ingredient 2",
         "category": "Test cat"},
        {"name": "Test ingredient 3",
         "category": "Test cat"}
    ]
    ingredient_ids = []
    for ingredient in ingredient_data:
        create_response = client.post('/api/ingredients/',
                                      data=json.dumps(ingredient),
                                      content_type='application/json')
        ingredient_id = create_response.get_json()['id']
        ingredient_ids.append(ingredient_id)
    ri_data = []
    for ingredient_id in ingredient_ids:
        ri_dict = {"ingredient_id": ingredient_id,
                   "quantity": "Three",
                   "unit": "each",
                   "notes": "Test"}
        ri_data.append(ri_dict)
    response = client.post(f'/api/recipes/{recipe_id}/ingredients/bulk',
                           data=json.dumps(ri_data),
                           content_type='application/json')
    assert response.status_code == 400


def test_add_multiple_ingredients_not_list_formatted(client):
    recipe_data = {
        "name": "Test recipe",
        "instructions": "Test steps",
        "prep_time": 10,
        "cook_time": 10,
        "servings": 3
    }
    create_response = client.post('/api/recipes/', data=json.dumps(recipe_data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    ingredient_data = [
        {"name": "Test ingredient",
         "category": "Test cat"},
        {"name": "Test ingredient 2",
         "category": "Test cat"},
        {"name": "Test ingredient 3",
         "category": "Test cat"}
    ]
    ingredient_ids = []
    for ingredient in ingredient_data:
        create_response = client.post('/api/ingredients/',
                                      data=json.dumps(ingredient),
                                      content_type='application/json')
        ingredient_id = create_response.get_json()['id']
        ingredient_ids.append(ingredient_id)
    ri_data = {}
    for ingredient_id in ingredient_ids:
        ri_dict = {"ingredient_id": ingredient_id,
                   "quantity": 1,
                   "unit": "each",
                   "notes": "Test"}
        ri_data[ingredient_id] = ri_dict
    response = client.post(f'/api/recipes/{recipe_id}/ingredients/bulk',
                           data=json.dumps(ri_data),
                           content_type='application/json')
    assert response.status_code == 400
