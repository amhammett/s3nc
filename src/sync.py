import logging
import os

import boto3
import botocore
import yaml

HOME_DIR = os.getenv('HOME')
S3NC_DEFAULT_BUCKET = '{}.s3nc'.format(os.getenv('USER'))
S3NC_CONFIG_PATH = '{}/.s3nc'.format(os.getenv('HOME'))
S3NC_CONFIG_FILE = '{}/registry.yaml'.format(S3NC_CONFIG_PATH)
S3NC_CONFIG = {}

FEATURE_DOWNLOAD = True
FEATURE_UPLOAD = True

logger = logging.getLogger('s3nc')
logger.setLevel(logging.INFO)

logging.basicConfig(filename='{}/sync.log'.format(S3NC_CONFIG_PATH))
logger_stdout = logging.StreamHandler()
logger_stdout.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
logging.getLogger().addHandler(logger_stdout)

if (os.getenv('VERBOSE', False)):
    logger.setLevel(logging.DEBUG)


def sync_s3_to_fs(s3nc_bucket, source, target):
    logger.info('syncing bucket={} src={} dest={}'.format(s3nc_bucket, source, target))

    if (FEATURE_DOWNLOAD):
        if (not os.path.isdir(target)):
            print('target path missing')
            os.makedirs(target)
        try:
            for s3_object in s3nc_bucket.objects.filter(Prefix=source):
                if (s3_object.key == '{}/'.format(source)):
                    continue

                target_path = '{}{}'.format(target, s3_object.key)
                print('downloading {} to {}'.format(s3_object.key, target_path))

                s3nc_bucket.download_file(s3_object.key, target_path)
        except botocore.exceptions.ClientError:
            logger.error('source resource ({}) does not exist'.format(source))


def sync_directory_to_s3(s3nc_bucket, path):
    global S3NC_CONFIG

    for root, dirs, files in os.walk(path):
        for file in files:
            sync_file = True

            for skip in S3NC_CONFIG['skip']:
                if (skip in file):
                    sync_file = False

            if (sync_file):
                sync_fs_to_s3(s3nc_bucket, os.path.join(root, file))


def sync_fs_to_s3(s3nc_bucket, file):
    file_key = file[1:]
    logger.info('syncing bucket={} src={} dest={}'.format(s3nc_bucket, file, file_key))

    if (FEATURE_UPLOAD):
        s3nc_bucket.upload_file(file, file_key)


def s3nc_bucket_exists(s3nc_bucket):
    return s3nc_bucket.creation_date


def read_configuration():
    global S3NC_CONFIG
    with open(S3NC_CONFIG_FILE, 'r') as stream:
        S3NC_CONFIG = yaml.safe_load(stream)

    if('bucket' not in S3NC_CONFIG):
        S3NC_CONFIG['bucket'] = S3NC_DEFAULT_BUCKET

    logger.debug(S3NC_CONFIG)


def main():
    logger.info('s3_sync')
    read_configuration()
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(S3NC_CONFIG['bucket'])

    if(s3nc_bucket_exists(bucket)):
        for line in S3NC_CONFIG['up']:
            sync_entry = line.strip()
            if (os.path.isfile(sync_entry)):
                sync_fs_to_s3(bucket, sync_entry)
            else:
                sync_directory_to_s3(bucket, sync_entry)

        for source, target in S3NC_CONFIG['down'].items():
            sync_s3_to_fs(bucket, source, target)

        logger.info('sync complete')


if __name__ == '__main__':
    main()
