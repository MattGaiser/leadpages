import json
from pathlib import Path

import pytest
import vcr
from django.urls import reverse
from rest_framework.test import APIClient
from celery.result import EagerResult
from app.extractor.tasks import fetch_transform_post_animals


@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_trigger_task_and_task_execution(api_client, tmp_path):
    url = reverse('trigger_task')
    full_url = f"http://testserver{url}"
    response = api_client.get(full_url)

    assert response.status_code == 200
    assert "Task started" in response.json().get('status', '')

    result = fetch_transform_post_animals.apply()

    assert isinstance(result, EagerResult)
    assert result.status == 'SUCCESS'



