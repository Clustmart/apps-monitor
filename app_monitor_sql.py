#####################################################################
## Application Monitor ('AppEye')
## Reads the ranking and number of reviews from App Store and
## Play Store and save the latest result in the local Sqlite3
## database for further processing and reports
#####################################################################
## Version: 0.6.2
## Email: paul.wasicsek@gmail.com
## Status: dev
#####################################################################

import sqlite3
import configparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib
import datetime
from app_store_scraper import AppStore
from google_play_scraper import app
from google_play_scraper import Sort, reviews
import pandas as pd
import logging as log
import os
from random import randint
import time
from jira import JIRA

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

if_new_review = config['Action']['NewReview']

s = smtplib.SMTP_SSL(host=config['Email']['Host'],
                     port=config['Email']['Port'])
#s.starttls()
s.ehlo()
s.login(config['Email']['Email'], config['Email']['Password'])

# Customize path to your SQLite database
database = config['Database']['DB_Name']

log.basicConfig(filename=config['Log']['File'],
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

# Improve https connection handling, see article:
# https://stackoverflow.com/questions/23013220/max-retries-exceeded-with-url-in-requests
#
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)


# execute query
def execute(query, param=""):
    log.debug("SQL:" + query)
    if (len(param) > 0):
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
    execute(query)
    row = cursor.fetchone()
    log.debug("Return:" + str(row[0]))
    return (str(row[0]))


def update_visit_date():
    log.debug("Nothing new ... saving visit_date in database")
    query = "UPDATE applications SET visit_date = '" + str(
        visit_date
    ) + "' WHERE id_app = " + str(fk_id_app) + " AND id_store = " + str(
        fk_id_store) + " AND id_country = " + str(
            fk_id_country) + " AND id_language = " + str(fk_id_language)
    execute(query)


#
#   Sende Email message
#
def send_message(From, To, Subject, Attachment):
    global if_new_review
    if (if_new_review == "SendEmail"):
        # send email to inform about new rating/review
        msg = MIMEMultipart()  # create a message
        # setup the parameters of the message
        msg['From'] = From
        msg['To'] = To
        msg['Subject'] = Subject
        # add in the message body
        msg.attach(MIMEText(Attachment, 'plain'))
        # send the message via the server set up earlier.
        s.send_message(msg)
    if (if_new_review == "CreateJiraTicket"):
        issue_dict = {
            'project': {
                'id': config['Jira']['ProjectID']
            },
            'summary': Subject,
            'description': Attachment,
            'issuetype': {
                'name': 'Task'
            },
        }
        try:
            new_ticket = jira.create_issue(fields=issue_dict)
            log.info("Ticket " + str(new_ticket) + " was created.")
        except Exception as err:
            log.debug("Creating Jira ticket failed due to: " + str(err))
            if_new_review = "SendEmail"
            send_message(config['Email']['Email'], config['Email']['Email_To'],
                         "[ERROR] creating new Jira ticket: ",
                         "Check application log file.")


def new_review_title(result):
    log.debug("... and also a new review title")
    log.debug("last review  RESULT:", str(result[0]))
    query = "UPDATE applications SET last_review_date = ?, last_review_title = ?, last_review_rating = ? WHERE id_app = " + str(
        fk_id_app) + " AND id_store = " + str(
            fk_id_store) + " AND id_country = " + str(
                fk_id_country) + " AND id_language = " + str(fk_id_language)
    param = (str(result[0]['at'].strftime("%Y-%m-%d %H:%M:%S")),
             result[0]['content'], str(result[0]['score']))
    execute(query)


