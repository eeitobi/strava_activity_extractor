import sys
import mariadb

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
        """
        TODO: docstring
        """
        # check length of response to find end of activity list
        batch_id = 1
        more_data_available = True

        while(more_data_available):

            activity_batch = self.get_athlete_activity_batch(batch_id=batch_id)
            # Rate limit exception handling is done in the background
            if activity_batch is None:
                print(f"Unlucky. Rate limit reached for now.")
                sys.exit(429)
            print(f"Activity batch received; BatchId; {batch_id};")

            # check length of response and stop execution of loop
            if len(activity_batch) < 50:
                more_data_available = False
                break

            # before requesting detailed activity, check if already in DB (main activities table)
            for activity in activity_batch:
                # check if activity id even exists
                if 'id' in activity:
                    print(f"Check if activity already in DB; ActivityId; {activity['id']};")
                    # check if activity missing
                    if not self.data.check_activity_in_activities(activity['id']):
                        # get detailed activity from API and write to DB
                        detailed_activity = self.get_detailed_activity(activity_id=activity['id'])
                        # Rate limit exception handling done in background already
                        if detailed_activity is None:
                            print(f"Unlucky. Rate limit reached for now.")
                            sys.exit(429)
                        print(f"Detailed activity received; ActivityId; {detailed_activity['id']};")               
                        
            # update batch ID for next run of while loop            
            batch_id += 1


    def get_athlete_data(self) -> dict:
        return self.strava.get_athlete_data()
    

    def get_athlete_activity_batch(self, batch_id: int) -> dict:
        return self.strava.get_athlete_activities(page_number=batch_id, activities_per_page=50)
    

    def get_detailed_activity(self, activity_id: int) -> dict:
        
        d = self.strava.get_detailed_activity(activity_id)

        # TODO: verify data completeness or write with NULL
        self.data.write_detailed_activity_data(d)

        return d