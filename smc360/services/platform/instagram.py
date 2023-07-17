"""
The `instagram` module uses the request library to connect to the Instagram Basic Display API and retrieve data. Later this raw data is parsed to extract relevant fields.

The connection is established using a configuration dictionary which should include the following keys:
- `service_name (str)`: The name of the platform service to use
- `key (str)`: The access token to use for the API connection

Example
----
`platform`:
    service_name: instagram
    key: my-key

Classes
----
    - `load_to_object_storage`: A class for retrieving Instagram data and loading it to object storage.
    - `load_to_database`: A class for parsing data and loading to database.
"""

import os, json, requests, logging
from functools import reduce

logger = logging.getLogger(__name__)
timestamp = os.getenv('timestamp')

class credentials:
    def __init__(self):
        env = os.getenv('platform')
        cred = json.loads(env) if env is not None else {}
        self.key = cred.get('key')
        self.instagram = "https://graph.instagram.com/v16.0/"

class load_to_object_storage(credentials):
    """
    A class that loads data from Instagram API and stores it in an object storage.

    Args
    ----
        - `object_storage (object)`: An object storage connection object.
        - `default_limit (int, optional)`: Default maximum number of results. Defaults to 5000.

    Attributes
    ----
        - `object_storage (object)`: An object storage connection object.
        - `default_limit (int)`: Default maximum number of results.
        - `__file_path (str)`: The path where data is stored.

    Methods
    ----
        - `user(parameters)`: Retrieve Instagram user data and store it in object storage.
        - `media(parameters)`: Retrieve Instagram media data and store it in object storage.
    """

    def __init__(self, object_storage):
        """
        Initializes an instance of load_to_object_storage class.

        Args
        ----
            - `object_storage (object)`: An object storage connection object.
        """

        super().__init__()
        self.object_storage = object_storage.connection()
        self.default_limit = 5000
        self.__file_path = f'instagram/{timestamp}'
    
    def users(self, parameters):
        """
        Retrieve Instagram user data and store it in object storage.

        Args
        ----
            - `parameters (dict)`: A dictionary containing query parameters for the Instagram API.
        """

        defaults = {
            'fields': 'account_type,id,media_count,username',
            'access_token': self.key
        }
        try:
            response = requests.get(self.instagram+"me",params=defaults)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(str(e))
            return
        data = response.json()
        user_id = data.get('id')
        json_string = json.dumps(data)
        self.object_storage.add_file(f"{self.__file_path}/users/{user_id}.json", json_string)

    def media(self, parameters):
        """
        Retrieve Instagram media data and store it in object storage.

        Args
        ----
            - `parameters (dict)`: A dictionary containing query parameters for the Instagram API.
        """

        defaults = {
            'fields': 'caption,id,is_shared_to_feed,media_type,media_url,permalink,thumbnail_url,timestamp,username,children',
            'access_token': self.key,
            'limit': 100
        }
        maxResults = self.default_limit
        next_url = self.instagram + "me/media"
        while next_url is not None and maxResults > 0:
            maxResults -= defaults['limit']
            try:
                response = requests.get(next_url, params=defaults)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error(str(e))
                break
            data = response.json()
            next_url = data.get('paging', {}).get('next')
            for media in data.get('data'):
                media_id = media.get('id')
                try:
                    json_string = json.dumps(media)
                    self.object_storage.add_file(f"{self.__file_path}/media/{media_id}.json", json_string)
                except Exception as e:
                    logger.error(str(e))
                for child in media.get('children', {}).get('data', []):
                    defaults = {
                        'fields': 'id,is_shared_to_feed,media_type,media_url,permalink,thumbnail_url,timestamp,username,children',
                        'access_token': self.key
                    }
                    try:
                        response = requests.get(self.instagram+str(child.get('id')),params=defaults)
                        response.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        logger.error(str(e))
                        continue
                    data = response.json()
                    media_id = data.get('id')
                    try:
                        json_string = json.dumps(data)
                        self.object_storage.add_file(f"{self.__file_path}/media/{media_id}.json", json_string)
                    except Exception as e:
                        logger.error(str(e))

class load_to_database:
    """
    A class that loads data from bucket, parses it and stores it in a database.

    Args
    ----
        - `database (object)`: A database connection object.
        - `object_storage (object)`: An object storage connection object.
        - `timestamp (str, optional)`: A timestamp for the data to be loaded. Defaults to the current timestamp.

    Attributes
    ----
        - `database (object)`: A database connection object.
        - `object_storage (object)`: An object storage connection object.
        - `timestamp (str)`: A timestamp for the data to be loaded.
        - `__file_path (str)`: The path where data is stored.

    Methods
    ----
        - `read_parse_load(model, table_name)`: Reads data from object storage, parses it and stores it in the database.
    """

    def __init__(self, database, object_storage):
        """
        Initializes an instance of the load_to_database class.

        Args
        ----
            - `database (object)`: A database connection object.
            - `object_storage (object)`: An object storage connection object.
            - `timestamp (str, optional)`: A string indicating the timestamp used for the data file path. Defaults to the current timestamp.
        """

        self.database = database.connection()
        self.object_storage = object_storage.connection()
        self.timestamp = timestamp
        self.__file_path = f'instagram/{self.timestamp}'

    def read_parse_load(self, model, table_name):
        """
        Reads data from object storage, parses it and stores it in the database.

        Args
        ----
            - `model (dict)`: A dictionary indicating the model of the data to be stored in the database.
            - `table_name (str)`: The name of the database table (same as folder name in object storage).
        """

        column_names = list(model.keys())
        paths = self.object_storage.get_objects(f'{self.__file_path}/{table_name}')
        entries = []
        for path in paths:
            try:
                file = json.loads(self.object_storage.read_file(path))
            except Exception as e:
                logger.error(str(e))
            entry = [self.timestamp]
            for keys in model.values():
                entry.append(reduce(lambda d, key: d.get(key, None) if isinstance(d, dict) else None, keys.split("."), file))
            entries.append(tuple(entry))
        with self.database as conn:
            try:
                conn.create_or_update_table(table_name, column_names)
                conn.add_records(table_name, column_names, entries)
            except Exception as e:
                logger.error(str(e))
    
    users = media = read_parse_load