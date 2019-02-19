from django.core.management.base import BaseCommand

from cvat.apps.engine.models import Job, Label, ObjectPath, Segment, Task, TrackedBox


class Command(BaseCommand):
    help = 'Prints some database information'

    def add_arguments(self, parser):
        parser.add_argument('--quiet', '-q', action='store_true',
                            help='Only display numeric IDs')
        parser.add_argument('--sort_by', type=int,
                            help='sort by column id: (0) TASK ID, (1) TASK NAME, \
                             (2) ANNOT., (3) CARTS, (4) PERSONS, (5) BBOXES, \
                             (6) CREATED AT, (7) SAVED/UPDATED AT, (8) STATUS',
                            default=0)
        parser.add_argument('--desc', '-d', action='store_true',
                            help='descending ordering')
        parser.add_argument('--completed', '-c', action='store_true',
                            help='only get completed')

    def handle(self, *args, **options):
        if options['completed']:
            task_query_set = Task.objects.filter(status='completed').order_by('-id')
        else:
            task_query_set = Task.objects.all().order_by('-id')

        if options['quiet']:
            for task in task_query_set:
                print(task.id)
            return

        tab = 4
        # maybe this? name_width = min(max(map(lambda task: len(task.name), task_query_set), 80) + tab
        name_width = min(max(map(lambda x: len(x.name), Task.objects.all())), 80) + tab

        print("{:<10} {:<{}} {:<12} {:<9} {:<11} {:<10} {:<23} {:<23} {:<10}".format('TASK ID', 'TASK NAME', name_width, 'ANNOTATOR', 'CARTS', 'PERSONS',
                                                                                     'BBOXES', 'CREATED AT', 'SAVED/UPDATED AT', 'STATUS'))

        table_content = []

        for task in task_query_set:
            try:
                annotator_name = task.assignee.username
            except Exception:
                annotator_name = 'None'

            cart_label_obj = Label.objects.filter(name='cart', task=task).first()
            person_label_obj = Label.objects.filter(name='person', task=task).first()

            job = Job.objects.filter(segment=Segment.objects.filter(task=task).first()).first()

            if cart_label_obj:
                cart_objects = list(ObjectPath.objects.filter(job=job, label=cart_label_obj))
                carts_count = len(cart_objects)
            else:
                cart_objects = []
                carts_count = 'None'

            if person_label_obj:
                person_objects = list(ObjectPath.objects.filter(job=job, label=person_label_obj))
                persons_count = len(person_objects)
            else:
                person_objects = []
                persons_count = 'None'

            track_ids = list(map(lambda x: x.id, cart_objects + person_objects))
            bboxes = TrackedBox.objects.filter(track_id__in=track_ids).count()

            table_content.append((task.id, task.name, name_width, annotator_name, carts_count, persons_count, bboxes,
                                  task.created_date.strftime('%Y-%m-%d %H:%M:%S'), task.updated_date.strftime('%Y-%m-%d %H:%M:%S'), task.status))

        table_content = sorted(table_content, key=lambda x: x[options['sort_by']], reverse=options['desc'])

        for row in table_content:
            print("{:<10} {:<{}} {:<12} {:<9} {:<11} {:<10} {:<23} {:<23} {:<10}".format(*row))
