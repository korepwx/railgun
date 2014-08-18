-- The initial script for MySQL database
-- WARNING: any existing data will be deleted after this script!

-- Drop existing database and user
DROP DATABASE IF EXISTS railgun;

-- Create database and user
CREATE DATABASE railgun CHARACTER SET utf8 COLLATE utf8_bin;
GRANT ALL PRIVILEGES ON railgun.* To 'railgun'@'localhost' IDENTIFIED BY '<the password>';

FLUSH PRIVILEGES;
