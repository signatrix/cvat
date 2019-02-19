from django.core.management.base import BaseCommand

from cvat.apps.engine.models import Task


class Command(BaseCommand):
    help = 'Renames a task'

    def add_arguments(self, parser):
        parser.add_argument('--task_name', type=str)
        parser.add_argument('--new_name', type=str)

    def handle(self, *args, **options):
        task = Task.objects.filter(task_name=options['task_name'])
        if task:
            task.name = options['new_name']
            task.save()
        else:
            raise ValueError("No such task: " + options['task_name'])
