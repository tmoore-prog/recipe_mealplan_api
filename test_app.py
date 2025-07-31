import pytest
import json
from config import create_app, db
from datetime import datetime, timedelta
# from models import recipe_schema, ingredient_schema, recipe_ingredient_schema


@pytest.fixture
def client():
    test_app = create_app(config_type='testing')

    with test_app.test_client() as client:
        with test_app.app_context():
            db.create_all()

            yield client

            db.session.remove()
            db.drop_all()


def create_test_user(client, username="johndoe123", password="1234secret",
                     email="john.doe@example.com"):
    user_data = {"username": username,
                 "password": password,
                 "email": email}
    return client.post('/api/auth/register', data=json.dumps(user_data),
                       content_type='application/json')


def login_test_user(client, username="johndoe123", password="1234secret"):
    login_data = {"username": username,
                  "password": password}
    return client.post('/api/auth/login', data=json.dumps(login_data),
                       content_type='application/json')


def get_auth_headers(client, func=login_test_user):
    response = func(client)
    access_token = response.get_json()['access_token']
    return {"Authorization": f"Bearer {access_token}"}


def create_test_recipe(client, name="Test recipe", instructions="Test steps",
                       prep_time=10, cook_time=10, servings=3):
    recipe_data = {
        "name": name,
        "instructions": instructions,
        "prep_time": prep_time,
        "cook_time": cook_time,
        "servings": servings
    }
    return client.post('/api/recipes/', data=json.dumps(recipe_data),
                       content_type='application/json')


def create_test_ingredient(client, name="Test ingredient",
                           category="Test cat"):
    ingredient_data = {
        "name": name,
        "category": category
    }
    return client.post('/api/ingredients/', data=json.dumps(ingredient_data),
                       content_type='application/json')


def create_test_recipe_ingredient(client, recipe_id,
                                  ingredient_id, quantity=2,
                                  unit="cups", notes="diced"):
    ri_data = {
        "ingredient_id": ingredient_id,
        "quantity": quantity,
        "unit": unit,
        "notes": notes
    }
    return client.post(f'/api/recipes/{recipe_id}/ingredients',
                       data=json.dumps(ri_data),
                       content_type='application/json')


def create_test_user_recipe(client, recipe_id, headers, user_notes="Test"):
    user_recipe_data = {
        "recipe_id": recipe_id,
        "user_notes": user_notes
    }
    return client.post('/api/users/recipes', data=json.dumps(user_recipe_data),
                       content_type='application/json', headers=headers)


''' Restructure? Bulky and unneeded?
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
'''


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
        response = create_test_recipe(client, **case)
        assert response.status_code == 400


def test_add_same_name_recipe(client):
    data = {
        "name": "Test recipe",
        "instructions": "Test instructions 2",
        "prep_time": 45,
        "cook_time": 20,
        "servings": 3
    }
    create_test_recipe(client)
    response = create_test_recipe(client, **data)
    assert response.status_code == 409


def test_add_name_empty(client):
    response = create_test_recipe(client, name="")
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
        response = create_test_recipe(client, **case)
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
    response = create_test_recipe(client)
    assert response.status_code == 201
    data = response.get_json()
    create_time = datetime.fromisoformat(data['created_at'])
    assert create_time


