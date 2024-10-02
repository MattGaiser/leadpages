import requests

ANIMALS_API_URL = "/animals/v1/animals"
ANIMALS_HOME_URL = "/animals/v1/home"
DEFAULT_BASE_URL = "http://host.docker.internal:3123"


class AnimalApiClient:
    def __init__(self, base_url="http://host.docker.internal:3123", audit_mode: bool = False,
                 audit_dir: str = 'audit_directory'):
        self.base_url = base_url
        self.audit_mode = audit_mode
        self.audit_dir = audit_dir

    def fetch_animals(self, page):
        response = requests.get(f"{self.base_url}{ANIMALS_API_URL}?page={page}")
        response.raise_for_status()
        return response.json()

    def fetch_total_pages(self):
        response = requests.get(f"{self.base_url}{ANIMALS_API_URL}?page=1")
        response.raise_for_status()
        data = response.json()
        return data.get('total_pages')

    def fetch_animal_data(self, animal_id):
        response = requests.get(f"{self.base_url}{ANIMALS_API_URL}/{animal_id}")
        response.raise_for_status()
        return response.json()

    def post_animal_batch(self, animals):
        response = requests.post(f"{self.base_url}{ANIMALS_HOME_URL}", json=animals)
        response.raise_for_status()
        return response
