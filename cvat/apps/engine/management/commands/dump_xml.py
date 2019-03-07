
import os
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from cvat.apps.engine.models import Task
from cvat.apps.engine.annotation import _AnnotationForTask, FORMAT_XML

# python3 manage.py dump_xml --tid=1 --dump_folder=/home/django/share/annotation
class Command(BaseCommand):
    help = 'Dumps the XML File of a task id to the root of the share folder'

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


def dump_annotation_for_task(task, dump_folder):
    task.path = dump_folder
    annotation = _AnnotationForTask(task)
    annotation.init_from_db()
    annotation.dump(FORMAT_XML, 'http', 'localhost:8080', {})
