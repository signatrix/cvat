
# Copyright (C) 2020 Intel Corporation
#
# SPDX-License-Identifier: MIT

# FIXME: Git application and package name clash in tests
class _GitImportFix:
    import sys
    former_path = sys.path[:]

    @classmethod
    def apply(cls):
        # HACK: fix application and module name clash
        # 'git' app is found earlier than a library in the path.
        # The clash is introduced by unittest discover
        import sys
        print('apply')

        apps_dir = __file__[:__file__.rfind('/dataset_manager/')]
        assert 'apps' in apps_dir
        try:
            sys.path.remove(apps_dir)
        except ValueError:
            pass

        for name in list(sys.modules):
            if name.startswith('git.') or name == 'git':
                m = sys.modules.pop(name, None)
                del m

        import git
        assert apps_dir not in git.__file__

    @classmethod
    def restore(cls):
        import sys
        print('restore')

        for name in list(sys.modules):
            if name.startswith('git.') or name == 'git':
                m = sys.modules.pop(name)
                del m

        sys.path.insert(0, __file__[:__file__.rfind('/dataset_manager/')])

        import importlib
        importlib.invalidate_caches()

def _setUpModule():
    _GitImportFix.apply()
    import cvat.apps.dataset_manager as dm
    globals()['dm'] = dm

    import datumaro
    globals()['datumaro'] = datumaro

    import sys
    sys.path.insert(0, __file__[:__file__.rfind('/dataset_manager/')])

# def tearDownModule():
    # _GitImportFix.restore()

from io import BytesIO
import os.path as osp
import tempfile
import zipfile

from PIL import Image
from django.contrib.auth.models import User, Group
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

_setUpModule()

from cvat.apps.dataset_manager.annotation import AnnotationIR
from cvat.apps.dataset_manager.bindings import TaskData
from cvat.apps.engine.models import Task


def generate_image_file(filename, size=(100, 50)):
    f = BytesIO()
    image = Image.new('RGB', size=size)
    image.save(f, 'jpeg')
    f.name = filename
    f.seek(0)
    return f

class ForceLogin:
    def __init__(self, user, client):
        self.user = user
        self.client = client

    def __enter__(self):
        if self.user:
            self.client.force_login(self.user,
                backend='django.contrib.auth.backends.ModelBackend')

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.user:
            self.client.logout()

class _DbTestBase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @classmethod
    def setUpTestData(cls):
        cls.create_db_users()

    @classmethod
    def create_db_users(cls):
        group, _ = Group.objects.get_or_create(name="adm")

        admin = User.objects.create_superuser(
            username="test", password="test", email="")
        admin.groups.add(group)

        cls.user = admin

    def _put_api_v1_task_id_annotations(self, tid, data):
        with ForceLogin(self.user, self.client):
            response = self.client.put("/api/v1/tasks/%s/annotations" % tid,
                data=data, format="json")

        return response

    def _create_task(self, data, image_data):
        with ForceLogin(self.user, self.client):
            response = self.client.post('/api/v1/tasks', data=data, format="json")
            assert response.status_code == status.HTTP_201_CREATED, response.status_code
            tid = response.data["id"]

            response = self.client.post("/api/v1/tasks/%s/data" % tid,
                data=image_data)
            assert response.status_code == status.HTTP_202_ACCEPTED, response.status_code

            response = self.client.get("/api/v1/tasks/%s" % tid)
            task = response.data

        return task

