import os, json, datetime
import unittest.mock as mock
from smc360.services.platform.youtube import load_to_object_storage, load_to_database, credentials

dummy_env = {'key': 'test-key'}

def test_credentials_class():
    # Initialise
    os.environ['platform'] = json.dumps(dummy_env)

    # Test class
    cred = credentials()
    assert cred.key == dummy_env.get('key')
    assert cred.youtube == 'https://www.googleapis.com/youtube/v3/'

    del os.environ['platform']
