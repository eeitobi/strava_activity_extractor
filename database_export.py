import sys
import logging
import mariadb
from datetime import datetime
import polyline

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


    def write_detailed_activity_data(self, activity: dict) -> None:
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

        # check required parameters
        if 'id' in activity:
            activity_id = activity['id']
        else:
            # TODO: log
            return None


        # check if activity already exists
        # TODO: maybe do this last if already checked before
        activityidcheck = self.check_activity_in_activities(activity_id)
        if not activityidcheck:
            # write essential activity data
            self.write_activities(activity)

        # write map data for specific activities with gps support
        # TODO: list of activities that use gps!
        # TODO: rethink match/case
        match activity['sport_type']:
            case 'AlpineSki' | 'Hike' | 'NordicSki' | 'Ride' | 'Run':

                # check if activity already exists
                activityidcheck = self.check_activity_in_gpsactivities(activity_id)
                if not activityidcheck:
                    # write additional activity data based on gps availability
                    self.write_gpsactivity(activity)
                
                activityidcheck = self.check_activity_in_coordinates(activity_id)
                if not activityidcheck:
                    # write coordinate data
                    self.write_coordinates(activity)
            case _:
                # no map data for other sport_type
                self.log.debug(f"Sport type '{activity['sport_type']}' contains no map information.")

        activityidcheck = self.check_activity_in_splitsmetric(activity_id)
        if not activityidcheck:
            # write splits_metric table data
            self.write_splits(activity)

        # commit after each successfully written activity
        self.dbconn.commit()
    
    
    def check_activity_in_activities(self, id: int) -> bool:
        """
        Checks if the given activity ID is already present in the activities database table.
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

        return self.mdb.check_mariadb_data('activities', id=id)
    
    def check_activity_in_gpsactivities(self, id: int) -> bool:
        """
        Checks if the given activity ID is already present in the gpsactitivies database table.
        """
        return self.mdb.check_mariadb_data('gpsactivities', activity_id=id)
    
    def check_activity_in_splitsmetric(self, id: int) -> bool:
        """
        Checks if a given activity ID is already present in the splits_metric database table.
        """
        return self.mdb.check_mariadb_data('splits_metric', activity_id=id)

    def check_activity_in_coordinates(self, id: int) -> bool:
        """
        Checks if a given activity ID is already present in the coordinates database table.
        """
        return self.mdb.check_mariadb_data('coordinates', activity_id=id)
    
    def write_activities(self, activity: dict) -> bool:
        """
        Writes essential activity information to 'activities' database table.
        """
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
        
        # define 'optional' parameters
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
        
        return True
    
    def write_gpsactivity(self, activity: dict) -> bool:
        """
        Writes additional activity information related to gps availability to 'gpsactivities' database table.
        """
        # check required parameters
        if 'id' in activity:
            activity_id = activity['id']
        else:
            # TODO: log
            return False
        
        # define 'optional' parameters
        total_elevation_gain = None
        elevation_max = None
        elevation_min = None
        start_lat = None
        start_lon = None
        end_lat = None
        end_lon = None

        if 'total_elevation_gain' in activity:
            total_elevation_gain = activity['total_elevation_gain']
        if 'elev_high' in activity:
            elevation_max = activity['elev_high']
        if 'elev_low' in activity:
            elevation_min = activity['elev_low']
        if 'start_latlng' in activity:
            start_lat = activity['start_latlng'][0]
            start_lon = activity['start_latlng'][1]
        if 'end_latlng' in activity:
            end_lat = activity['end_latlng'][0]
            end_lon = activity['end_latlng'][1]

        self.mdb.write_mariadb_data(dbtable='gpsactivities',
                                    activity_id=activity_id,
                                    total_elevation_gain=total_elevation_gain,
                                    elevation_max=elevation_max,
                                    elevation_min=elevation_min,
                                    start_lat=start_lat,
                                    start_lon=start_lon,
                                    end_lat=end_lat,
                                    end_lon=end_lon)
        
        return True
    
    def write_coordinates(self, activity: dict) -> bool:
        """
        Decodes polyline data and writes lat/lon-tuples to 'coordinates' database table.
        """
        # check required parameters
        if 'id' in activity:
            activity_id = activity['id']
        else:
            # TODO: log
            return False
        
        # write polyline data
        poly = None
        if 'map' in activity:
            # use normal polyline if available
            if 'polyline' in activity['map']:
                poly = polyline.decode(activity['map']['polyline'])
                # TODO remove debug print
                print(f"polyline[{activity_id}]: {len(poly)}")

            # use summary polyline as backup if non-truncated map is not available
            elif 'summary_polyline' in activity['map']:
                poly = polyline.decode(activity['map']['summary_polyline'])
                # TODO remove debug print
                print(f"summary polyline[{activity_id}]: {len(poly)}")
        
        if poly is not None:
            for tuple in poly:
                # write coordinates table data
                self.mdb.write_mariadb_data(dbtable='coordinates',
                                            activity_id=activity_id,
                                            latitude=tuple[0],
                                            longitude=tuple[1])
                
        return True
    
    def write_splits(self, activity: dict) -> bool:
        """
        Writes splits activity information to 'splits_metric' database table.
        """
        # check required parameters
        if 'id' in activity:
            activity_id = activity['id']
        else:
            # TODO: log
            return False
        
        for split in activity['splits_metric']:
            # check split data
            split_distance = 0
            split_moving_time = 0
            split_elevation_difference = 0
            split_avg_gas = None
            split_avg_hr = None

            if 'distance' in split:
                split_distance = split['distance']
            if 'moving_time' in split:
                split_moving_time = split['moving_time']
            if 'elevation_difference' in split:
                split_elevation_difference = split['elevation_difference']
            if 'average_grade_adjusted_speed' in split:
                split_avg_gas = split['average_grade_adjusted_speed']
            if 'average_heartrate' in split:
                split_avg_hr = split['average_heartrate']

            self.mdb.write_mariadb_data(dbtable='splits_metric',
                                        activity_id=activity_id,
                                        distance=split_distance,
                                        moving_time=split_moving_time,
                                        elevation_difference=split_elevation_difference,
                                        avg_gas=split_avg_gas,
                                        avg_hr=split_avg_hr)
            
        return True

