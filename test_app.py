import pytest
import json
from config import create_app, db


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
