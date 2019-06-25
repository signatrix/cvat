from django.core.management.base import BaseCommand

from cvat.apps.engine.models import Task

# python3 manage.py rename_task --task_name='bla' --new_name='blub'


class Command(BaseCommand):
    help = "Renames a task\nUse:\n./exec_manage rename_task --task_name='bla' --new_name='blub'"

    def add_arguments(self, parser):
        parser.add_argument('--task_name', type=str)
        parser.add_argument('--new_name', type=str)

    def handle(self, *args, **options):
        task = Task.objects.filter(name=options['task_name']).first()
        if task:
            task.name = options['new_name']
            task.save()
        else:
            raise ValueError("No such task: " + options['task_name'])
