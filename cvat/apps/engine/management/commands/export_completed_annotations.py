import os
from datetime import datetime
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from cvat.apps.engine.models import Task
from .export_annotation import dump_annotation_for_task


# python3 manage.py export_completed_annotations --dump_folder=/home/django/share/exported_annotations/
class Command(BaseCommand):
    help = 'Exports completed annotations and deletes the imported tasks if the user wants\nUse:\n./exec_manage export_completed_annotations --dump_folder=/home/django/share/exported_annotations/'

    def add_arguments(self, parser):
        parser.add_argument('--dump_folder', type=str, default='')
        parser.add_argument('--overwrite', '-o', action='store_true',
                            help='Overwrite annotation if already present')

    def handle(self, *args, **options):
        if not options['dump_folder']:
            options['dump_folder'] = os.path.join("/home/django/share/exported_annotations/", datetime.now().strftime("%Y_%m_%d"))
        if not os.path.exists(options['dump_folder']):
            os.makedirs(options['dump_folder'])

        exported_tasks = []
        for user in User.objects.all():
            tasks = Task.objects.filter(status='completed').filter(Q(assignee=user) | Q(owner=user))
            if tasks:
                for task in tasks:
                    if task not in exported_tasks:
                        try:
                            dump_annotations(task, options['dump_folder'], overwrite=options['overwrite'])
                            exported_tasks.append(task)
                        except Exception as e:
                            print(e)
                            print("Could not export annotation for " + task.name + "\nContinuing...")
                            continue
        if exported_tasks:
            print('\nThe following tasks have been exported to ' + options['dump_folder'] + ':')
            for task in exported_tasks:
                print('    Task ' + task.name + ', assignee: ' + task.assignee.username + ', owner: ' + task.owner.username)
            answer = input('\nShould these tasks be deleted now? (yes/no): ')
            if answer in ['yes', 'Yes']:
                for task in exported_tasks:
                    task.delete()
            else:
                print('\nNo tasks were deleted. Make sure you will not export them multiple times to red in the future.')
        else:
            print('No completed tasks were exported.')


def dump_annotations(task, dump_folder, overwrite=False):
    if task.assignee.username != 'bot':
        task.owner = task.assignee
        task.assignee = User.objects.get(username='bot')
        task.save()
    dump_annotation_for_task(task, dump_folder, overwrite=overwrite)
