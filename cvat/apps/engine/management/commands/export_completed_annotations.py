import os
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from cvat.apps.engine.task import delete
from cvat.apps.engine.models import Task
from .export_annotation import dump_annotation_for_task


# python3 manage.py export_completed_annotations --dump_folder=/home/django/share/exported_annotations/
class Command(BaseCommand):
    help = 'Exports completed annotations and deletes the imported tasks if the user wants'

    def add_arguments(self, parser):
        parser.add_argument('--dump_folder', type=str, default='/home/django/share/exported_annotations')

    def handle(self, *args, **options):
        if not os.path.exists(options['dump_folder']):
            os.makedirs(options['dump_folder'])

        exported_tasks = []
        for user in User.objects.all():
            tasks = Task.objects.filter(status='completed').filter(Q(assignee=user) | Q(owner=user))
            if tasks:
                for task in tasks:
                    if task not in exported_tasks:
                        dump_annotations(task, options['dump_folder'])
                        exported_tasks.append(task)
        if exported_tasks:
            print('\nThe following tasks have been exported to ' + options['dump_folder'] + ':')
            for task in exported_tasks:
                print('    Task ' + task.name + ', assignee: ' + task.assignee.username + ', owner: ' + task.owner.username)
            answer = input('\nShould these tasks be deleted now? (yes/no): ')
            if answer in ['yes', 'Yes']:
                for task in exported_tasks:
                    delete(task.id)
            else:
                print('\nNo tasks were deleted. Make sure you will not export them multiple times to red in the future.')
        else:
            print('No completed tasks were exported.')


def dump_annotations(task, dump_folder):
    task.owner = task.assignee
    task.assignee = User.objects.get(username='bot')
    task.save()
    dump_annotation_for_task(task, dump_folder)
