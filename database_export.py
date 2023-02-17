import sys
import logging
import mariadb
from datetime import datetime

import mariadb_handler

class DatabaseExport():
    """
    TODO: class docstring
    """
    def __init__(self, dbconn: mariadb.Connection=None) -> None:
        self.log = logging.getLogger("main")
        self.dbconn = dbconn
        self.mdb = mariadb_handler.MariaDbHandler()

    
    def update_connection(self, dbconn: mariadb.Connection) -> None:
        """
        Set database connection.
        """
        self.dbconn = dbconn


    def write_detailed_activity_data(self, activity: dict, polyline: dict = None) -> bool:
        """
        Writes data from detailed activity requests to database.
        Returns 'True' if data was written, 'False' if not.
        """
        # set database cursor/name for operations
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
                                                      id=activity['id'])

        if not activityidcheck:
            # check required parameters
            if 'id' in activity:
                activity_id = activity['id']
            else:
                # TODO: log
                return False
            if 'sport_type' in activity:
                activity_type = activity['sport_type']
            else:
                # TODO: log
                return False
            activity_name = None
            activity_distance = 0
            activity_moving_time = 0
            activity_elapsed_time = 0
            activity_start_date = None
            activity_max_speed = None
            activity_average_heartrate = None
            activity_max_heartrate = None
            activity_calories = 0

            # fill variables
            if 'name' in activity:
                activity_name = activity['name']
            if 'distance' in activity:
                activity_distance = activity['distance']
            if 'moving_time' in activity:
                activity_moving_time = activity['moving_time']
            if 'elapsed_time' in activity:
                activity_elapsed_time = activity['elapsed_time']    
            if 'start_date' in activity:
                # convert time format
                t = datetime.strptime(activity['start_date'], '%Y-%m-%dT%H:%M:%SZ')
                activity_start_date = t.strftime('%Y-%m-%d %H:%M:%S')
            if 'max_speed' in activity:
                activity_max_speed = activity['max_speed']    
            if 'average_heartrate' in activity:
                activity_average_heartrate = activity['average_heartrate']    
            if 'max_heartrate' in activity:
                activity_max_heartrate = activity['max_heartrate']    
            if 'calories' in activity:
                activity_calories = activity['calories']    

            # write activities table
            self.mdb.write_mariadb_data(dbtable='activities',
                                        id=activity_id,
                                        name=activity_name,
                                        type=activity_type,
                                        distance=activity_distance,
                                        moving_time=activity_moving_time,
                                        elapsed_time=activity_elapsed_time,
                                        start_timestamp_utc=activity_start_date,
                                        max_speed=activity_max_speed,
                                        avg_hr=activity_average_heartrate,
                                        max_hr=activity_max_heartrate,
                                        calories=activity_calories)

            # write map data for specific activities
            # TODO: rethink match/case
            match activity['sport_type']:
                case 'AlpineSki' | 'Hike' | 'NordicSki' | 'Ride' | 'Run':
                    self.mdb.update_mariadb_data(dbtable='activities',
                                                 searchcolumnname='id',
                                                 searchcolumnvalue=activity['id'],
                                                 total_elevation_gain=activity['total_elevation_gain'],
                                                 elevation_max=activity['elev_high'],
                                                 elevation_min=activity['elev_low'],
                                                 start_lat=activity['start_latlng'][0],
                                                 start_lon=activity['start_latlng'][1],
                                                 end_lat=activity['end_latlng'][0],
                                                 end_lon=activity['end_latlng'][1])

                    # write polyline data
                    if polyline is not None:
                        for tuple in polyline:
                            # write coordinates table data
                            self.mdb.write_mariadb_data(dbtable='coordinates',
                                                        activity_id=activity['id'],
                                                        latitude=tuple[0],
                                                        longitude=tuple[1])

                case _:
                    # no map data for other sport_type
                    self.log.debug(f"Sport type '{activity['sport_type']}' contains no map information.")

            # write splits_metric table data
            for split in activity['splits_metric']:
                self.mdb.write_mariadb_data(dbtable='splits_metric',
                                            activity_id=activity['id'],
                                            distance=split['distance'],
                                            moving_time=split['moving_time'],
                                            elevation_difference=split['elevation_difference'],
                                            avg_gas=split['average_grade_adjusted_speed'],
                                            avg_hr=split['average_heartrate'])
                
            
            # successfully added activity to database
            return True

        # activity already in database        
        return False