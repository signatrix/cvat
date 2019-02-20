import os
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from cvat.apps.engine.task import delete
from cvat.apps.engine.models import Task
from .dump_xml import dump_annotation_for_task


class Command(BaseCommand):
    help = 'Exports completed annotations and deletes the imported tasks if the user wants'

    def add_arguments(self, parser):
        parser.add_argument('--dump_folder', type=str, default='/home/django/share/exported_annotations')

    def handle(self, *args, **options):
        if not os.path.exists(options['dump_folder']):
            os.makedirs(options['dump_folder'])
        for user in User.objects.all():
            dump_completed_annotations_for_user(user)


def dump_completed_annotations_for_user(user, dump_folder):
    tasks = Task.objects.filter(status='completed', assignee=user)
    if tasks:
        print('\nThe following tasks from ' + user.name + ' have been exported to ' + 'dump_folder' + ':')
        for task in tasks:
            task.owner = task.assignee
            task.assignee = User.objects.get(username='bot')
            task.save()
            dump_annotation_for_task(task, 'dump_folder')
            print('    Task ' + task + ', assignee: ' + task.assignee + ', owner: ' + task.owner)
        answer = input('\nShould these tasks be deleted now? (yes/no)    ')
        if answer in ['yes', 'Yes']:
            for task in tasks:
                delete(task.id)
        else:
            print('\nNo tasks were deleted. Make sure you will not double export them to red in the future.')
    else:
        print("No completed tasks found for " + user.name + ".")
