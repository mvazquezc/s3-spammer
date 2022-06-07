from importlib.metadata import files
import os
import time
import argparse
from concurrent.futures.thread import ThreadPoolExecutor
from lib.utils import *

parser = argparse.ArgumentParser(description='Spam files to folder')
parser.add_argument('-f', '--files', type=int, help='The number of files that will be created in the folder.', required=True)
parser.add_argument('-m', '--max-workers', type=int, help='The number of concurrent threads that will run. If not set, concurrent threads will equal number of files', required=False)
parser.add_argument('-w', '--wait-time', type=int, help='Number of seconds to wait between executions.', required=True)
parser.add_argument('-s', '--file-size', type=str, help='Size for the generated files. It supports the size+units format (Defaults to M). e.g: 100M|10K|1G', required=True)
parser.add_argument('-p', '--file-path', type=str, help='Path where the files will be created.', required=True)

args = parser.parse_args()

logging = Logger("block-spammer", "INFO")
logger = logging.new_logger()

number_of_files = args.files
wait_time = args.wait_time
file_size = str(args.file_size)
file_path = args.file_path
num_workers = args.max_workers

if num_workers is None or num_workers > number_of_files:
    num_workers = number_of_files

logger.info("Spammer config. Number of files: %s, Workers: %s, Wait time: %s, File size: %s, File path: %s", number_of_files, num_workers, wait_time, file_size, file_path)

file_names = []
for file_number in range(number_of_files):
    file_name = "test" + "-" + str(file_number)
    file_names.append(file_name)

while(True):
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for file_name in file_names:
            executor.submit(gen_file_on_disk, file_name, file_size, file_path, logger)
    
    logger.info("Sleeping for %s seconds...", wait_time)
    time.sleep(wait_time)
