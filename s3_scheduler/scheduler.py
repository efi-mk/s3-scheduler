import io
from datetime import datetime

from dateutil.parser import parse as date_parser
from typing import Tuple, Any
from urllib import parse

from .utils import nowut, info, warn, move_file
from .utils import add_utc_tz


class Scheduler:
    def __init__(self, bucket: str, path: str, s3_resource, s3_client) -> None:
        """
        :param bucket: In which bucket to store the scheduled tasks
        :param path: The key in S3 to keep the scheduled tasks
        """
        super().__init__()
        self._bucket = bucket
        self._path = path if not path.endswith("/") else path[:-1]
        self._s3_resource = s3_resource

        self._s3_client = s3_client

    def schedule(self, when: datetime, bucket: str, path: str, what: str) -> str:
        """
        Schedule a file to be copied to a specific location.
        :param when: When to schedule the file copying
        :param bucket: Copy to this bucket
        :param path:Path to which to copy, includes the directory and file name. Should not start with '/'
        :param what: The actual content to copy.
        :return: Full path of where the file was copied to
        """
        when_escaped = parse.quote(str(add_utc_tz(when)))
        bucket_escaped = parse.quote(bucket)
        # / is treated as directory mark in S3 so replace it with something else
        path_escaped = parse.quote(path if not path.startswith("/") else path[1:]).replace("/", "~~")

        if "|" in when_escaped or "|" in bucket_escaped or "|" in path_escaped:
            raise ValueError(f'{when_escaped} or {bucket_escaped} or {path_escaped} has "|" in it')
        file_name = f"|{when_escaped}|{bucket_escaped}|{path_escaped}"
        fo = io.BytesIO(bytes(what, encoding="utf-8"))

        upload_to = f"{self._path}/{file_name}"
        self._s3_client.upload_fileobj(fo, self._bucket, upload_to)
        info(f"Scheduled on {what} to copy {path}")
        return upload_to

    def stop(self, key: Any) -> bool:
        """
        Stop a scheduled task donated by 'key'. Return True on success, false otherwise
        """
        # noinspection PyBroadException
        try:
            result: dict = self._s3_client.delete_object(Bucket=self._bucket, Key=key)
            info(f"Deleted a scheduled task {key}.")
            return result["ResponseMetadata"]["HTTPStatusCode"] in [204, 200]
        except Exception as ex:
            warn(f"Unable to delete key in scheduler - {ex}")
            return False

    def handle(self,):
        # Get a list of all files in an s3 path
        bucket = self._s3_resource.Bucket(self._bucket)

        # check if time has passed, if it did then copy the file to the relevant bucket
        requires_handling = []

        for obj in bucket.objects.filter(Prefix=self._path):
            if self._time_passed(obj.key):
                # noinspection PyBroadException
                try:
                    requires_handling.append(self._extract_location(obj.key))
                except Exception as ex:
                    warn(f"{obj} has invalid structure, ignoring scheduled task. {ex}")

        for source_file, target_bucket, target_path in requires_handling:
            # noinspection PyBroadException
            try:
                move_file(self._bucket, target_bucket, source_file, self._s3_client, target_path)
            except Exception as ex:
                warn(f"Unable to copy {source_file} to {bucket}/{target_path}. {ex}")

    def _time_passed(self, key: str) -> bool:
        elements = key.split("|")
        if len(elements) != 4:
            warn(f"{key} has invalid structure, ignoring scheduled task")
            return False

        try:
            time = date_parser(parse.unquote(elements[1]))
            return nowut() > time
        except ValueError:
            warn(f"{key} has invalid structure, ignoring scheduled task")
            return False

    def _extract_location(self, key: str) -> Tuple[str, str, str]:
        """
        Extract the components from the key's name
        :param key: Key to extract from
        :return: A tuple of original's key name, target  buck, target path
        """
        elements = key.split("|")

        bucket = parse.unquote(elements[2])
        target_path = parse.unquote(elements[3]).replace("~~", "/")

        return key, bucket, target_path
