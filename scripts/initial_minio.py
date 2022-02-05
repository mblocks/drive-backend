from minio import Minio
from minio.notificationconfig import NotificationConfig, QueueConfig, PrefixFilterRule
from app.config import get_settings


def main() -> None:
    settings = get_settings()
    minio_client = Minio(settings.SERVICES_MINIO_HOST,
                         access_key=settings.SERVICES_MINIO_ACCESS_KEY,
                         secret_key=settings.SERVICES_MINIO_SECRET_KEY,
                         secure=False,
                         region='mblocks'
                         )
    if not minio_client.bucket_exists(settings.SERVICES_MINIO_BUCKET):
        minio_client.make_bucket(settings.SERVICES_MINIO_BUCKET)

    minio_client.set_bucket_notification(settings.SERVICES_MINIO_BUCKET, NotificationConfig(
        queue_config_list=[
            QueueConfig(
                'QUEUE-ARN-{}'.format(settings.SERVICES_MINIO_BUCKET.upper()),  # nopep8
                ["s3:ObjectCreated:*"],
                config_id=settings.SERVICES_MINIO_BUCKET,
                prefix_filter_rule=PrefixFilterRule("home"),
            ),
        ],
    ))


if __name__ == "__main__":
    main()
