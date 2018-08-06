from datetime import datetime, timezone
from logging import getLogger

logger = getLogger("s3_scheduler")


class UnableToMoveFileError(Exception):
    pass


def nowut() -> datetime:
    """
    Current time with UTC timezone. use it instead of datetime.now()
    """
    return datetime.now(tz=timezone.utc)


def add_utc_tz(to_this: datetime) -> datetime:
    """
    Add timezone of utc to a naive representation of datetime, if time tz already exists then do not change anything
    :param to_this: Add relevant tz to this object.
    :return: Either new datetime if tz was added or the same that was given in param if no tz was added.
    """
    return to_this if to_this.tzinfo else to_this.replace(tzinfo=timezone.utc)


def move_file(source_bucket: str, target_bucket: str, source_file: str, s3_client, target_file: str = None):
    """
    Move a file from one bucket to the other.
    :param source_bucket:  Move a file from this bucket
    :param target_bucket: Move a file to this bucket
    :param source_file: File that exists in ;source_bucket' that you wish to move.
    :param s3_client: A boto S3 client used to interact with AWS api.
    :param target_file: If None then the target file name will be exactly like the source file name.
    """
    if not target_file:
        target_file = source_file
    if source_bucket and source_file and target_bucket:
        s3_client.copy_object(Bucket=target_bucket, CopySource=f"{source_bucket}/{source_file}", Key=target_file)
        s3_client.delete_object(Bucket=source_bucket, Key=source_file)
    else:
        raise UnableToMoveFileError()


def info(msg, *args, **kwargs):
    logger.info(msg, *args, **kwargs)


def warn(msg, *args, **kwargs):
    logger.warning(msg, *args, **kwargs)