def test_patch_recipe(client):
    create_test_recipe(client)
    update = {"servings": 4}
    response = client.patch('/api/recipes/1', data=json.dumps(update),
                            content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['servings'] == 4


def test_get_recipe_by_id(client):
    recipe_id = create_test_recipe(client).get_json()['id']
    response = client.get(f'/api/recipes/{recipe_id}')
    assert response.status_code == 200


def test_delete_recipe_by_id(client):
    recipe_id = create_test_recipe(client).get_json()['id']
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
    ingredient_data = [
        {"name": "Test ingredient 1", "category": "Test"},
        {"name": "Test ingredient 2", "category": "Test"}
    ]
    for data in ingredient_data:
        create_test_ingredient(client, **data)
    response = client.get('/api/ingredients/')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2


def test_create_ingredient_empty_name(client):
    create_response = create_test_ingredient(client, name="")
    assert create_response.status_code == 400


def test_create_ingredient_empty_category(client):
    create_response = create_test_ingredient(client, category="")
    assert create_response.status_code == 400


def test_update_ingredient(client):
    ingredient_id = create_test_ingredient(client).get_json()['id']
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
    ingredient_id = create_test_ingredient(client).get_json()['id']
    update = {"category": ""}
    response = client.patch(f'/api/ingredients/{ingredient_id}',
                            data=json.dumps(update),
                            content_type='application/json')
    assert response.status_code == 400


def test_get_ingredient_by_id(client):
    ingredient_id = create_test_ingredient(client).get_json()['id']
    get_response = client.get(f'/api/ingredients/{ingredient_id}')
    assert get_response.status_code == 200


def test_get_non_existent_ingredient(client):
    response = client.get('/api/ingredients/100')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Ingredient with id:100 not found"


def test_delete_ingredient(client):
    ingredient_id = create_test_ingredient(client).get_json()['id']
    response = client.delete(f'/api/ingredients/{ingredient_id}')
    assert response.status_code == 200
    get_response = client.get(f'/api/ingredients/{ingredient_id}')
    assert get_response.status_code == 404


def test_delete_non_existent_ingredient(client):
    response = client.delete('/api/ingredients/100')
    assert response.status_code == 404


'''# Restructure preload client?
def test_get_ingredients_by_recipe(preload_client):
    recipe_id = 1
    response = preload_client.get(f'/api/recipes/{recipe_id}/ingredients')
    assert response.status_code == 200
    data = response.get_json()
    assert data[0]['quantity'] == 2
    assert data[1]['notes'] == "diced"
    assert data[2]['ingredient']['name'] == "Ingredient 3"
'''


def test_add_ingredient_to_recipe(client):
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_id = create_test_ingredient(client).get_json()['id']
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
    ingredient_id = create_test_ingredient(client).get_json()['id']
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
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_id = 55
    response = create_test_recipe_ingredient(client, recipe_id,
                                             ingredient_id)
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Ingredient id 55 not found"


def test_add_ingredient_to_recipe_invalid_ri_data(client):
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_id = create_test_ingredient(client).get_json()['id']
    ri_data_cases = [
        {"quantity": "Two", "unit": "cups", "notes": "diced"},
        {"quantity": 2, "unit": "this is well over limit",
         "notes": "diced"},
        {"quantity": 2, "unit": "cups",
         "notes": "this is over twenty characters"}
    ]
    for case in ri_data_cases:
        response = create_test_recipe_ingredient(client, recipe_id,
                                                 ingredient_id,
                                                 **case)
        assert response.status_code == 400


def test_add_same_ingredient_to_recipe_twice(client):
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_id = create_test_ingredient(client).get_json()['id']
    create_test_recipe_ingredient(client, recipe_id,
                                  ingredient_id)
    response = create_test_recipe_ingredient(client, recipe_id,
                                             ingredient_id)
    assert response.status_code == 409


def test_get_specific_recipe_ingredient(client):
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_id = create_test_ingredient(client).get_json()['id']
    create_test_recipe_ingredient(client, recipe_id, ingredient_id)
    response = client.get(f'/api/recipes/{recipe_id}/'
                          f'ingredients/{ingredient_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['ingredient']['name'] == "Test ingredient"


def test_get_non_existent_recipe_ingredient(client):
    recipe_id = 38
    ingredient_id = 31
    response = client.get(f'/api/recipes/{recipe_id}/'
                          f'ingredients/{ingredient_id}')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Ingredient id 31 not found for recipe id 38"


def test_remove_ingredient_from_recipe(client):
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_id = create_test_ingredient(client).get_json()['id']
    create_test_recipe_ingredient(client, recipe_id, ingredient_id)
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
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_id = create_test_ingredient(client).get_json()['id']
    create_test_recipe_ingredient(client, recipe_id, ingredient_id)
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
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_id = create_test_ingredient(client).get_json()['id']
    create_test_recipe_ingredient(client, recipe_id, ingredient_id)
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
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_id = create_test_ingredient(client).get_json()['id']
    create_test_recipe_ingredient(client, recipe_id, ingredient_id)
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
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_ids = [create_test_ingredient(client,
                      name=f"Test{i}").get_json()['id'] for i in range(3)]
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
    ingredient_ids = [create_test_ingredient(client,
                      name=f"Test{i}").get_json()['id'] for i in range(3)]
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
    recipe_id = create_test_recipe(client).get_json()['id']
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
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_ids = [create_test_ingredient(client,
                      name=f"Test{i}").get_json()['id'] for i in range(3)]
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
    recipe_id = create_test_recipe(client).get_json()['id']
    ingredient_ids = [create_test_ingredient(client,
                      name=f"Test{i}").get_json()['id'] for i in range(3)]
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


def test_register_new_user_doesnt_return_hash(client):
    user_data = {"username": "johndoe123",
                 "password": "1234secret",
                 "email": "john.doe@example.com"}
    response = client.post('/api/auth/register', data=json.dumps(user_data),
                           content_type='application/json')

    assert response.status_code == 201
    data = response.get_json()
    assert 'password_hash' not in data
    assert 'password' not in data


def test_register_new_user_missing_data(client):
    data_cases = [
        {"password": "1234secret", "email": "test@example.com"},
        {"username": "testexample", "email": "test1@example.com"},
        {"username": "testexample1", "password": "1234secret"}
    ]
    for data in data_cases:
        response = client.post('/api/auth/register', data=json.dumps(data),
                               content_type='application/json')
        assert response.status_code == 400


def test_register_new_user_unique_constraints(client):
    create_test_user(client)
    data_cases = [
        {"username": "johndoe123", "password": "1234secret",
         "email": "jdoe@example.org"},
        {"username": "johndoe2", "password": "1234secret",
         "email": "john.doe@example.com"}
    ]
    for data in data_cases:
        response = create_test_user(client, **data)
        assert response.status_code == 409


def test_get_jwt_with_valid_user(client):
    create_test_user(client)
    response = login_test_user(client)
    assert response.status_code == 200
    data = response.get_json()
    assert data['access_token']


def test_get_jwt_with_invalid_pw(client):
    create_test_user(client)
    response = login_test_user(client, password="FakePassword")
    assert response.status_code == 400


def test_get_empty_user_recipes(client):
    create_test_user(client)
    headers = get_auth_headers(client)
    response = client.get('/api/users/recipes', headers=headers)
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_user_recipes_no_token(client):
    response = client.get('/api/users/recipes')
    assert response.status_code == 401


def test_add_recipe_to_user(client):
    create_test_user(client)
    create_response = create_test_recipe(client)
    recipe_id = create_response.get_json()['id']
    headers = get_auth_headers(client)
    response = create_test_user_recipe(client, recipe_id, headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data['user_id'] == 1


def test_add_non_existent_recipe_to_user(client):
    create_test_user(client)
    recipe_id = 101
    headers = get_auth_headers(client)
    response = create_test_user_recipe(client, recipe_id, headers)
    assert response.status_code == 404


def test_add_user_recipe_no_token(client):
    create_response = create_test_recipe(client)
    recipe_id = create_response.get_json()['id']
    response = create_test_user_recipe(client, recipe_id, headers=None)
    assert response.status_code == 401


def test_add_user_recipe_bad_data(client):
    create_test_user(client)
    recipe_response = create_test_recipe(client)
    recipe_id = recipe_response.get_json()['id']
    headers = get_auth_headers(client)
    response = create_test_user_recipe(client, recipe_id, headers,
                                       user_notes=123)
    assert response.status_code == 400


def test_add_duplicate_user_recipe(client):
    create_test_user(client)
    recipe_id = create_test_recipe(client).get_json()['id']
    headers = get_auth_headers(client)
    create_test_user_recipe(client, recipe_id, headers)
    response = create_test_user_recipe(client, recipe_id, headers)
    assert response.status_code == 409


def test_add_user_recipe_no_notes(client):
    create_test_user(client)
    recipe_id = create_test_recipe(client).get_json()['id']
    headers = get_auth_headers(client)
    response = create_test_user_recipe(client, recipe_id, headers,
                                       user_notes=None)
    assert response.status_code == 201


def test_get_specific_recipe_from_user_collection(client):
    create_test_user(client)
    recipe_id = create_test_recipe(client).get_json()['id']
    headers = get_auth_headers(client)
    create_test_user_recipe(client, recipe_id, headers)
    get_response = client.get(f'/api/users/recipes/{recipe_id}',
                              headers=headers)
    assert get_response.status_code == 200
    data = get_response.get_json()
    print(data)


def test_delete_user_recipe(client):
    create_test_user(client)
    recipe_id = create_test_recipe(client).get_json()['id']
    headers = get_auth_headers(client)
    create_test_user_recipe(client, recipe_id, headers)
    delete_response = client.delete(f'/api/users/recipes/{recipe_id}',
                                    headers=headers)
    assert delete_response.status_code == 200
    get_response = client.get(f'/api/users/recipes/{recipe_id}',
                              headers=headers)
    assert get_response.status_code == 404
