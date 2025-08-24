import boto3
import yaml
import os
from aws_logger import setup_logger

logger = setup_logger('aws_helpers')

class AWSHelper:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        print(config_path)
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['aws']

        self.s3 = boto3.client('s3', region_name=self.config['region'])
        self.sqs = boto3.client('sqs', region_name=self.config['region'])
        self.queue_url = self._get_queue_url()

    def _get_queue_url(self):
        try:
            response = self.sqs.get_queue_url(QueueName=self.config['sqs']['queue_name'])
            return response['QueueUrl']
        except Exception as e:
            logger.error(f"Error getting queue URL: {str(e)}")
            raise

    def receive_messages(self):
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=self.config['sqs']['max_messages'],
                WaitTimeSeconds=self.config['sqs']['wait_time']
            )
            return response.get('Messages', [])
        except Exception as e:
            logger.error(f"Error receiving messages: {str(e)}")
            return []

    def delete_message(self, receipt_handle):
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            return False

    def move_file(self, file_key, source_folder, dest_folder):
        try:
            source = f"{self.config['s3']['folders'][source_folder]}{file_key}"
            destination = f"{self.config['s3']['folders'][dest_folder]}{file_key}"
            
            # Copy the object
            self.s3.copy_object(
                Bucket=self.config['s3']['bucket_name'],
                CopySource={'Bucket': self.config['s3']['bucket_name'], 'Key': source},
                Key=destination
            )
            
            # Delete the original
            self.s3.delete_object(
                Bucket=self.config['s3']['bucket_name'],
                Key=source
            )
            
            return True
        except Exception as e:
            logger.error(f"Error moving file {file_key}: {str(e)}")
            return False

    def download_file(self, file_key, local_path):
        try:
            self.s3.download_file(
                self.config['s3']['bucket_name'],
                f"{self.config['s3']['folders']['input']}{file_key}",
                local_path
            )
            return True
        except Exception as e:
            logger.error(f"Error downloading file {file_key}: {str(e)}")
            return False

    def upload_file(self, local_path, file_key, destination_folder):
        try:
            destination = f"{self.config['s3']['folders'][destination_folder]}{file_key}"
            self.s3.upload_file(
                local_path,
                self.config['s3']['bucket_name'],
                destination
            )
            return True
        except Exception as e:
            logger.error(f"Error uploading file {file_key}: {str(e)}")
            return False


