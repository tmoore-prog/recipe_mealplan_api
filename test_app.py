import pytest
import json
from config import create_app, db
from datetime import datetime, timedelta

@pytest.fixture
def client():
    test_app = create_app(config_type='testing')

    with test_app.test_client() as client:
        with test_app.app_context():
            db.create_all()

            yield client

            db.session.remove()
            db.drop_all()


def test_get_empty_recipes_list(client):
    response = client.get('/api/recipes')
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
    response = client.post('/api/recipes', data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 201
    response = client.get('/api/recipes')
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
        response = client.post('/api/recipes', data=json.dumps(data),
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
    client.post('/api/recipes', data=json.dumps(data[0]),
                content_type='application/json')
    response = client.post('/api/recipes', data=json.dumps(data[1]),
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
    response = client.post('/api/recipes', data=json.dumps(data),
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
        response = client.post('/api/recipes', data=json.dumps(data),
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
    response = client.post('/api/recipes', data=json.dumps(data),
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
    response = client.post('/api/recipes', data=json.dumps(data),
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
    client.post('/api/recipes', data=json.dumps(data),
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
    create_response = client.post('/api/recipes', data=json.dumps(data),
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
    create_response = client.post('/api/recipes', data=json.dumps(data),
                                  content_type='application/json')
    recipe_id = create_response.get_json()['id']
    response = client.delete(f'/api/recipes/{recipe_id}')
    assert response.status_code == 200
    check = client.get(f'/api/recipes/{recipe_id}')
    assert check.status_code == 404

