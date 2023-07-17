from test import test_instagram, test_postgresql, test_s3, test_snowflake, test_youtube

# Run test on instagram module
test_instagram.test_credentials_class()
test_instagram.test_media_method()
test_instagram.test_users_method()

# Run test on postgresql module
test_postgresql.test_add_records()
test_postgresql.test_create_or_update_table()
test_postgresql.test_credentials_class()

# Run test on s3 module
test_s3.test_add_file()
test_s3.test_read_file()
test_s3.test_get_objects()
test_s3.test_credentials_class()

# Run test on snowflake module
test_snowflake.test_add_records()
test_snowflake.test_create_or_update_table()
test_snowflake.test_credentials_class()

# Run test on youtube module
test_youtube.test_credentials_class()
