import boto3
import os
import logging
import re
import time

def generate_file(filename, size, logger):
    if not re.match(r"^([0-9].*)([A-Z])", str(size)):
        logger.error("Bad size received: %s, setting size to 1M", size)
        size = "1M"
    unit = re.search(r"^([0-9].*)([A-Z])", str(size))
    size = unit.group(1)
    unit = unit.group(2)
    logger.debug("Size: %s, Unit: %s", size, unit)
    if unit == "K":
        byte_size = int(size) * 1024
    elif unit == "M":
        byte_size = int(size) * 1024 * 1024
    elif unit == "G":
        byte_size = int(size) * 1024 * 1024 * 1024
    else:
        unit = "B"
    
    with open('%s'%filename, 'wb') as generated_file:
        try:
            generated_file.write(os.urandom(int(byte_size)))
            logger.debug("Wrote %s%s to file %s", size, unit, filename)
        except Exception as e:
            logger.error(e)

def gen_file_on_s3(filename, file_size, s3_client, bucket_name, bucket_path, logger):
    generate_file(filename, file_size, logger)
    object_name = str(int(time.time())) + '-' + filename
    logger.info("Pushing %s to bucket %s into %s folder", object_name, bucket_name, bucket_path)
    s3_client.upload(bucket_name, filename, object_name, bucket_path)

def gen_file_on_disk(filename, file_size, file_path, logger):
    file_name = str(int(time.time())) + '-' + filename
    file_destination = file_path + file_name
    generate_file(file_destination, file_size, logger)
    logger.info("Creating %s into %s folder", file_name, file_path)

class Logger():
    def __init__(self, logger_name, logger_level):
        self.logger = logging.getLogger(logger_name)
        
        ch = logging.StreamHandler()
        if logger_level == "DEBUG":            
            self.logger.setLevel(logging.DEBUG)    
        elif logger_level == "ERROR":
            self.logger.setLevel(logging.ERROR)
        else:
            self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s]: %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
    def new_logger(self):
        return self.logger

class S3:

    def __init__(self):
        logging = Logger("utils_lib_s3", "DEBUG")
        self.logger = logging.new_logger()
        if "S3_ACCESS_KEY" not in os.environ or "S3_SECRET_KEY" not in os.environ:
            self.logger.error("S3_ACCESS_KEY or S3_SECRET_KEY env var not set, exiting...")
            exit(1)
        else:        
            s3_access_key = os.environ['S3_ACCESS_KEY']
            s3_secret_key = os.environ['S3_SECRET_KEY']
        if "S3_ENDPOINT" in os.environ:
            s3_endpoint = os.environ['S3_ENDPOINT']
        else:
            s3_endpoint = None

        if s3_endpoint is not None:
            verify_ssl=True
            if "S3_NO_VERIFY_SSL" in os.environ:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                verify_ssl=False
            try:
                self.client = boto3.client('s3', endpoint_url=s3_endpoint, verify=verify_ssl, aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key)
            except Exception as e:
                self.logger.error(e)
        else:
            try:
                self.client = boto3.client('s3', aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key)
            except Exception as e:
                self.logger.error(e)
        
    def upload(self, s3_bucket, file_object, object_name, folder=None):
        if folder is not None:
            object_name = folder + '/' + object_name
        try:
            self.client.upload_file(str(file_object), s3_bucket, object_name)
        except Exception as e:
            self.logger.error(e)

    def download(self, s3_bucket, s3_file_path, output_file_path):
        try:
            self.client.download_file(s3_bucket, s3_file_path, output_file_path)
        except Exception as e:
            self.logger.error(e)

    def delete_object(self, s3_bucket, s3_file_path):
        try:
            self.client.delete_object(Bucket=s3_bucket, Key=s3_file_path)
        except:
            self.logger.error(e)

    def list_bucket_content(self, s3_bucket, s3_path=None, s3_filter=None):
        keys = []
        if s3_path is not None:
            kwargs = {'Bucket': s3_bucket, 'Prefix': s3_path}
        else:
            kwargs = {'Bucket': s3_bucket}
        while True:
            try:
                resp = self.client.list_objects_v2(**kwargs)
                if resp['ResponseMetadata']['HTTPStatusCode'] == 200 and resp['KeyCount'] != 0:           
                    try:
                        for obj in resp['Contents']:
                            keys.append(obj['Key'])
                    except KeyError:
                        self.logger.error("Error while listing bucket content")
                        exit(1)
                    try:
                        kwargs['ContinuationToken'] = resp['NextContinuationToken']
                    except KeyError:
                        break
                elif resp['ResponseMetadata']['HTTPStatusCode'] != 200:
                    self.logger.error("Error while listing bucket content. Make sure S3 Bucket and Path are correct")
                    exit(1)
                else:
                    self.logger.warning("Buket is empty")
                    break
            except self.client.exceptions.NoSuchBucket:
                self.logger.error("Bucket %s does not exist", s3_bucket)
                exit(1)
        if s3_filter is not None and len(keys) > 0:
            for entry in keys[:]:
                if not (entry.endswith(s3_filter)):
                    keys.remove(entry)
        return keys

"""     def download_images_from_bucket(self, s3_bucket, output_folder, folder=None):
        # Create a list with only .jpg images present on s3 bucket     
        images = self.list_bucket_content(s3_bucket, folder, ".jpg")
        if len(images) > 0:
            for s3_image_path in images:
                image_path, image_filename = os.path.split(s3_image_path)
                output_file_path = os.path.join(output_folder, image_filename)
                if os.path.isfile(output_file_path):
                   self.logger.debug("Image %s already downloaded", output_file_path)
                else:
                    # Create output folder if it does not exist
                    if not (os.path.isdir(output_folder)):
                        self.logger.info("Folder %s does not exist, creating it for the first time...", output_folder)
                        os.makedirs(output_folder)
                    self.download(s3_bucket, s3_image_path, output_file_path)
                    self.logger.debug("Image %s downloaded to %s", s3_image_path, output_file_path)
        return images """
