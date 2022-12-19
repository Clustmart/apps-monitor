#####################################################################
## This script copies todays entries from table applications to
## table applications_history where historical data is kept
#####################################################################
## Version: 0.1.2
## Email: paul.wasicsek@gmail.com
## Status: dev
#####################################################################

from email.mime import application
import json
import datetime
import configparser
import sqlite3
import os
import logging as log

# Read initialization parameters
config = configparser.ConfigParser()
try:
    config.read("config.ini")
except Exception as err:
    print('Cannot read INI file due to Error: %s' % (str(err)))

# Customize path to your SQLite database
database = config['Database']['DB_Name']

log.basicConfig(filename=os.path.splitext(__file__)[0] + ".log",
                level=os.environ.get("LOGLEVEL", config['Log']['Level']),
                format='%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S ')

# Connect to the database
try:
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
except Exception as err:
    print('Connecting to DB failed due to: %s\nError: %s' % (str(err)))

# visit_date = datetime.date.today().strftime("%Y-%m-%d")


# execute query
def execute(cursor, query, param):
    log.debug("SQL:" + query)
    log.debug("Param:" + str(param))
    return_value = ""
    try:
        return_value = cursor.execute(query, param)
        if (query.startswith("UPDATE") or query.startswith("INSERT")):
            cursor.execute("COMMIT")
    except Exception as err:
        print('Query Failed: %s\nError: %s' % (query, str(err)))
    return (return_value)


def main():
    log.info("=======================")
    log.info("Program start")

    query = "INSERT INTO applications_history (app, date, rating, rating_count, review_count) SELECT app, visit_date, rating, rating_count, review_count FROM applications  WHERE visit_date = DATE()"
    c = execute(cursor, query, "")


if __name__ == '__main__':
    main()