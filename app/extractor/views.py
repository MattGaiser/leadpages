from django.http import JsonResponse
from .tasks import fetch_transform_post_animals


def trigger_task(request):
    task = fetch_transform_post_animals.delay()
    return JsonResponse({'status': 'Task started', 'task_id': task.id})
