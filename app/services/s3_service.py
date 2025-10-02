import boto3
import os
from botocore.exceptions import NoCredentialsError

def upload_file_to_s3(file, bucket_name, object_name=None):
    """
    Upload a file to an S3 bucket

    :param file: File to upload
    :param bucket_name: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    if object_name is None:
        object_name = file.filename

    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )
    try:
        s3_client.upload_fileobj(file, bucket_name, object_name)
        return f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
    except NoCredentialsError:
        return None
