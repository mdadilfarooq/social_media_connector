Social Media Parser
----

This program extracts data from social media platforms and stores parsed data in a database and raw response in object storage.

The program supports the following services:
- `Platform: YouTube(Youtube Data API), Instagram(Basic Display API)`
- `Database: PostgreSQL, Snowflake`
- `Object Storage: s3`

Usage
----

The program will use the configuration data to connect to the social media platform, database, and object storage service. 
It will then load additional configuration data from the object storage service, parse the social media data, and store it in the database.

Installation: `pip install "git+https://github.com/BLEND360/COE_Socialmedia_Parser.git@dev"`
