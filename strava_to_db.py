import requests
import os
import configparser
import json
import time
import polyline
import mariadb
import sys

import database_export as dbe
import strava_connector as sc

# query Strava API with access token directly
# http_header = {'Authorization': 'Bearer d623a206053610f20ba7c43f17794d38a8674ce8'}
# http_response = requests.get('https://www.strava.com/api/v3/athlete', headers=http_header)

auth_path = os.path.join(os.curdir, '.stravatokens', 'auth.cfg')
# client_path = os.path.join(os.curdir, '.stravatokens', 'client.cfg')
# dbconfig_path = os.path.join(os.curdir, '.dbconfig', 'db.cfg')
config_path = os.path.join(os.curdir, '.appconf', 'strava_activity_extractor.cfg')

authorization_url = 'http://www.strava.com/oauth/authorize'
# TODO: is it https://www.strava.com/api/v3/oauth/token?
token_url = 'https://www.strava.com/oauth/token'
athlete_url = 'https://www.strava.com/api/v3/athlete'
activities_url = 'https://www.strava.com/api/v3/athlete/activities'
detailed_activity_url = 'https://www.strava.com/api/v3/activities/' # needs {id}/ at the end

# first run probably needs actual client authentication
# http://www.strava.com/oauth/authorize?client_id=76303&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read_all,profile:read_all,activity:read_all

# create config
appconf = configparser.ConfigParser()


auth_config = configparser.ConfigParser()

# create client.cfg
# client_config = configparser.ConfigParser()

# create modules
db = dbe.DatabaseExport()
strava = sc.StravaConnector(authconfigpath=auth_path)

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

# check if auth.cfg already exists from previous authentication
if os.path.exists(auth_path):
    auth_config.read(auth_path, encoding='utf-8')
else:
    # if auth.cfg does not exist yet, create from code
    strava.oauth_get_token_from_code(id=appconf['Strava']['client_id'],
                                     secret=appconf['Strava']['client_secret'],
                                     code=appconf['Strava']['client_code'])

# check if token expired
currepoch = int(time.time())
if currepoch > int(auth_config['Strava']['expires_at'], base=10):
    
    # refresh tokens
    strava.oauth_refresh_access_token(id=appconf['Strava']['client_id'],
                                      secret=appconf['Strava']['client_secret'])

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

db.update_connection(dbconn)

# make athlete request
header = {'Authorization': 'Bearer '+ auth_config['Strava']['access_token']}
response = requests.get(url=athlete_url, headers=header)

print(f"Athlete response error code = {response.status_code}")

if response.status_code == requests.codes.ok:
    athletedata = response.json()

    with open(os.path.join(os.curdir, 'response', 'athlete.json'),'w') as f:
        json.dump(athletedata, fp=f)

# make activities request
print(f"Current epoch: {currepoch}")
params = {#'before': currepoch,
          'after': 0,
          'page': 1,
          'per_page': 3
          }
response = requests.get(url=activities_url, params=params, headers=header)

print(f"Activities response error code = {response.status_code}")

if response.status_code == requests.codes.ok:
    activitydata = response.json()

    with open(os.path.join(os.curdir, 'response', 'activities.json'),'w') as f:
        json.dump(activitydata, fp=f)

    # detailed activities from separate API
    for i in range(10):        

        # request detailed activity
        params = {'include_all_efforts': True}
        urlstring = f"{detailed_activity_url}{activitydata[i]['id']}/"
        response = requests.get(url=urlstring, params=params, headers=header)

        print(f"Detailed activity {activitydata[i]['id']} response error code = {response.status_code}")

        if response.status_code == requests.codes.ok:
            detailedactivitydata = response.json()

            with open(os.path.join(os.curdir, 'response', f'det_activities_{i}.json'),'w') as f:
                json.dump(detailedactivitydata, fp=f)

            # decode detailed polylines
            poly = detailedactivitydata['map']['polyline']
            # convert to lat, lon tuples
            mapdata = polyline.decode(poly)
            print(f"polyline[{i}]: {len(mapdata)}")

            # TODO: verify data completeness or write with NULL

            db.write_detailed_activity_data(responsedata=detailedactivitydata,
                                            polyline=mapdata)

            dbconn.commit()

# close db connection
dbconn.close()

            


