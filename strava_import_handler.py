import sys
import polyline
import mariadb
from time import time

import strava_connector as sc
import database_export as dbe

class StravaImportHandler():
    """
    TODO: docstring
    """
    def __init__(self, stravaconfigpath, clientid, clientsecret, clientscope, redirecturi) -> None:
        self.strava = sc.StravaConnector(stravaconfigpath)
        self.data = dbe.DatabaseExport()
        self.clientid = clientid
        self.clientsecret = clientsecret
        self.clientscope = clientscope
        self.clientredirecturi = redirecturi

    def authenticate(self) -> None:
        """
        Handle authentication with Strava API.
        Generate code if nothing exists, or at least provide URL to user to generate code and input code.
        Generate token from code if code exists.
        Generate new token from refresh token if token timed out.
        """
        if self.strava.load_auth_config():
            # config loaded
            # check and refresh validity of tokens if necessary
            self.strava.oauth_refresh_access_token(self.clientid, self.clientsecret)


        else:
            # config not found
            urlstring = self.strava.oauth_get_code(id=self.clientid,
                                                   scope=self.clientscope,
                                                   redirecturi=self.clientredirecturi)
            # TODO: Auth link output
            print(f"Authentication url: {urlstring}")
            try:
                clientcode = input("Enter code generated from authentication redirect: ")
            except EOFError:
                sys.exit(201)

            # TODO: handle wrong input of code
            self.strava.oauth_get_token_from_code(id=self.clientid,
                                                  secret=self.clientsecret,
                                                  code=clientcode)


    def update_db_connection(self, dbConn: mariadb.Connection) -> None:
        self.data.update_connection(dbConn)
    
    def import_all_available(self) -> None:
        pass


    def get_athlete_data(self) -> dict:
        return self.strava.get_athlete_data()
    
    def get_athlete_activity_batch(self, batch_id: int) -> dict:
        return self.strava.get_athlete_activities(start_epoch=0, page_number=batch_id, activities_per_page=50)
    
    def get_detailed_activity(self, activity_id: int) -> dict:
        
        d = self.strava.get_detailed_activity(activity_id)
        
        # decode detailed polylines
        poly = d['map']['polyline']
        # convert to lat, lon tuples
        mapdata = polyline.decode(poly)
        print(f"polyline[{activity_id}]: {len(mapdata)}")

        # TODO: verify data completeness or write with NULL
        self.data.write_detailed_activity_data(activity=d, polyline=mapdata)

        return d