from cvat.apps.engine.models import TrackedShape
from cvat.apps.engine.frame_provider import FrameProvider

import numpy as np
import cv2
import copy


def rectangle_to_cv_bbox(rectangle_points):
    """
    Convert the CVAT rectangle points (serverside) to a OpenCV rectangle.
    :param tuple rectangle_points: Tuple of form (x1,y1,x2,y2)
    :return: Form (x1, y1, width, height)
    """
    # Dimensions must be ints, otherwise tracking throws a exception
    return (int(rectangle_points[0]), int(rectangle_points[1]),
            int(rectangle_points[2] - rectangle_points[0]),
            int(rectangle_points[3] - rectangle_points[1]))

def cv_bbox_to_rectangle(cv_bbox):
    """
    Convert the OpenCV bounding box points to a CVAT rectangle points.
    :param tuple cv_bbox: Form (x1, y1, width, height)
    :return: Form (x1,y1,x2,y2)
    """
    return (cv_bbox[0], cv_bbox[1], cv_bbox[0] + cv_bbox[2], cv_bbox[1] + cv_bbox[3])

POINT_WIDTH = 50  # arbitrary value
POINT_HEIGHT = 50

def point_to_cv_bbox(point):
    """
    Convert the CVAT point (serverside) to a OpenCV rectangle.
    :param tuple point: Tuple of form (x1,y1)
    :return: Form (x1, y1, width, height)
    """
    # Dimensions must be ints, otherwise tracking throws a exception
    x, y = point
    return (int(x - POINT_WIDTH // 2), int(y - POINT_HEIGHT // 2),
            POINT_WIDTH, POINT_HEIGHT)

def cv_bbox_to_point(cv_bbox):
    """
    Convert the OpenCV bounding box points to a CVAT point.
    :param tuple cv_bbox: Form (x1, y1, width, height)
    :return: Form (x1,y1)
    """
    x1, y1, width, height = cv_bbox
    return (x1 + width // 2, y1 + height // 2)  # center



def image_iterable_from_task(task, start_frame, stop_frame):
    """
    Create a iterable to iterate over the images from a CVAT task.
    :param Task task The Django model of type Task
    :param int start_frame: Frame number where iteration should start (included)
    :param int stop_frame: First frame that is excluded from iteration (excluded)
    :return: Iterable over OpenCV images
    """
    fp = FrameProvider(task.data)
    for frame in range(start_frame, stop_frame + 1):
        buffer, _ = fp.get_frame(frame)
        arr = np.fromstring(buffer.read(), np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        yield frame, img

class RectangleTracker:
    tracker_types = ['BOOSTING', 'MIL', 'KCF', 'CSRT', 'MEDIANFLOW', 'TLD',
        'MOSSE', 'GOTRUN']

    def __init__(self, tracker_type = "BOOSTING"):
        """Create tracker.
        :param str tracker_type: String specifying tracker, see tracker_types.
        """
        self.tracker_factory = {
            'BOOSTING': cv2.TrackerBoosting_create,
            'MIL': cv2.TrackerMIL_create,
            'KCF': cv2.TrackerKCF_create,
            'CSRT': cv2.TrackerCSRT_create,
            'MEDIANFLOW': cv2.TrackerMedianFlow_create,
            'TLD': cv2.TrackerTLD_create,
            'MOSSE': cv2.TrackerMOSSE_create,
            'GOTRUN': cv2.TrackerGOTURN_create,
        }

        if tracker_type not in self.tracker_factory:
            raise Exception("Tracker type not known:" + tracker_type)

        self._tracker_type = tracker_type

    def track_rectangles(self, task, start_shapes, stop_frame):
        # Only track in to future.
        start_frame = start_shapes[0].frame
        if stop_frame < start_frame:
            return []

        # Load the image iterable for range of frames
        # and init the tracker with the bounding box from the user given shape
        images = image_iterable_from_task(task, start_frame, stop_frame)
        img0 = next(images)[1]

        trackers = cv2.MultiTracker_create()

        for shape in start_shapes:
            bbox = rectangle_to_cv_bbox(shape.points)
            tracker = self.tracker_factory[self._tracker_type]()
            trackers.add(tracker, img0, bbox)

        #Generated shapes
        shapes_by_tracking = []
        for frame, img  in images:
            # Let the tracker find the bounding box in the next image(s)
            no_errors, boxes = trackers.update(img)

            if no_errors:
                for shape, bbox in zip(start_shapes, boxes):
                    new_shape = copy.copy(shape)
                    new_shape.points = cv_bbox_to_rectangle(bbox)
                    new_shape.frame = frame
                    shapes_by_tracking.append(new_shape)
            else:
                break

        return shapes_by_tracking

class PointsTracker:
    tracker_types = ['BOOSTING', 'MIL', 'KCF', 'CSRT', 'MEDIANFLOW', 'TLD',
        'MOSSE', 'GOTRUN']

    def __init__(self, tracker_type = "CSRT"):
        """Create tracker.
        :param str tracker_type: String specifying tracker, see tracker_types.
        """
        self.tracker_factory = {
            'BOOSTING': cv2.TrackerBoosting_create,
            'MIL': cv2.TrackerMIL_create,
            'KCF': cv2.TrackerKCF_create,
            'CSRT': cv2.TrackerCSRT_create,
            'MEDIANFLOW': cv2.TrackerMedianFlow_create,
            'TLD': cv2.TrackerTLD_create,
            'MOSSE': cv2.TrackerMOSSE_create,
            'GOTRUN': cv2.TrackerGOTURN_create,
        }

        if tracker_type not in self.tracker_factory:
            raise Exception("Tracker type not known:" + tracker_type)

        self._tracker_type = tracker_type

    def track_multi_points(self, task, starting_shapes, stop_frame):
        # Only track in to future.
        start_frame = starting_shapes[0].frame
        if stop_frame < start_frame:
            return []

        # Load the image iterable for range of frames
        # and init the tracker with the bounding box from the user given shape
        images = image_iterable_from_task(task, start_frame, stop_frame)
        img0 = next(images)[1]

        trackers = cv2.MultiTracker_create()

        for shape in starting_shapes:
            bbox = point_to_cv_bbox(shape.points)
            tracker = self.tracker_factory[self._tracker_type]()
            trackers.add(tracker, img0, bbox)

        #Generated shapes
        shapes_by_tracking = []
        for frame, img  in images:
            # Let the tracker find the bounding box in the next image(s)
            no_errors, boxes = trackers.update(img)

            if no_errors:
                for shape, bbox in zip(starting_shapes, boxes):
                    new_shape = copy.copy(shape)
                    new_shape.points = cv_bbox_to_point(bbox)
                    new_shape.frame = frame
                    shapes_by_tracking.append(new_shape)
            else:
                break

        return shapes_by_tracking
