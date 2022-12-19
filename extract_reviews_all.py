#####################################################################
## Extract Reviews
## Reads the reviews from App Store and Play Store and saves the
## latest result in the local Sqlite3 database together with info
## like ranting, number of ratings and number of reviews
#####################################################################
## Version: 0.1.1 based on extract_reviews.py
## Email: paul.wasicsek@gmail.com
## Status: dev
#####################################################################

import sqlite3
import configparser
import urllib
import datetime
from app_store_scraper import AppStore
from google_play_scraper import app
from google_play_scraper import Sort, reviews_all
import pandas as pd
import logging as log
import os
from random import randint
import time

# global variables
fk_id_app = ""
fk_id_store = ""
fk_id_country = ""
fk_id_language = ""
visit_date = datetime.date.today().strftime("%Y-%m-%d")

# Read initialization parameters
config = configparser.ConfigParser()
try:
    config.read("config.ini")
except Exception as err:
    print('Cannot read INI file due to Error: %s' % (str(err)))
    exit()

# Customize path to your SQLite database
database = config['Database']['DB_Name']

batch_size = int(config['PlayStore']['BatchSize'])
max_reviews = int(config['PlayStore']['MaxDownloadedReviews'])

log.basicConfig(filename=os.path.splitext(__file__)[0] + ".log",
                level=os.environ.get("LOGLEVEL", config['Log']['Level']),
                format='%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S ')

if (config['Action']['Execute'] == "Delay"):
    # Include a waiting period, so the algorithm doesn't think it's automatic processing
    t = randint(int(config['Wait']['Min']), int(config['Wait']['Max']))
    time.sleep(t)

# Connect to the database
try:
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
except Exception as err:
    print('Connecting to DB failed due to: %s\n' % (str(err)))
    exit()


# execute query
def execute(query, param):
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


#
# Input parameters:
#   table name
#   quey_field - column to query for
#   query_value - value for query_field to match
#   name for the result column
# Output:
#   the value stored in the result column
#
def sql_value(table, query_field, query_value, result_field):
    query = "select " + result_field + " from " + table + " where " + query_field + " = " + str(
        query_value)
    execute(query, "")
    row = cursor.fetchone()
    log.debug("Return:" + str(row[0]))
    return (str(row[0]))


def main():
    global fk_id_app
    global fk_id_store
    global fk_id_country
    global fk_id_language

    log.info("=======================")
    log.info("Program start")

    c = execute("select * from applications", "")
    field_names = [description[0] for description in c.description]

    apps = c.fetchall()
    for c_app in apps:
        fk_id_app = c_app[1]
        fk_id_store = c_app[2]
        fk_id_country = c_app[3]
        fk_id_language = c_app[4]
        application_name = sql_value("applications_list", "id_app", fk_id_app,
                                     "application_name")
        application_store = sql_value("stores", "id_store", fk_id_store,
                                      "store_name")
        application_country = sql_value("countries", "id_country",
                                        fk_id_country, "code")
        application_language = sql_value("languages", "id_language",
                                         fk_id_language, "code")

        app_app = c_app[field_names.index("app")]
        app_id = c_app[field_names.index("app_id")]
        app_name = c_app[field_names.index("app_name")]

        log.info("*** Application name: " + application_name + " Store: " +
                 application_store + "Country: " + application_country +
                 "Language: " + application_language + " app name: " +
                 app_name)

        # check iOS application
        if (application_store == "App Store"):
            appstore_app = AppStore(country=application_country,
                                    app_name=app_name,
                                    app_id=app_id)
            appstore_app.review()
            for review in appstore_app.reviews:
                log.info(str(review))
                query = "INSERT INTO reviews(app, store, review_id, reviewer_name, review_title, review_description, rating, thumbs_up, review_date, developer_response, developer_response_date) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
                try:
                    param = (fk_id_app, application_store, "",
                             review['userName'], review['title'],
                             review['review'], review['rating'], "",
                             review['date'],
                             review['developerResponse']['body'],
                             review['developerResponse']['modified'])
                except:
                    param = (fk_id_app, application_store, "",
                             review['userName'], review['title'],
                             review['review'], review['rating'], "",
                             review['date'], "", "")
                log.info("Param: " + str(param))
                execute(query, param)

        if (application_store == "Google Play"):
            result = app(app_name,
                         lang=application_language,
                         country=application_country)
            log.info("result: app name, lang, country: " + app_name + ", " +
                     application_language + ", " + application_country)
            _count = 0

            # while True:
            log.info(
                f"loading from google {application_language}, {application_country}, {_count}..."
            )
            # result, continuation_token = reviews(
            #     app_name,
            #     lang=application_language,
            #     country=application_country,
            #     count=batch_size)
            result = reviews_all(
                app_name,
                sleep_milliseconds=200,  # defaults to 0
                lang=application_language,
                country=application_country)
            for review in result:
                query = "INSERT INTO reviews(app, store, review_id, reviewer_name, review_title, review_description, rating, thumbs_up, review_date, developer_response, developer_response_date) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
                param = (fk_id_app, application_store, review['reviewId'],
                         review['userName'], "", review['content'],
                         review['score'], review['thumbsUpCount'],
                         review['at'], review['replyContent'],
                         review['repliedAt'])
                execute(query, param)

            # result, _ = reviews(app_name,
            #                     continuation_token=continuation_token)

            _count += len(result)
            # time.sleep(randint(1, 5))

            # if continuation_token is None:
            #     break

            # if _count >= max_reviews:
            #     break


if __name__ == '__main__':
    main()
