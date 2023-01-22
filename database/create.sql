CREATE TABLE `activities` (
  `id` bigint PRIMARY KEY,
  `name` varchar(255),
  `type` ENUM ('AlpineSki', 'Hike', 'IceSkate', 'InlineSkate', 'NordicSki', 'Ride', 'Rowing', 'Run', 'Swim') NOT NULL,
  `distance` float,
  `moving_time` int,
  `elapsed_time` int,
  `total_elevation_gain` float,
  `elevation_max` float,
  `elevation_min` float,
  `start_timestamp_utc` datetime,
  `max_speed` float,
  `avg_hr` float,
  `max_hr` float,
  `calories` int,
  `start_lat` float,
  `start_lon` float,
  `end_lat` float,
  `end_lon` float
);

CREATE TABLE `coordinates` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `activity_id` bigint,
  `latitude` float,
  `longitude` float
);

CREATE TABLE `splits_metric` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `activity_id` bigint,
  `distance` float,
  `moving_time` float,
  `elevation_difference` float,
  `avg_gas` float,
  `avg_hr` float
);

ALTER TABLE `coordinates` ADD FOREIGN KEY (`activity_id`) REFERENCES `activities` (`id`);

ALTER TABLE `splits_metric` ADD FOREIGN KEY (`activity_id`) REFERENCES `activities` (`id`);
