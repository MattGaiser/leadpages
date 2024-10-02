import requests
from celery import shared_task, group
from celery.utils.log import get_task_logger
from datetime import datetime
import pytz
from pydantic import BaseModel
from typing import List, Optional
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = get_task_logger(__name__)

ANIMALS_API_URL = "http://host.docker.internal:3123/animals/v1/animals"
ANIMALS_HOME_URL = "http://host.docker.internal:3123/animals/v1/home"


class AnimalID(BaseModel):
    id: int

    class Config:
        allow_mutation = True


class AnimalRaw(BaseModel):
    id: int
    name: str
    born_at: Optional[int] = None
    friends: Optional[str] = None

    class Config:
        allow_mutation = True


class Animal(BaseModel):
    id: int
    name: str
    born_at: Optional[str] = None
    friends: List[str] = []

    class Config:
        allow_mutation = True


class AnimalApiClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def fetch_animals(self, page):
        response = requests.get(f"{self.base_url}?page={page}")
        response.raise_for_status()
        return response.json()

    def fetch_total_pages(self):
        response = requests.get(f"{self.base_url}?page=1")
        response.raise_for_status()
        data = response.json()
        return data.get('total_pages')

    def fetch_animal_data(self, animal_id):
        response = requests.get(f"{self.base_url}/{animal_id}")
        response.raise_for_status()
        return response.json()

    def post_animal_batch(self, animals):
        response = requests.post(ANIMALS_HOME_URL, json=animals)
        response.raise_for_status()
        return response


class AnimalExtractor:
    def __init__(self, client: AnimalApiClient):
        self.client = client

    def extract_animal_ids_batch(self, start_page=1, num_pages=10):
        animal_ids = []
        page_numbers = list(range(start_page, start_page + num_pages))

        def fetch_page(page):
            data = retry_api_call(self.client.fetch_animals, page, max_retries=3, delay=5)
            if not data:
                logger.error(f"Failed to fetch page {page}.")
                return []
            logger.info(f"Extracting IDs from page {page}")
            animals = data.get('items', [])
            return [AnimalID(**animal) for animal in animals]

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_page, page) for page in page_numbers]

            for future in as_completed(futures):
                animal_ids.extend(future.result())

        return animal_ids


class AnimalTransformer:
    @staticmethod
    def transform_animal(animal_raw: AnimalRaw) -> Animal:
        born_at_iso = None
        if animal_raw.born_at:
            born_at_iso = datetime.utcfromtimestamp(animal_raw.born_at / 1000).replace(tzinfo=pytz.UTC).isoformat()

        friends_list = []
        if animal_raw.friends:
            friends_list = animal_raw.friends.split(',')

        return Animal(
            id=animal_raw.id,
            name=animal_raw.name,
            born_at=born_at_iso,
            friends=friends_list,
        )

    def transform_all(self, raw_animals: List[AnimalRaw]) -> List[Animal]:
        return [self.transform_animal(animal_raw) for animal_raw in raw_animals]


class AnimalLoader:
    @staticmethod
    def post_batches(client: AnimalApiClient, animals: List[dict]):
        for i in range(0, len(animals), 100):
            batch = animals[i:i + 100]
            retry_api_call(client.post_animal_batch, batch, max_retries=3, delay=5)


def retry_api_call(api_call_func, *args, max_retries=3, delay=5, **kwargs):
    retries = 0
    while retries < max_retries:
        try:
            return api_call_func(*args, **kwargs)
        except requests.exceptions.RequestException as exc:
            retries += 1
            logger.warning(f"API call failed: {exc}. Retrying {retries}/{max_retries}...")
            if retries >= max_retries:
                logger.error(f"API call failed after {max_retries} retries: {exc}")
                return None
            time.sleep(delay)


@shared_task(bind=True)
def process_animal_batch(self, animal_ids):
    client = AnimalApiClient(ANIMALS_API_URL)
    transformer = AnimalTransformer()
    loader = AnimalLoader()

    detailed_raw_animals = []
    all_transformed_animals = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(retry_api_call, client.fetch_animal_data, animal_id['id'], max_retries=3, delay=5)
                   for animal_id in animal_ids]

        for future in as_completed(futures):
            detailed_data = future.result()
            if detailed_data:
                detailed_raw_animals.append(AnimalRaw(**detailed_data))

    transformed_animals = transformer.transform_all(detailed_raw_animals)
    all_transformed_animals.extend([animal.dict() for animal in transformed_animals])

    loader.post_batches(client, all_transformed_animals)


@shared_task(bind=True)
def fetch_transform_post_animals(self):
    client = AnimalApiClient(ANIMALS_API_URL)
    extractor = AnimalExtractor(client)

    total_pages = client.fetch_total_pages()
    logger.info(f"Total pages to process: {total_pages}")

    batch_size = 10
    start_page = 1

    sub_tasks = []
    for page in range(start_page, total_pages + 1, batch_size):
        animal_ids = extractor.extract_animal_ids_batch(start_page=page, num_pages=batch_size)

        animal_ids_dict = [animal_id.dict() for animal_id in animal_ids]

        sub_tasks.append(process_animal_batch.s(animal_ids_dict))

    group(sub_tasks).apply_async()
