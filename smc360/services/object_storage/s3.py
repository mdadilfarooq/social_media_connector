"""
The `s3` module provides a `connection` class which has a simple interface to work with an object storage service using Amazon S3.

The connection is established using a configuration dictionary which should include the following keys:
- `service_name (str)`: The name of the object storage service to use
- `endpoint_url (str)`: The endpoint URL for the object storage service.
- `aws_access_key_id (str)`: The access key for the object storage service.
- `aws_secret_access_key (str)`: The secret key for the object storage service.
- `bucket_name (str)`: The name of the bucket to work with.

Example
----
`object_storage`:
    service_name: s3
    endpoint_url: my-endpoint-url
    aws_access_key_id: my-aws-access-key-id
    aws_secret_access_key: my-aws-secret-access-key
    bucket_name: my-bucket-name

Classes
----
    - `credentials`: A class that populates credentials
    - `connection`: A class for establishing a connection to an object storage service and performing operations on it.
"""

import os, json, boto3, logging

logger = logging.getLogger(__name__)

class credentials:
    def __init__(self):
        env = os.getenv('object_storage')
        cred = json.loads(env) if env is not None else {}
        self.endpoint_url = "http://" + cred.get('endpoint_url') if cred.get('endpoint_url') is not None else None
        self.aws_access_key_id = cred.get('aws_access_key_id')
        self.aws_secret_access_key = cred.get('aws_secret_access_key')
        self.bucket_name = cred.get('bucket_name')
        self.s3 = boto3.resource('s3', endpoint_url=self.endpoint_url, aws_access_key_id=self.aws_access_key_id, aws_secret_access_key=self.aws_secret_access_key)

class connection(credentials):
    """
    A class for establishing a connection to an object storage service and performing operations on it.

    Methods
    ----
        - `read_file(file_name, bucket_name)`: This method reads a file from the object storage service.
        - `add_file(file_name, file_contents, bucket_name)`: This method writes a file to the object storage service.
        - `get_objects(folder_name, bucket_name)`: This method gets a list of objects in a folder in the object storage service.
    """

    def __init__(self):
        super().__init__()

    def read_file(self, file_name):
        """
        Reads a file from the object storage service.
        
        Args
        ----
            - `file_name (str)`: The name of the file to read.
            - `bucket_name (str, optional)`: The name of the bucket to read the file from.
        
        Returns
        ----
            The contents of the file as a string, or the parsed JSON/YAML data if the file is in one of those formats.
        """

        try:
            obj = self.s3.Object(self.bucket_name, file_name)
            file_contents = obj.get()['Body'].read().decode('utf-8')
            return file_contents
        except:
            raise
    
    def add_file(self, file_name, file_contents):
        """
        Writes a file to the object storage service.
        
        Args
        ----
            - `file_name (str)`: The name of the file to write.
            - `file_contents (str)`: The contents of the file to write.
            - `bucket_name (str, optional)`: The name of the bucket to write the file to.
        """

        try:
            obj = self.s3.Object(self.bucket_name, file_name)
            obj.put(Body=file_contents)
        except:
            raise

    def get_objects(self, folder_name=''):
        """
        Get a list of objects in a folder in the object storage service.

        Args
        ----
            - `folder_name (str, optional)`: The name of the folder to list objects for. If omitted, all objects in the bucket will be listed.
            - `bucket_name (str, optional)`: The name of the bucket to list objects from.

        Returns
        ----
            A list of object paths in the specified folder of the specified S3 bucket.
        """

        try:
            files = self.s3.Bucket(self.bucket_name).objects.filter(Prefix=folder_name)
            paths = [file.key for file in files]
            return paths
        except:
            raise