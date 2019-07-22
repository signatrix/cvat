
import os
import shutil
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from cvat.apps.engine.models import Task
from cvat.apps.engine.annotation import _AnnotationForTask, FORMAT_XML


# python3 manage.py export_annotation --tid=1 --dump_folder=/home/django/share/annotation
class Command(BaseCommand):
    help = 'Exports the XML File of a task id to the root of the share folder'

    def add_arguments(self, parser):
        parser.add_argument('--tid', nargs='+', type=int)
        parser.add_argument('--dump_folder', type=str,
                            default="/home/django/share/annotation_tesco")
        parser.add_argument('--user', type=str, default="bot")

    def handle(self, *args, **options):
        if not os.path.exists(options['dump_folder']):
            os.makedirs(options['dump_folder'])
        user = User.objects.get(username=options['user'])

        for tid in options['tid']:
            db_task = Task.objects.get(id=tid)

            if db_task.assignee != user:
                db_task.owner = db_task.assignee
                db_task.assignee = user
                db_task.save()

            dump_annotation_for_task(db_task, options['dump_folder'])


def dump_annotation_for_task(task, dump_folder, overwrite=False):
    annotation = _AnnotationForTask(task)
    annotation.init_from_db()
    annotation.dump(FORMAT_XML, 'http', 'localhost:8080', {})
    path_to_dump = task.get_dump_path()
    output_path = os.path.join(dump_folder, os.path.basename(path_to_dump))
    if overwrite and os.path.exists(output_path):
        os.remove(output_path)
    shutil.move(path_to_dump, dump_folder)
    permissions = 0o760  # owner all, group read and write, executable
    os.chmod(dump_folder, permissions)
