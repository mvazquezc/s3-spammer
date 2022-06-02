from importlib.metadata import files
import os
import time
import argparse
from concurrent.futures.thread import ThreadPoolExecutor
from lib.utils import *

parser = argparse.ArgumentParser(description='Spam an S3 bucket.')
parser.add_argument('-f', '--files', type=int, help='The number of files that will be created in the bucket.', required=True)
parser.add_argument('-w', '--wait-time', type=int, help='Number of seconds to wait between executions.', required=True)
parser.add_argument('-s', '--file-size', type=int, help='Size (in MiB) for the generated files.', required=True)
parser.add_argument('-b', '--bucket-name', type=str, help='Name of the bucket where files will be pushed.', required=True)
parser.add_argument('-p', '--bucket-path', type=str, help='Path within the bucket where files will be pushed.', required=False)

args = parser.parse_args()

logging = Logger("s3-spammer", "INFO")
logger = logging.new_logger()

number_of_files = args.files
wait_time = args.wait_time
file_size=str(args.file_size) + 'M'
bucket_name=args.bucket_name
bucket_path=args.bucket_path


logger.info("Spammer config. Number of files: %s, Wait time: %s, File size: %s, Bucket name: %s, Bucket path: %s", number_of_files, wait_time, file_size, bucket_name, bucket_path)

s3_client = S3()

file_names = []
for file_number in range(number_of_files):
    file_name = "test" + "-" + str(file_number)
    file_names.append(file_name)

while(True):
    with ThreadPoolExecutor(max_workers=number_of_files) as executor:
        for file_name in file_names:
            executor.submit(gen_file_on_s3, file_name, file_size, s3_client, bucket_name, bucket_path, logger)
    logger.info("Sleeping for %s seconds...", wait_time)
    time.sleep(wait_time)