import requests
import os
import configparser
import json
import time
import polyline
import mariadb
import sys

import database_export as dbe

# query Strava API with access token directly
# http_header = {'Authorization': 'Bearer d623a206053610f20ba7c43f17794d38a8674ce8'}
# http_response = requests.get('https://www.strava.com/api/v3/athlete', headers=http_header)

auth_path = os.path.join(os.curdir, '.stravatokens', 'auth.cfg')
client_path = os.path.join(os.curdir, '.stravatokens', 'client.cfg')
dbconfig_path = os.path.join(os.curdir, '.dbconfig', 'db.cfg')

authorization_url = 'http://www.strava.com/oauth/authorize'
# TODO: is it https://www.strava.com/api/v3/oauth/token?
token_url = 'https://www.strava.com/oauth/token'
athlete_url = 'https://www.strava.com/api/v3/athlete'
activities_url = 'https://www.strava.com/api/v3/athlete/activities'
detailed_activity_url = 'https://www.strava.com/api/v3/activities/' # needs {id}/ at the end

# first run probably needs actual client authentication
# http://www.strava.com/oauth/authorize?client_id=76303&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read_all,profile:read_all,activity:read_all

# create auth.cfg
auth_config = configparser.ConfigParser()

# create client.cfg
client_config = configparser.ConfigParser()
# client_config['Strava'] = {}
# client_config['Strava']['client_Id'] = str(client_id)
# client_config['Strava']['client_secret'] = client_secret
# client_config['Strava']['client_code'] = client_code
# client_config['Strava']['scope'] = scope

# with open(client_path, 'w') as f:
#     client_config.write(f)

db_config = configparser.ConfigParser()
db = dbe.DatabaseExport()

# load db.cfg
if os.path.exists(dbconfig_path):
    db_config.read(dbconfig_path, encoding='utf-8')
else:
    db_config['MariaDB'] = {}
    db_config['MariaDB']['host'] = 'ENTER DATABASE URL HERE'
    db_config['MariaDB']['port'] = '3306'
    db_config['MariaDB']['name'] = 'ENTER DATABASE NAME HERE'
    db_config['MariaDB']['user'] = 'ENTER DATABASE USER HERE'
    db_config['MariaDB']['password'] = 'ENTER DATABASE USER PASSWORD HERE'

    if not os.path.exists(os.path.dirname(dbconfig_path)):
        os.mkdir(os.path.dirname(dbconfig_path))
    with open(dbconfig_path, 'w') as f:
        db_config.write(f)

# load client.cfg
if os.path.exists(client_path):
    client_config.read(client_path, encoding='utf-8')
else:
    client_config['Strava'] = {}
    client_config['Strava']['client_Id'] = 'ENTER CLIENT ID HERE'
    client_config['Strava']['client_secret'] = 'ENTER CLIENT SECRET HERE'
    client_config['Strava']['client_code'] = 'ENTER CLIENT CODE FROM OAUTH REDIRECT HERE'
    client_config['Strava']['scope'] = 'read_all,profile:read_all,activity:read_all'

    if not os.path.exists(os.path.dirname(client_path)):
        os.mkdir(os.path.dirname(client_path))
    with open(client_path, 'w') as f:
        client_config.write(f)

# check if auth.cfg already exists from previous authentication (if not, will be created automatically later)
if os.path.exists(auth_path):
    auth_config.read(auth_path, encoding='utf-8')
else:
    # get new tokens from code
    # TODO: also do this when 401 response
    tokendata = {'client_id': client_config['Strava']['client_id'], 
                'client_secret': client_config['Strava']['client_secret'],
                'code': client_config['Strava']['client_code'],
                'grant_type': 'authorization_code'
                }
    r = requests.post(url=token_url, data=tokendata)

    # check for ok response (200)
    if r.status_code == requests.codes.ok:
        stravatokens = r.json()

        # save tokens to config
        auth_config['Strava'] = {}
        auth_config['Strava']['access_token'] = stravatokens['access_token']
        auth_config['Strava']['refresh_token'] = stravatokens['refresh_token']
        auth_config['Strava']['expires_at'] = str(stravatokens['expires_at'])

        # save auth config to file
        if not os.path.exists(os.path.dirname(auth_path)):
            os.mkdir(os.path.dirname(auth_path))
        with open(auth_path, 'w') as f:
            auth_config.write(f)

# check if token expired
currepoch = int(time.time())
if currepoch > int(auth_config['Strava']['expires_at'], base=10):
    # refresh token
    refreshdata = {'client_id': client_config['Strava']['client_id'],
                   'client_secret': client_config['Strava']['client_secret'],
                   'grant_type': 'refresh_token',
                   'refresh_token': auth_config['Strava']['refresh_token']
                   }
    r = requests.post(url=token_url, data=refreshdata)

    # check for ok response (200)
    if r.status_code == requests.codes.ok:
        stravatokens = r.json()

        # update auth.cfg
        # TODO: rework objectified
        auth_config.set(section='Strava', option='access_token', value=stravatokens['access_token'])
        auth_config.set(section='Strava', option='refresh_token', value=stravatokens['refresh_token'])
        auth_config.set(section='Strava', option='expires_at', value=str(stravatokens['expires_at']))

        # write changes of auth.cfg
        if not os.path.exists(os.path.dirname(auth_path)):
            os.mkdir(os.path.dirname(auth_path))
        with open(auth_path, 'w') as f:
            auth_config.write(f)

# establish database connection
dbconn : mariadb.Connection = None
try:
    dbconn = mariadb.connect(user=db_config['MariaDB']['user'],
                             password=db_config['MariaDB']['password'],
                             host=db_config['MariaDB']['host'],
                             port=int(db_config['MariaDB']['port']),
                             database=db_config['MariaDB']['name'])
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
params = {'before': currepoch,
          'page': 1,
          'per_page': 10
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

            


