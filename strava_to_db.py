import requests
import os
import configparser
import json
import time
import polyline

# query Strava API with access token directly
# http_header = {'Authorization': 'Bearer d623a206053610f20ba7c43f17794d38a8674ce8'}
# http_response = requests.get('https://www.strava.com/api/v3/athlete', headers=http_header)

auth_path = os.path.join(os.curdir, '.stravatokens', 'auth.cfg')
client_path = os.path.join(os.curdir, '.stravatokens', 'client.cfg')

authorization_url = 'http://www.strava.com/oauth/authorize'
# TODO: is it https://www.strava.com/api/v3/oauth/token?
token_url = 'https://www.strava.com/oauth/token'
athlete_url = 'https://www.strava.com/api/v3/athlete'
activities_url = 'https://www.strava.com/api/v3/athlete/activities'
detailed_activity_url = 'https://www.strava.com/api/v3/activities/' # needs {id}/ at the end

# first run probably needs actual client authentication
# http://www.strava.com/oauth/authorize?client_id=76303&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all

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

# load client.cfg
if os.path.exists(client_path):
    client_config.read(client_path, encoding='utf-8')
# TODO: handle client.cfg not existing

# check if auth.cfg already exists from previous authentication
if os.path.exists(auth_path):
    auth_config.read(auth_path, encoding='utf-8')

else:
    # get new tokens from code
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

    # extract polylines
    for i in range(9):        
        poly = activitydata[i]['map']['summary_polyline']

        # convert to lat, lon tuples
        mapdata = polyline.decode(poly)
        print(f"polyline[{i}]: {len(mapdata)}")


