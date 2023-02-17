import requests
import os
import configparser
import json
import time
import polyline
import mariadb
import sys

import database_export as dbe
# import strava_connector as sc
import strava_import_handler as sih

# query Strava API with access token directly
# http_header = {'Authorization': 'Bearer d623a206053610f20ba7c43f17794d38a8674ce8'}
# http_response = requests.get('https://www.strava.com/api/v3/athlete', headers=http_header)

auth_path = os.path.join(os.curdir, '.stravatokens', 'auth.cfg')
# client_path = os.path.join(os.curdir, '.stravatokens', 'client.cfg')
# dbconfig_path = os.path.join(os.curdir, '.dbconfig', 'db.cfg')
config_path = os.path.join(os.curdir, '.appconf', 'strava_activity_extractor.cfg')

# authorization_url = 'http://www.strava.com/oauth/authorize'
# # TODO: is it https://www.strava.com/api/v3/oauth/token?
# token_url = 'https://www.strava.com/oauth/token'
# athlete_url = 'https://www.strava.com/api/v3/athlete'
# activities_url = 'https://www.strava.com/api/v3/athlete/activities'
# detailed_activity_url = 'https://www.strava.com/api/v3/activities/' # needs {id}/ at the end

# first run probably needs actual client authentication
# http://www.strava.com/oauth/authorize?client_id=76303&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read_all,profile:read_all,activity:read_all

# create config
appconf = configparser.ConfigParser()


# auth_config = configparser.ConfigParser()

# create client.cfg
# client_config = configparser.ConfigParser()

# create modules
db = dbe.DatabaseExport()
# strava = sc.StravaConnector(authconfigpath=auth_path)


# load db.cfg
if os.path.exists(config_path):
    appconf.read(config_path, encoding='utf-8')
else:
    appconf['MariaDB'] = {}
    appconf['MariaDB']['host'] = 'ENTER DATABASE URL HERE'
    appconf['MariaDB']['port'] = '3306'
    appconf['MariaDB']['name'] = 'ENTER DATABASE NAME HERE'
    appconf['MariaDB']['user'] = 'ENTER DATABASE USER HERE'
    appconf['MariaDB']['password'] = 'ENTER DATABASE USER PASSWORD HERE'

    if not os.path.exists(os.path.dirname(config_path)):
        os.mkdir(os.path.dirname(config_path))
    with open(config_path, 'w') as f:
        appconf.write(f)

# load client.cfg
    appconf['Strava'] = {}
    appconf['Strava']['client_id'] = 'ENTER CLIENT ID HERE'
    appconf['Strava']['client_secret'] = 'ENTER CLIENT SECRET HERE'
    appconf['Strava']['client_code'] = 'ENTER CLIENT CODE FROM OAUTH REDIRECT HERE'
    appconf['Strava']['scope'] = 'read_all,profile:read_all,activity:read_all'

    with open(config_path, 'w') as f:
        appconf.write(f)

# authentication handled in subclass
# TODO: redefine redirect uri
strava_import = sih.StravaImportHandler(stravaconfigpath=auth_path, 
                                        clientid=appconf['Strava']['client_id'],
                                        clientsecret=appconf['Strava']['client_secret'],
                                        clientscope=appconf['Strava']['scope'],
                                        redirecturi='http://localhost/exchange_token')
strava_import.authenticate()

# establish database connection
dbconn : mariadb.Connection = None
try:
    dbconn = mariadb.connect(user=appconf['MariaDB']['user'],
                             password=appconf['MariaDB']['password'],
                             host=appconf['MariaDB']['host'],
                             port=int(appconf['MariaDB']['port']),
                             database=appconf['MariaDB']['name'])
except mariadb.Error:
    # log.exception(f"Error connecting to MariaDB instance {dbconn.database} @ {dbconn.server_name}!")
    sys.exit(500)
# log.info(f"Load modules; MariaDB connection initialized. Database name: {dbconn.database} @ {dbconn.server_name}.")

# db.update_connection(dbconn)
strava_import.update_db_connection(dbconn)

# make athlete request
# data = strava_import.get_athlete_data()
# print(f"Athlete username: {data['username']}")

# make activities request
data = strava_import.get_athlete_activity_batch(7)

for act in data:
    print(f"ActivityName: {act['name']:120}; ActivityId: {act['id']:12}; Timestamp: {act['start_date']}")

data = strava_import.get_detailed_activity(8330295632)

dbconn.commit()

# close db connection
dbconn.close()