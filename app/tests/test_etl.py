import pytest
import requests
import vcr
from datetime import datetime
import pytz

from app.extractor.tasks import AnimalApiClient, AnimalRaw, AnimalTransformer, fetch_transform_post_animals


@pytest.fixture
def api_client():
    return AnimalApiClient(base_url="http://host.docker.internal:3123")


@pytest.fixture
def vcr_config():
    return {
        'record_mode': 'once'
    }


@vcr.use_cassette('tests/fixtures/vcr_cassettes/fetch_total_pages.yaml')
def test_fetch_total_pages(api_client):
    total_pages = api_client.fetch_total_pages()
    assert isinstance(total_pages, int)
    assert total_pages > 0


@vcr.use_cassette('tests/fixtures/vcr_cassettes/fetch_animals_page_1.yaml')
def test_fetch_animals_page(api_client):
    animals_data = api_client.fetch_animals(page=1)
    assert isinstance(animals_data, dict)
    assert 'items' in animals_data
    assert isinstance(animals_data['items'], list)
    assert len(animals_data['items']) > 0


@vcr.use_cassette('tests/fixtures/vcr_cassettes/fetch_animal_data.yaml')
def test_fetch_animal_data(api_client):
    animal_data = api_client.fetch_animal_data(animal_id=1)
    assert isinstance(animal_data, dict)
    assert 'id' in animal_data
    assert animal_data['id'] == 1


def test_transform_animal():
    born_at = 1444102907778
    animal_raw = AnimalRaw(
        id=1,
        name="Cobra",
        born_at=born_at,
        friends="Dog,Cat"
    )

    transformer = AnimalTransformer()
    transformed_animal = transformer.transform_animal(animal_raw)

    assert transformed_animal.id == animal_raw.id
    assert transformed_animal.name == animal_raw.name
    assert transformed_animal.friends == ['Dog', 'Cat']

    assert transformed_animal.born_at == datetime.utcfromtimestamp(born_at / 1000).replace(
        tzinfo=pytz.UTC).isoformat()


@vcr.use_cassette('tests/fixtures/vcr_cassettes/post_animal_batch.yaml')
def test_post_animal_batch(api_client):
    animals = [
        {
            "id": 0,
            "name": "Panda",
            "born_at": "2024-07-21T08:55:34.421Z",
            "friends": ["Koala", "Sloth"]
        },
        {
            "id": 1,
            "name": "Penguin",
            "born_at": "2024-06-21T11:15:27.789Z",
            "friends": ["Seal", "Walrus"]
        },
        {
            "id": 2,
            "name": "Wolf",
            "born_at": "2024-05-21T19:35:09.654Z",
            "friends": ["Bear", "Fox"]
        }
    ]

    response = api_client.post_animal_batch(animals)
    assert response.status_code == 200

