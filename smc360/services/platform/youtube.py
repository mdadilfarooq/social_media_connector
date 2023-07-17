"""
The `youtube` module uses the apiclient library to connect to the YouTube API and retrieve data. Later this raw data is parsed to extract relevant fields.

The connection is established using a configuration dictionary which should include the following keys:
- `service_name (str)`: The name of the platform service to use
- `key (str)`: The developer key to use for the API connection

Example
----
`platform`:
    service_name: youtube
    key: my-key

Classes
----
    - `load_to_object_storage`: A class for retrieving YouTube data and loading it to object storage.
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
        self.youtube = 'https://www.googleapis.com/youtube/v3/'

class load_to_object_storage(credentials):
    """
    A class that loads data from YouTube API and stores it in an object storage.

    Args
    ----
        - `object_storage (object)`: An object storage connection object.
        - `get_comments (bool, optional)`: Whether to retrieve comments for videos. Defaults to False.
        - `follow_up_on_search (bool, optional)`: Whether to follow up on related resources. Defaults to False.
        - `default_limit (int, optional)`: Default maximum number of results. Defaults to 5000.

    Attributes
    ----
        - `object_storage (object)`: An object storage connection object.
        - `get_comments (bool)`: Whether to retrieve comments for videos.
        - `follow_up_on_search (bool)`: Whether to follow up on related resources.
        - `default_limit (int)`: Default maximum number of results.
        - `__file_path (str)`: The path where data is stored.
        - `__supported_resources (dict)`: A dictionary of supported YouTube resources.

    Methods
    ----
        - `__followUp(resources)`: A helper method that retrieves downstream resources for a given resource.
        - `channels(parameters)`: Retrieves channels data from the YouTube API and stores it in object storage.
        - `playlists(parameters)`: Retrieves playlists data from the YouTube API and stores it in object storage.
        - `playlistItems(parameters)`: Retrieves playlistItems data from the YouTube API and stores it in object storage.
        - `videos(parameters)`: Retrieves videos data from the YouTube API and stores it in object storage.
        - `comments(parameters)`: Retrieves comments data from the YouTube API and stores it in object storage.
        - `search(parameters)`: Retrieves resources based on a search query and their associated metadata.
    """

    def __init__(self, object_storage):
        """
        Initializes an instance of load_to_object_storage class.

        Args
        ----
            - `object_storage (object)`: An object storage connection object.
            - `get_comments (bool, optional)`: Whether to retrieve comments for videos. Defaults to False.
            - `follow_up_on_search (bool, optional)`: Whether to follow up on related resources. Defaults to False.
            - `default_limit (int, optional)`: Default maximum number of results. Defaults to 5000.
        """

        super().__init__()
        self.object_storage = object_storage.connection()
        self.get_comments = False
        self.follow_up_on_search = False
        self.default_limit = 5000
        self.__file_path = f'youtube/{timestamp}'
        self.__supported_resources = {
            'youtube#video': {
                'method': 'videos',
                'id': lambda resource: resource['videoId']
            },
            'youtube#channel': {
                'method': 'channels',
                'id': lambda resource: resource['channelId']
            },
            'youtube#playlists': {
                'method': 'playlists',
                'id': lambda resource: resource['playlistId']
            }
        }

    def __followUp(self, resources):
        """
        A private method that follows up on related resources.

        Args
        ----
            - `resources (list)`: A list of dicts, where each dict contains resource kind and resource id.
        """

        values_dict = {}
        for key, value in self.__supported_resources.items():
            values_list = [value['id'](resource) for resource in resources if resource['kind'] == key]
            values_dict[value['method']] = values_list

        for method_name, values in values_dict.items():
            for i in range(0, len(values), 50):
                batch_values = values[i:i+50]
                values_str = ','.join(batch_values)
                method_to_call = getattr(self, method_name)
                method_to_call({'id': values_str})

    def __apiCall(func):
        def wrapper(self, parameters, *args, **kwargs):
            func(self, parameters)
            defaults = {
                'key': self.key,
                'maxResults': 50,
                'pageToken': ''
            }
            follow_up = []
            max_results = self.default_limit
            parameters.update(defaults)
            action_dict = {
                'channels':      {'follow_up_func': self.playlists, 'type_of_follow_up_id': 'id',
                                  'resource_func': lambda item: item['contentDetails']['relatedPlaylists']['uploads']},
                'playlists':     {'follow_up_func': self.playlistItems, 'type_of_follow_up_id': 'playlistId',
                                  'resource_func': lambda item: item['id']},
                'videos':        {'follow_up_func': self.comments, 'type_of_follow_up_id': 'videoId',
                                  'resource_func': lambda item: item['id']},
                'search':        {'follow_up_func': self.__followUp if self.follow_up_on_search is True else None,
                                  'resource_func': lambda item: item['id'] if item['id']['kind'] in self.__supported_resources.keys() else None},
                'playlistItems': {'follow_up_func': self.__followUp,
                                  'resource_func': lambda item: item['snippet']['resourceId'] if item['snippet']['resourceId']['kind'] in self.__supported_resources.keys() else None},
            }
            while parameters['pageToken'] is not None and max_results > 0:
                max_results -= parameters.get('maxResults', 50)
                try:
                    response = requests.get(self.youtube+func.__name__, params=parameters)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.error(str(e))
                    break
                data = response.json()
                for item in data['items']:
                    try:
                        json_string = json.dumps(item)
                        self.object_storage.add_file(f"{self.__file_path}/{func.__name__}/{item['id'] if isinstance(item['id'], str) else item['etag']}.json", json_string)
                    except Exception as e:
                        logger.error(str(e))
                    resource_func = action_dict[func.__name__]['resource_func']
                    resource = resource_func(item)
                    if resource is not None:
                        follow_up.append(resource)
                parameters['pageToken'] = data.get('nextPageToken')
            follow_up_func = action_dict[func.__name__]['follow_up_func']
            if func.__name__ in ['search', 'playlistItems'] and follow_up_func is not None:
                follow_up_func(follow_up)
            elif func.__name__ in ['channels', 'playlists', 'videos'] and follow_up_func is not None:
                [follow_up_func({action_dict[func.__name__]['type_of_follow_up_id']: resource}) for resource in follow_up]
        return wrapper

    @__apiCall
    def search(self,parameters):
        """
        Retrieves searchResults and their associated metadata.

        Args
        ----
            - `parameters (dict)`: A dictionary of parameters for the API request.
        """

        parameters['part'] = 'snippet'
        
    @__apiCall
    def channels(self, parameters):
        """
        Retrieves channels and their associated metadata.

        Args
        ----
            - `parameters (dict)`: A dictionary of parameters for the API request.
        """

        parameters['part'] = 'brandingSettings,contentDetails,contentOwnerDetails,id,localizations,snippet,statistics,status,topicDetails'
        
    @__apiCall
    def playlists(self, parameters):
        """
        Retrieves playlists and their associated metadata.

        Args
        ----
            - `parameters (dict)`: A dictionary of parameters for the API request.
        """

        parameters['part'] = 'contentDetails,id,localizations,player,snippet,status'

    @__apiCall
    def playlistItems(self, parameters):
        """
        Retrieves playlistItems and their associated metadata.

        Args
        ----
            - `parameters (dict)`: A dictionary of parameters for the API request.
        """

        parameters['part'] = 'contentDetails,id,snippet,status'

    @__apiCall
    def videos(self, parameters):
        """
        Retrieves videos and their associated metadata.

        Args
        ----
            - `parameters (dict)`: A dictionary of parameters for the API request.
        """

        parameters['part'] = 'contentDetails,id,liveStreamingDetails,localizations,player,recordingDetails,snippet,statistics,status,topicDetails'

    def comments(self, parameters):
        """
        Retrieves comments and their associated metadata.

        Args
        ----
            - `parameters (dict)`: A dictionary of parameters for the API request.
        """

        if self.get_comments:
            defaults = {
                'part': 'id,snippet',
                'maxResults': 100,
                'pageToken': '',
                'key': self.key
            }
            maxResults = self.default_limit
            parameters.update(defaults)
            while parameters['pageToken'] is not None and maxResults > 0:
                maxResults -= parameters['maxResults']
                try:
                    response = requests.get(self.youtube+'commentThreads', params=parameters)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.error(str(e))
                    break
                comment_data = response.json()
                for comment_item in comment_data['items']:
                    comment_item = comment_item['snippet']
                    comment = comment_item.pop('topLevelComment')
                    try:
                        json_string = json.dumps(comment)
                        self.object_storage.add_file(f"{self.__file_path}/comments/{comment['id']}.json", json_string)
                    except Exception as e:
                        logger.error(str(e))
                    for key, value in comment_item.items():
                        comment[key] = value
                    if comment['totalReplyCount'] > 0:
                        reply_parameters = {
                            'parentId': comment['id']
                        }
                        reply_parameters.update(defaults)
                        while reply_parameters['pageToken'] is not None:
                            try:
                                response = requests.get(self.youtube+'comments', params=reply_parameters)
                                response.raise_for_status()
                            except requests.exceptions.RequestException as e:
                                logger.error(str(e))
                                break
                            reply_data = response.json()
                            for reply in reply_data['items']:
                                try:
                                    json_string = json.dumps(reply)
                                    self.object_storage.add_file(f"{self.__file_path}/comments/{reply['id']}.json", json_string)
                                except Exception as e:
                                    logger.error(str(e))
                            reply_parameters['pageToken'] = reply_data.get('nextPageToken')
                parameters['pageToken'] = comment_data.get('nextPageToken')

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
        self.__file_path = f'youtube/{self.timestamp}'

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
    
    channels = videos = playlists = comments = read_parse_load