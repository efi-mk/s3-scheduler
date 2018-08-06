from datetime import timedelta
from unittest import TestCase
from unittest.mock import MagicMock, patch
from urllib import parse

from s3_scheduler.scheduler import Scheduler
from s3_scheduler.utils import nowut


class SchedulerTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.s3_client = MagicMock()
        self.s3_resource = MagicMock()

        self.scheduler = Scheduler("bucket", "/path", self.s3_resource, self.s3_client)

    def test_stop_error_occured_return_false(self):
        self.s3_client.delete_object.side_effect = Exception()
        self.assertFalse(self.scheduler.stop("key"))

    def test_schedule_file_saved_in_right_format(self):
        now = nowut()
        upload_to = self.scheduler.schedule(now, "s3-bucket", "s3_files-important+", "content")

        self.assertEqual(upload_to, f'/path/|{parse.quote(str(now))}|s3-bucket|{parse.quote("s3_files-important+")}')

    @patch("s3_scheduler.scheduler.move_file")
    def test_handle_a_valid_file_time_arrived_file_is_copied(self, move_file_mock):
        time = nowut() - timedelta(minutes=10)
        upload_to = self.scheduler.schedule(time, "s3-bucket", "s3_files-important+", "content")

        mock_bucket = MagicMock(name="test")
        mock_result = MagicMock()
        mock_result.key = upload_to

        mock_bucket.objects.filter.return_value = [mock_result]
        self.s3_resource.Bucket.return_value = mock_bucket

        self.scheduler.handle()

        move_file_mock.assert_called_once_with("bucket", "s3-bucket", upload_to, self.s3_client, "s3_files-important+")

    @patch("s3_scheduler.utils.move_file")
    def test_handle_a_valid_file_time_not_arrived_file_is_not_copied(self, move_file_mock):
        time = nowut() + timedelta(minutes=10)
        upload_to = self.scheduler.schedule(time, "s3-bucket", "s3_files-important+", "content")

        mock_bucket = MagicMock(name="test")
        mock_result = MagicMock()
        mock_result.key = upload_to

        mock_bucket.objects.filter.return_value = [mock_result]
        self.s3_resource.Bucket.return_value = mock_bucket

        self.scheduler.handle()

        move_file_mock.assert_not_called()

    @patch("s3_scheduler.utils.move_file")
    def test_handle_an_invalid_file_file_is_not_copied(self, move_file_mock):
        time = nowut() - timedelta(minutes=10)
        upload_to = self.scheduler.schedule(time, "s3-bucket", "s3_files-important+", "content")

        mock_bucket = MagicMock(name="test")
        mock_result = MagicMock()
        mock_result.key = upload_to + "|ddd"

        mock_bucket.objects.filter.return_value = [mock_result]
        self.s3_resource.Bucket.return_value = mock_bucket

        self.scheduler.handle()

        move_file_mock.assert_not_called()

    @patch("s3_scheduler.utils.move_file")
    def test_handle_an_invalid_time_format_file_is_not_copied(self, move_file_mock):
        time = nowut() - timedelta(minutes=10)
        upload_to = self.scheduler.schedule(time, "s3-bucket", "s3_files-important+", "content")

        mock_bucket = MagicMock(name="test")
        mock_result = MagicMock()
        mock_result.key = upload_to.replace(str(time.year), "Hello")

        mock_bucket.objects.filter.return_value = [mock_result]
        self.s3_resource.Bucket.return_value = mock_bucket

        self.scheduler.handle()

        move_file_mock.assert_not_called()

    @patch("s3_scheduler.scheduler.move_file")
    @patch("s3_scheduler.scheduler.warn")
    def test_handle_unable_to_copy_file_handle_gracefully(self, warn_mock, move_file_mock):
        time = nowut() - timedelta(minutes=10)
        upload_to = self.scheduler.schedule(time, "s3-bucket", "s3_files-important+", "content")

        mock_bucket = MagicMock(name="test")
        mock_result = MagicMock()
        mock_result.key = upload_to

        mock_bucket.objects.filter.return_value = [mock_result]
        self.s3_resource.Bucket.return_value = mock_bucket
        move_file_mock.side_effect = Exception()

        # noinspection PyTypeChecker
        self.scheduler.handle()

        warn_mock.assert_called_once()
