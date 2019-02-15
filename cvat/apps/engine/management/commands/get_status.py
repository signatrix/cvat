from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from ... import models


class Command(BaseCommand):
    help = 'Prints some database information'

    def handle(self, *args, **options):

        labels = models.Label.objects.all()
        segments = models.Segment.objects.all()
        jobs = models.Job.objects.all()
        objectpaths = models.ObjectPath.objects.all()
        trackedboxes = models.TrackedBox.objects.all()
        annotators = User.objects.all()

        tab = 4
        name_width = min(max(map(lambda x: len(x.name), models.Task.objects.all())), 80) + tab

        print("{:<10} {:<{}} {:<12} {:<9} {:<11} {:<10} {:<23} {:<23} {:<10}".format('task id', 'task name', name_width, 'annotator', 'carts', 'persons', 'bboxes', 'created date', 'saved/updated at', 'status'))

        for task in models.Task.objects.all():
            try:
                annotator_name = next(filter(lambda x: x.id == task.assignee_id, annotators)).username
            except Exception:
                annotator_name = 'None'

            cart_label_obj = next(filter(lambda x: x.task_id == task.id and x.name == 'cart', labels), None)
            person_label_obj = next(filter(lambda x: x.task_id == task.id and x.name == 'person', labels), None)

            segment_id = next(filter(lambda x: x.task_id == task.id, segments)).id
            job_id = next(filter(lambda x: x.segment_id == segment_id, jobs)).id

            if cart_label_obj:
                cart_objects = list(filter(lambda x: x.job_id == job_id and x.label_id == cart_label_obj.id, objectpaths))
                carts_count = len(cart_objects)
            else:
                cart_objects = []
                carts_count = 'None'

            if person_label_obj:
                person_objects = list(filter(lambda x: x.job_id == job_id and x.label_id == person_label_obj.id, objectpaths))
                persons_count = len(person_objects)
            else:
                person_objects = []
                persons_count = 'None'

            track_ids = list(map(lambda x: x.id, cart_objects + person_objects))
            bboxes = len(list(filter(lambda x: x.track_id in track_ids, trackedboxes)))

            print("{:<10} {:<{}} {:<12} {:<9} {:<11} {:<10} {:<23} {:<23} {:<10}".format(task.id, task.name, name_width, annotator_name, carts_count, persons_count, bboxes, task.created_date.strftime('%Y-%m-%d %H:%M:%S'), task.updated_date.strftime('%Y-%m-%d %H:%M:%S'), task.status))
