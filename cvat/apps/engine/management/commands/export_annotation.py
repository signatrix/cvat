
import os
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from cvat.apps.engine.models import Task
from cvat.apps.engine import annotation
from cvat.apps.annotation.models import AnnotationDumper

base_url = "http://localhost:8080/"
user, password = "cvat", "cvat1234"
# python3 manage.py export_annotation --tid=1 --dump_folder=/home/django/share/annotation


class Command(BaseCommand):
    help = 'Exports the XML File of a task id to the root of the share folder'

    def add_arguments(self, parser):
        parser.add_argument('--tid', nargs='+', type=int)
        parser.add_argument('--dump_folder', type=str,
                            default="/home/django/share/out")
        parser.add_argument('--user', type=str, default="bot")
        parser.add_argument('--delete', '-d', action='store_true',
                            help='Delete the task afterwards')

    def handle(self, *args, **options):
        if not os.path.exists(options['dump_folder']):
            os.makedirs(options['dump_folder'])
        user = User.objects.get(username=options['user'])

        for tid in options['tid']:
            db_task = Task.objects.get(id=tid)

            if db_task.assignee != user:
                db_task.owner = db_task.assignee or db_task.owner
                db_task.assignee = user
                db_task.save()

            dump_annotation_for_task(db_task, options['dump_folder'])
            if options['delete']:
                db_task.delete()


def dump_annotation_for_task(task, dump_folder, overwrite=False):
    output_path = os.path.join(dump_folder, task.name.replace('/', '_') + ".xml")
    print(output_path.replace("/home/django/share/", "/mnt/data/cvat_share/"))
    display_name = "CVAT XML 1.1 for videos"
    cvat_dumper = AnnotationDumper.objects.get(display_name=display_name)
    annotation.dump_task_data(task.id, user, output_path, cvat_dumper, 'http', 'localhost:8080')
    permissions = 0o770  # owner all, group read and write, executable
    os.chmod(output_path, permissions)
    os.chmod(dump_folder, permissions)
