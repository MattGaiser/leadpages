import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List

import pytz
import requests
from celery.utils.log import get_task_logger

from celery import group, shared_task

from .client import DEFAULT_BASE_URL, AnimalApiClient
from .models import Animal, AnimalID, AnimalRaw

logger = get_task_logger(__name__)


class AnimalExtractor:
    def __init__(self, client: AnimalApiClient):
        self.client = client

    def extract_animal_ids_batch(self, start_page=1, num_pages=10):
        """Extracts the animal IDs in batches of 10 pages"""
        animal_ids = []
        page_numbers = list(range(start_page, start_page + num_pages))

        def fetch_page(page: int):
            """Fetches the passed page"""
            data = retry_api_call(
                self.client.fetch_animals, page, max_retries=3, delay=5
            )
            if not data:
                logger.error(f"Failed to fetch page {page}.")
                return []
            logger.info(f"Extracting IDs from page {page}")
            animals = data.get("items", [])
            return [AnimalID(**animal) for animal in animals]

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_page, page) for page in page_numbers]

            for future in as_completed(futures):
                animal_ids.extend(future.result())

        return animal_ids


class AnimalTransformer:
    @staticmethod
    def transform_animal(animal_raw: AnimalRaw) -> Animal:
        """Converts the raw data into the format specified for the home API"""
        born_at_iso = None
        if animal_raw.born_at:
            born_at_iso = (
                datetime.utcfromtimestamp(animal_raw.born_at / 1000)
                .replace(tzinfo=pytz.UTC)
                .isoformat()
            )

        friends_list = []
        if animal_raw.friends:
            friends_list = animal_raw.friends.split(",")

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
    def post_batches(client: "AnimalApiClient", animals: List[dict]):
        """Sends lists of Animal data to the home API and if audit mode is configured,
        generates the IDs in batched audit logs"""
        if client.audit_mode:
            audit_dir = Path(client.audit_dir)
            audit_dir.mkdir(parents=True, exist_ok=True)

        for i in range(0, len(animals), 100):
            batch = animals[i : i + 100]

            if client.audit_mode:
                ids = [animal["id"] for animal in batch]
                file_name = f"batch_{uuid.uuid4()}.json"
                file_path = Path(client.audit_dir) / file_name

                with open(file_path, "w") as f:
                    json.dump(ids, f)

            retry_api_call(client.post_animal_batch, batch, max_retries=3, delay=5)


def retry_api_call(api_call_func, *args, max_retries=3, delay=5, **kwargs):
    """Wrapper that retries failed API calls and logs both individual and repeated failures"""
    retries = 0
    while retries < max_retries:
        try:
            return api_call_func(*args, **kwargs)
        except requests.exceptions.RequestException as exc:
            retries += 1
            logger.warning(
                f"API call failed: {exc}. Retrying {retries}/{max_retries}..."
            )
            if retries >= max_retries:
                logger.error(f"API call failed after {max_retries} retries: {exc}")
                return None
            time.sleep(delay)


@shared_task(bind=True)
def process_animal_batch(self, animal_ids, base_url, audit_mode, audit_dir):
    """Takes the AnimalIDs and uses them to get the Animal detail data"""
    client = AnimalApiClient(
        base_url=base_url, audit_mode=audit_mode, audit_dir=audit_dir
    )
    transformer = AnimalTransformer()
    loader = AnimalLoader()

    detailed_raw_animals = []
    all_transformed_animals = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(
                retry_api_call,
                client.fetch_animal_data,
                animal_id["id"],
                max_retries=3,
                delay=5,
            )
            for animal_id in animal_ids
        ]

        for future in as_completed(futures):
            detailed_data = future.result()
            if detailed_data:
                detailed_raw_animals.append(AnimalRaw(**detailed_data))

    transformed_animals = transformer.transform_all(detailed_raw_animals)
    all_transformed_animals.extend(
        [animal.model_dump() for animal in transformed_animals]
    )

    loader.post_batches(client, all_transformed_animals)


@shared_task(bind=True)
def fetch_transform_post_animals(
    self, base_url=DEFAULT_BASE_URL, audit_mode=False, audit_dir="audit_dir"
):
    """Iterates through the pages of Animals and creates additional Celery
    tasks to get the detail data on those animals"""
    client = AnimalApiClient(
        base_url=base_url, audit_mode=audit_mode, audit_dir=audit_dir
    )
    extractor = AnimalExtractor(client)

    total_pages = client.fetch_total_pages()
    logger.info(f"Total pages to process: {total_pages}")

    batch_size = 10
    start_page = 1

    sub_tasks = []
    for page in range(start_page, total_pages + 1, batch_size):
        animal_ids = extractor.extract_animal_ids_batch(
            start_page=page, num_pages=batch_size
        )

        animal_ids_dict = [animal_id.model_dump() for animal_id in animal_ids]

        sub_tasks.append(
            process_animal_batch.s(animal_ids_dict, base_url, audit_mode, audit_dir)
        )

    group(sub_tasks).apply_async()