def main():
    global fk_id_app
    global fk_id_store
    global fk_id_country
    global fk_id_language

    log.info("=======================")
    log.info("Program start")
    try:
        external_ip = urllib.request.urlopen('https://ident.me').read().decode(
            'utf8')
    except Exception as err:
        external_ip = "error " + str(err) + "getting external IP"
    log.info("External IP: " + external_ip)
    log.info("=======================")

    if_new_review = config['Action']['NewReview']

    if (if_new_review == "CreateJiraTicket"):
        try:
            jira = JIRA(options=jiraOptions,
                        basic_auth=(config['Jira']['Email'],
                                    config['Jira']['API_Token']))
        except Exception as err:
            print('Connecting to Jira failed due to:', str(err))
            if_new_review = "SendEmail"
            send_message(From, To, "ERROR " + config['Log']['File'],
                         "Can not connect to Jira")
            exit()

    c = execute("select * from applications")
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
        app_id = c_app[field_names.index("app_id")]
        app_name = c_app[field_names.index("app_name")]
        app_url = c_app[field_names.index("url")]
        rating_count = c_app[field_names.index("rating_count")]
        reviews_count = c_app[field_names.index("review_count")]
        last_review_title = c_app[field_names.index("last_review_title")]
        email_alarm = c_app[field_names.index("email_alarm")]

        log.info("*** Application name: " + application_name + " Store: " +
                 application_store + "Country: " + application_country +
                 "Language: " + application_language + " app name: " +
                 app_name)

        # check iOS application
        if (application_store == "App Store"):
            base_url = "https://itunes.apple.com/" + application_country + "/lookup?id=" + str(
                app_id)
            log.debug("Base URL:" + base_url)
            data = session.get(base_url).json()
            # data = requests.get(base_url).json()
            result = data["results"]
            row_json = result[0]

            averageUserRating = row_json["averageUserRating"]
            userRatingCount = row_json["userRatingCount"]

            now = str(datetime.datetime.now())[0:19]
            # check if new user ratings are available
            log.debug("Check for new rating " + str(rating_count) + " != " +
                      str(userRatingCount))
            if (rating_count != userRatingCount):
                # save the new user average ratings and rating count
                query = "UPDATE applications SET rating = '" + str(
                    averageUserRating) + "', rating_count = '" + str(
                        userRatingCount
                    ) + "', last_change = '" + now + "', visit_date='" + str(
                        visit_date) + "' WHERE id_app = " + str(
                            fk_id_app) + " AND id_store = " + str(
                                fk_id_store) + " AND id_country = " + str(
                                    fk_id_country
                                ) + " AND id_language = " + str(fk_id_language)
                execute(query)

                #update with last review date, rating and title
                log.debug("Apple store: country " + application_country +
                          ", name: " + app_name + "id: " + str(app_id))

                appstore_app = AppStore(country=application_country,
                                        app_name=app_name,
                                        app_id=app_id)
                appstore_app.review()
                app_reviews = appstore_app.reviews

                # check that there is already a reviewUPDATE applications SET last_review_date
                if (len(app_reviews) > 0):
                    log.debug("There are some reviews")
                    pd_reviews = pd.DataFrame(app_reviews)
                    sorted_reviews = pd_reviews.sort_values(by='date',
                                                            ascending=False)
                    last_review = sorted_reviews.iloc[0]

                    # if it's a new review, save it and send email
                    if (last_review_title != last_review['title']):
                        log.debug("There is a NEW user review title")
                        log.debug("last review:", last_review)
                        query = "UPDATE applications SET last_review_date = ?, last_review_title = ?, last_review_rating =? WHERE id_app = " + str(
                            fk_id_app) + " AND id_store = " + str(
                                fk_id_store) + " AND id_country = " + str(
                                    fk_id_country
                                ) + " AND id_language = " + str(fk_id_language)
                        param = (
                            last_review['date'].strftime("%Y-%m-%d %H:%M:%S"),
                            last_review['title'], str(last_review['rating']))
                        execute(query, param)
                        if (email_alarm == "y"):
                            send_message(
                                config['Email']['Email'],
                                config['Email']['Email_To'],
                                "[" + application_country +
                                "] New App Store Rating/Review: " +
                                str(last_review['rating']) + " - " +
                                last_review['title'],
                                "New rating or review was published in app store:"
                                + app_url)
            else:
                update_visit_date()

        if (application_store == "Google Play"):
            log.info("Android: app name, lang, country: " + app_name + ", " +
                     application_language + ", " + application_country)
            result = app(app_name,
                         lang=application_language,
                         country=application_country)
            log.debug("app(" + app_name + ",lang=" +
                      str(application_language) + ",country=" +
                      str(application_country) + ")")
            userRatingCount = result['ratings']
            averageUserRating = result['score']
            userReviewsCount = result['reviews']
            now = str(datetime.datetime.now())[0:19]
            log.info("userRatingCount, averageUserRating, userReviewsCount: " +
                     str(userRatingCount) + " " + str(averageUserRating) +
                     " " + str(userReviewsCount))
            log.info("result: app name, lang, country: " + app_name + ", " +
                     application_language + ", " + application_country)
            result, continuation_token = reviews(app_name,
                                                 lang=application_language,
                                                 country=application_country,
                                                 sort=Sort.NEWEST,
                                                 count=1)
            log.debug("Check for new review " + str(reviews_count) + " != " +
                      str(userReviewsCount))
            if (reviews_count != userReviewsCount):
                log.debug("There is a NEW user rating ...")
                # save the new user average ratings and rating count
                # Update Rating and REviews fields
                query = "UPDATE applications SET rating = '" + str(
                    averageUserRating) + "', rating_count = '" + str(
                        userRatingCount
                    ) + "', review_count = '" + str(
                        userReviewsCount
                    ) + "', last_change = '" + now + "', visit_date = '" + str(
                        visit_date) + "' WHERE id_app = " + str(
                            fk_id_app) + " AND id_store = " + str(
                                fk_id_store) + " AND id_country = " + str(
                                    fk_id_country
                                ) + " AND id_language = " + str(fk_id_language)

                execute(query)
                if (len(result) > 0):
                    if (last_review_title != result[0]['content']):
                        new_review_title(result)

                        if (email_alarm == "y"):
                            send_message(
                                config['Email']['Email'],
                                config['Email']['Email_To'],
                                "[" + application_country +
                                "] App Store Rating/Review: " +
                                str(result[0]['score']),
                                "New rating or review was published in app store:"
                                + app_url + '\r\n' + result[0]['content'])
            else:
                update_visit_date()


if __name__ == '__main__':
    main()