class TaskExportTest(_DbTestBase):
    def _generate_annotations(self, task):
        annotations = {
            "version": 0,
            "tags": [
                {
                    "frame": 0,
                    "label_id": task["labels"][0]["id"],
                    "group": None,
                    "attributes": []
                }
            ],
            "shapes": [
                {
                    "frame": 0,
                    "label_id": task["labels"][0]["id"],
                    "group": None,
                    "attributes": [
                        {
                            "spec_id": task["labels"][0]["attributes"][0]["id"],
                            "value": task["labels"][0]["attributes"][0]["values"][0]
                        },
                        {
                            "spec_id": task["labels"][0]["attributes"][1]["id"],
                            "value": task["labels"][0]["attributes"][0]["default_value"]
                        }
                    ],
                    "points": [1.0, 2.1, 100, 300.222],
                    "type": "rectangle",
                    "occluded": False
                },
                {
                    "frame": 1,
                    "label_id": task["labels"][1]["id"],
                    "group": None,
                    "attributes": [],
                    "points": [2.0, 2.1, 100, 300.222, 400, 500, 1, 3],
                    "type": "polygon",
                    "occluded": False
                },
                {
                    "frame": 1,
                    "label_id": task["labels"][0]["id"],
                    "group": 1,
                    "attributes": [],
                    "points": [100, 300.222, 400, 500, 1, 3],
                    "type": "points",
                    "occluded": False
                },
                {
                    "frame": 1,
                    "label_id": task["labels"][0]["id"],
                    "group": 1,
                    "attributes": [],
                    "points": [2.0, 2.1, 400, 500, 1, 3],
                    "type": "polyline",
                    "occluded": False
                },
            ],
            "tracks": [
                {
                    "frame": 0,
                    "label_id": task["labels"][0]["id"],
                    "group": None,
                    "attributes": [
                        {
                            "spec_id": task["labels"][0]["attributes"][0]["id"],
                            "value": task["labels"][0]["attributes"][0]["values"][0]
                        },
                    ],
                    "shapes": [
                        {
                            "frame": 0,
                            "points": [1.0, 2.1, 100, 300.222],
                            "type": "rectangle",
                            "occluded": False,
                            "outside": False,
                            "attributes": [
                                {
                                    "spec_id": task["labels"][0]["attributes"][1]["id"],
                                    "value": task["labels"][0]["attributes"][1]["default_value"]
                                }
                            ]
                        },
                        {
                            "frame": 1,
                            "attributes": [],
                            "points": [2.0, 2.1, 100, 300.222],
                            "type": "rectangle",
                            "occluded": True,
                            "outside": True
                        },
                    ]
                },
                {
                    "frame": 1,
                    "label_id": task["labels"][1]["id"],
                    "group": None,
                    "attributes": [],
                    "shapes": [
                        {
                            "frame": 1,
                            "attributes": [],
                            "points": [1.0, 2.1, 100, 300.222],
                            "type": "rectangle",
                            "occluded": False,
                            "outside": False
                        }
                    ]
                },
            ]
        }
        self._put_api_v1_task_id_annotations(task["id"], annotations)
        return annotations

    def _generate_task_images(self, count):
        images = {
            "client_files[%d]" % i: generate_image_file("image_%d.jpg" % i)
            for i in range(count)
        }
        images["image_quality"] = 75
        return images

    def _generate_task(self, images):
        task = {
            "name": "my task #1",
            "owner": '',
            "assignee": '',
            "overlap": 0,
            "segment_size": 100,
            "z_order": False,
            "labels": [
                {
                    "name": "car",
                    "attributes": [
                        {
                            "name": "model",
                            "mutable": False,
                            "input_type": "select",
                            "default_value": "mazda",
                            "values": ["bmw", "mazda", "renault"]
                        },
                        {
                            "name": "parked",
                            "mutable": True,
                            "input_type": "checkbox",
                            "default_value": False
                        },
                    ]
                },
                {"name": "person"},
            ]
        }
        return self._create_task(task, images)

    @staticmethod
    def _test_export(check, task, format_name, **export_args):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = osp.join(temp_dir, format_name)
            dm.task.export_task(task["id"], file_path,
                format_name, **export_args)

            check(file_path)

    def test_export_formats_query(self):
        formats = dm.views.get_export_formats()

        self.assertEqual({f.DISPLAY_NAME for f in formats},
        {
            'COCO 1.0',
            'CVAT for images 1.1',
            'CVAT for video 1.1',
            'Datumaro 1.0',
            'LabelMe 3.0',
            'MOT 1.1',
            'PASCAL VOC 1.1',
            'Segmentation mask 1.1',
            'TFRecord 1.0',
            'YOLO 1.1',
        })

    def test_import_formats_query(self):
        formats = dm.views.get_import_formats()

        self.assertEqual({f.DISPLAY_NAME for f in formats},
        {
            'COCO 1.0',
            'CVAT 1.1',
            'LabelMe 3.0',
            'MOT 1.1',
            'PASCAL VOC 1.1',
            'Segmentation mask 1.1',
            'TFRecord 1.0',
            'YOLO 1.1',
        })

    def test_exports(self):
        def check(file_path):
            with open(file_path, 'rb') as f:
                self.assertTrue(len(f.read()) != 0)

        for f in dm.views.get_export_formats():
            if not f.ENABLED:
                self.skipTest("Format is disabled")

            format_name = f.DISPLAY_NAME
            for save_images in { True, False }:
                images = self._generate_task_images(3)
                task = self._generate_task(images)
                self._generate_annotations(task)
                with self.subTest(format=format_name, save_images=save_images):
                    self._test_export(check, task,
                        format_name, save_images=save_images)

    def test_empty_images_are_exported(self):
        dm_env = dm.formats.registry.dm_env

        for format_name, importer_name in [
            ('COCO 1.0', 'coco'),
            ('CVAT for images 1.1', 'cvat'),
            # ('CVAT for video 1.1', 'cvat'), # does not support
            ('Datumaro 1.0', 'datumaro_project'),
            ('LabelMe 3.0', 'label_me'),
            # ('MOT 1.1', 'mot_seq'), # does not support
            ('PASCAL VOC 1.1', 'voc'),
            ('Segmentation mask 1.1', 'voc'),
            ('TFRecord 1.0', 'tf_detection_api'),
            ('YOLO 1.1', 'yolo'),
        ]:
            with self.subTest(format=format_name):
                if not dm.formats.registry.EXPORT_FORMATS[format_name].ENABLED:
                    self.skipTest("Format is disabled")

                images = self._generate_task_images(3)
                task = self._generate_task(images)

                def check(file_path):
                    def load_dataset(src):
                        if importer_name == 'datumaro_project':
                            project = datumaro.components.project. \
                                Project.load(src)

                            # NOTE: can't import cvat.utils.cli
                            # for whatever reason, so remove the dependency
                            project.config.remove('sources')

                            return project.make_dataset()
                        return dm_env.make_importer(importer_name)(src) \
                            .make_dataset()

                    if zipfile.is_zipfile(file_path):
                        with tempfile.TemporaryDirectory() as tmp_dir:
                            zipfile.ZipFile(file_path).extractall(tmp_dir)
                            dataset = load_dataset(tmp_dir)
                    else:
                        dataset = load_dataset(file_path)

                    self.assertEqual(len(dataset), task["size"])
                self._test_export(check, task, format_name, save_images=False)

    def test_cant_make_rel_frame_id_from_unknown(self):
        images = self._generate_task_images(3)
        images['frame_filter'] = 'step=2'
        task = self._generate_task(images)
        task_data = TaskData(AnnotationIR(), Task.objects.get(pk=task['id']))

        with self.assertRaisesRegex(ValueError, r'Unknown'):
            task_data.rel_frame_id(1) # the task has only 0 and 2 frames

    def test_can_make_rel_frame_id_from_known(self):
        images = self._generate_task_images(6)
        images['frame_filter'] = 'step=2'
        images['start_frame'] = 1
        task = self._generate_task(images)
        task_data = TaskData(AnnotationIR(), Task.objects.get(pk=task['id']))

        self.assertEqual(2, task_data.rel_frame_id(5))

    def test_cant_make_abs_frame_id_from_unknown(self):
        images = self._generate_task_images(3)
        images['frame_filter'] = 'step=2'
        task = self._generate_task(images)
        task_data = TaskData(AnnotationIR(), Task.objects.get(pk=task['id']))

        with self.assertRaisesRegex(ValueError, r'Unknown'):
            task_data.abs_frame_id(2) # the task has only 0 and 1 indices

    def test_can_make_abs_frame_id_from_known(self):
        images = self._generate_task_images(6)
        images['frame_filter'] = 'step=2'
        images['start_frame'] = 1
        task = self._generate_task(images)
        task_data = TaskData(AnnotationIR(), Task.objects.get(pk=task['id']))

        self.assertEqual(5, task_data.abs_frame_id(2))
