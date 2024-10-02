from django.http import JsonResponse
from .tasks import fetch_transform_post_animals


def trigger_task(request):
    DEFAULT_BASE_URL = "http://host.docker.internal:3123"
    audit_mode = request.GET.get('audit_mode', 'false').lower() == 'true'
    task = fetch_transform_post_animals.delay(base_url=DEFAULT_BASE_URL, audit_mode=audit_mode, audit_dir='audit_dir')
    return JsonResponse({'status': 'Task started', 'task_id': task.id})
