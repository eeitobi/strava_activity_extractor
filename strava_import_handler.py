import sys
from time import time

import strava_connector as sc

class StravaImportHandler():
    """
    TODO: docstring
    """
    def __init__(self, stravaconfigpath, clientid, clientsecret, clientscope, redirecturi) -> None:
        self.strava = sc.StravaConnector(stravaconfigpath)
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

    
    def import_all_available(self) -> None:
        pass