import os
import shutil
from datetime import datetime
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from cvat.apps.engine.models import Task
from cvat.apps.dataset_manager.task import delete_task_data

from .export_annotation import dump_annotation_for_task


# python3 manage.py export_completed_annotations --dump_folder=/home/django/share/out/
class Command(BaseCommand):
    help = 'Exports completed annotations and deletes the imported tasks if the user wants\nUse:\n./exec_manage export_completed_annotations --dump_folder=/home/django/share/out/'

    def add_arguments(self, parser):
        parser.add_argument('--dump_folder', type=str, default='')
        parser.add_argument('--overwrite', '-o', action='store_true',
                            help='Overwrite annotation if already present')
        parser.add_argument('--delete_tasks', '-d', action='store_true',
                            help='Delete the task after a successful export')
        parser.add_argument('--verbose', '-y', action='store_true',
                            help='Print status updates')

    def handle(self, *args, **options):
        if not options['dump_folder']:
            options['dump_folder'] = os.path.join("/home/django/share/out/", datetime.now().strftime("%Y_%m_%d"))
        verbose = options['verbose']
        exported_tasks = []
        for task in Task.objects.filter(status='completed', owner__isnull=False, assignee__isnull=False):
            try:
                dump_annotations(task, options['dump_folder'], overwrite=options['overwrite'])
                exported_tasks.append(task)
            except Exception as e:
                print(e)
                print("Could not export annotation for " + task.name + "\nContinuing...")
                continue
        if exported_tasks:
            if verbose:
                print('\nThe following tasks have been exported to ' + options['dump_folder'] + ':')
                for task in exported_tasks:
                    print('    Task ' + task.name + ', assignee: ' + task.assignee.username + ', owner: ' + task.owner.username)
            if options['delete_tasks']:
                answer = 'yes'
            else:
                answer = input('\nShould these tasks be deleted now? (yes/no): ')
            if answer in ['yes', 'Yes']:
                for task in exported_tasks:
                    delete_task(task)
            else:
                if verbose:
                    print('\nNo tasks were deleted. Make sure you will not export them multiple times to red in the future.')
        else:
            shutil.rmtree(options['dump_folder'], ignore_errors=True)


def dump_annotations(task, dump_folder, overwrite=False):
    if not os.path.exists(dump_folder):
        os.makedirs(dump_folder)
    if task.assignee.username != 'bot':
        task.owner = task.assignee
        task.assignee = User.objects.get(username='bot')
        task.save()
    if any(i in task.name for i in ('/', '.')):
        # case that the tasks name does not adhere to the database_datasetid[_labelsetid] format
        output_folder = dump_folder
    else:
        database = "_".join([s for s in task.name.split("_") if "0" not in s])
        output_folder = os.path.join(dump_folder, database)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    dump_annotation_for_task(task, output_folder, overwrite=overwrite)


def delete_task(task):
    try:
        delete_task_data(task.id, task.assignee)

        data_dirname = task.data.get_data_dirname()
        task_dirname = task.get_task_dirname()

        task.data.delete()
        task.delete()
    except Exception as e:
        print("Could not delete task data for " + str(task))
        print(e)
    else:
        shutil.rmtree(data_dirname, ignore_errors=True)
        shutil.rmtree(task_dirname, ignore_errors=True)
