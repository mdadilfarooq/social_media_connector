import os, json
from unittest.mock import MagicMock, call
from smc360.services.database.snowflake import connection, credentials

dummy_env ={'user': 'user', 'password': 'password', 'account': 'account', 'warehouse': 'warehouse', 'database': 'database', 'schema': 'schema'}

def test_create_or_update_table():
    # Create a mock cursor and connection
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Create a mock credentials object
    mock_credentials = credentials()
    mock_credentials.user = "test_user"
    mock_credentials.password = "test_password"
    mock_credentials.account = "test_account"
    mock_credentials.warehouse = "test_warehouse"
    mock_credentials.database = "test_database"
    mock_credentials.schema = "test_schema"

    # Create a mock table name and column names
    table_name = "test_table"
    column_names = ["col1", "col2", "col3"]

    # Create a mock existing columns list
    mock_cursor.fetchall.return_value = [("timestamp",), ("col1",)]

    # Create a mock connection object and call create_or_update_table
    conn = connection()
    conn.conn = mock_conn
    conn.cur = mock_cursor
    conn.create_or_update_table(table_name, column_names)

    # Assert that the mock cursor executed the correct SQL queries
    expected_calls = [
        call(f"CREATE TABLE IF NOT EXISTS {table_name}(timestamp TIMESTAMP,col1 VARCHAR,col2 VARCHAR,col3 VARCHAR);"),
        call(f"DESCRIBE {table_name};"),
        call(f"ALTER TABLE {table_name} ADD COLUMN col1 VARCHAR;"),
        call(f"ALTER TABLE {table_name} ADD COLUMN col2 VARCHAR;"),
        call(f"ALTER TABLE {table_name} ADD COLUMN col3 VARCHAR;")
    ]
    mock_cursor.execute.assert_has_calls(expected_calls)

def test_add_records():
    # Create a mock cursor and connection
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Create a mock credentials object
    mock_credentials = credentials()
    mock_credentials.user = "test_user"
    mock_credentials.password = "test_password"
    mock_credentials.account = "test_account"
    mock_credentials.warehouse = "test_warehouse"
    mock_credentials.database = "test_database"
    mock_credentials.schema = "test_schema"

    # Create a mock table name, column names, and records
    table_name = "test_table"
    column_names = ["col1", "col2", "col3"]
    records = [("2023-05-13 12:00:00", "value1", "value2", "value3"), ("2023-05-13 12:01:00", "value4", "value5", "value6")]

    # Create a mock connection object and call add_records
    conn = connection()
    conn.conn = mock_conn
    conn.cur = mock_cursor
    conn.add_records(table_name, column_names, records)

    # Assert that the mock cursor executed the correct SQL query
    mock_cursor.executemany.assert_called_once_with(f"INSERT INTO {table_name} (timestamp, col1, col2, col3) VALUES (%s, %s, %s, %s);", records)

def test_credentials_class():
    # Initialise
    os.environ['database'] = json.dumps(dummy_env)

    # Test class
    cred = credentials()
    assert cred.user == dummy_env.get('user')
    assert cred.password == dummy_env.get('password')
    assert cred.account == dummy_env.get('account')
    assert cred.warehouse == dummy_env.get('warehouse')
    assert cred.database == dummy_env.get('database')
    assert cred.schema == dummy_env.get('schema')

    del os.environ['database']
