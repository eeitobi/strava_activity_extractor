import sys
import logging
import mariadb
from datetime import datetime

import mariadb_handler

class DatabaseExport():
    def __init__(self, dbconn: mariadb.Connection=None) -> None:
        self.log = logging.getLogger("main")
        self.dbconn = dbconn
        self.mdb = mariadb_handler.MariaDbHandler()

    def update_connection(self, dbconn: mariadb.Connection) -> None:
        self.dbconn = dbconn

    def write_activity_data(self) -> None:
        """
        Writes activity to database
        """


    def write_detailed_activity_data(self, responsedata: dict, polyline: dict = None) -> None:
        """
        Writes data from detailed activity requests to database
        """

        # set database cursor/name for opertions
        try:
            cur = self.dbconn.cursor()
            dbname = self.dbconn.database
        except mariadb.Error:
            # TODO: log and handle
            sys.exit(501)
        else:
            # set cursor
            self.mdb.cursor = cur
            # set database
            self.mdb.database = dbname


        # check if activity already exists
        activityidcheck = self.mdb.check_mariadb_data(dbtable='activities',
                                                      id=responsedata['id'])

        if not activityidcheck:
            # convert time
            datetimeutc = datetime.strptime(responsedata['start_date'], '%Y-%m-%dT%H:%M:%SZ')
            starttimeutc = datetimeutc.strftime('%Y-%m-%d %H:%M:%S')

            # write activities table
            self.mdb.write_mariadb_data(dbtable='activities',
                                        id=responsedata['id'],
                                        name=responsedata['name'],
                                        type=responsedata['sport_type'],
                                        distance=responsedata['distance'],
                                        moving_time=responsedata['moving_time'],
                                        elapsed_time=responsedata['elapsed_time'],
                                        start_timestamp_utc=starttimeutc,
                                        max_speed=responsedata['max_speed'],
                                        avg_hr=responsedata['average_heartrate'],
                                        max_hr=responsedata['max_heartrate'],
                                        calories=responsedata['calories'])

            # write map data for specific activities
            # TODO: rethink match/case
            match responsedata['sport_type']:
                case 'AlpineSki' | 'Hike' | 'NordicSki' | 'Ride' | 'Run':
                    self.mdb.update_mariadb_data(dbtable='activities',
                                                 searchcolumnname='id',
                                                 searchcolumnvalue=responsedata['id'],
                                                 total_elevation_gain=responsedata['total_elevation_gain'],
                                                 elevation_max=responsedata['elev_high'],
                                                 elevation_min=responsedata['elev_low'],
                                                 start_lat=responsedata['start_latlng'][0],
                                                 start_lon=responsedata['start_latlng'][1],
                                                 end_lat=responsedata['end_latlng'][0],
                                                 end_lon=responsedata['end_latlng'][1])

                    # write polyline data
                    if polyline is not None:
                        
                        # TODO: not sure if this works
                        for tuple in polyline:
                            # write coordinates table data
                            self.mdb.write_mariadb_data(dbtable='coordinates',
                                                        activity_id=responsedata['id'],
                                                        latitude=tuple[0],
                                                        longitude=tuple[1])

                case _:
                    # no map data for other sport_type
                    self.log.debug(f"Sport type '{responsedata['sport_type']}' contains no map information.")

            # write splits_metric table data
            for split in responsedata['splits_metric']:
                self.mdb.write_mariadb_data(dbtable='splits_metric',
                                            activity_id=responsedata['id'],
                                            distance=split['distance'],
                                            moving_time=split['moving_time'],
                                            elevation_difference=split['elevation_difference'],
                                            avg_gas=split['average_grade_adjusted_speed'],
                                            avg_hr=split['average_heartrate'])