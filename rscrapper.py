# Reviews Scrapper
# Reads the latest review from App Store and Play Store and saves the result in Google Drive
# ver 0.1

from distutils.command.config import LANG_EXT
import json
import requests
import urllib.request
import pandas as pd
from pprint import pprint
import gspread
import datetime
import smtplib
import configparser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
from time import sleep
from random import randint
from app_store_scraper import AppStore
from google_play_scraper import app
from google_play_scraper import Sort, reviews

# Read initialization parameters
config = configparser.ConfigParser()
try:
    config.read("config.ini")
except Exception as err:
    print('Cannot read INI file due to Error: %s' % (str(err)))

s = smtplib.SMTP_SSL(host=config['Email']['Host'],
                     port=config['Email']['Port'])
#s.starttls()
s.ehlo()
s.login(config['Email']['Email'], config['Email']['Password'])


def send_message(From, To, Subject, Attachment):
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


def main():
    sa = gspread.service_account(filename="credentials.json")
    sheet = sa.open("app_reviews")
    wks = sheet.worksheet("check")

    sh_row = 2
    while (wks.cell(sh_row, 1).value != None):
        app_id = str(wks.cell(sh_row, 6).value)
        app_name = str(wks.cell(sh_row, 5).value)
        country = wks.cell(sh_row, 4).value
        lang = wks.cell(sh_row, 14).value
        app_url = str(wks.cell(sh_row, 2).value)
        rating = wks.cell(sh_row, 8).value
        rating_count = wks.cell(sh_row, 9).value
        reviews_count = wks.cell(sh_row, 10).value
        review_title = wks.cell(sh_row, 13).value
        # if (1 == 2):
        # checkk iOS application
        if (wks.cell(sh_row, 2).value == "iOS"):
            print("iOS")
            base_url = "https://itunes.apple.com/" + country + "/lookup?id=" + app_id
            print("Base URL:", base_url)
            data = requests.get(base_url).json()
            result = data["results"]
            row_json = result[0]
            averageUserRating = row_json["averageUserRating"]
            userRatingCount = row_json["userRatingCount"]

            # store Last check
            now = str(datetime.datetime.now())
            wks.update_cell(sh_row, 7, value=now[0:19])

            # check if new user ratings are available
            if (rating_count != userRatingCount):
                print("New rating")
                # save the new user average ratings and rating count
                wks.update_cell(sh_row, 8, value=averageUserRating)
                wks.update_cell(sh_row, 9, value=userRatingCount)

                #update with last review date, rating and title
                appstore_app = AppStore(country=country,
                                        app_name=app_name,
                                        app_id=app_id)
                appstore_app.review()
                app_reviews = appstore_app.reviews
                # check that there is already a review
                if (len(app_reviews) > 0):
                    pd_reviews = pd.DataFrame(app_reviews)
                    sorted_reviews = pd_reviews.sort_values(by='date',
                                                            ascending=False)
                    last_review = sorted_reviews.iloc[0]
                    last_review_date = last_review['date'].strftime(
                        "%Y-%m-%d %H:%M:%S")
                    last_review_title = last_review['title']
                    last_review_rating = str(last_review['rating'])
                    # if it's a new review, save it and send email
                    if (review_title != last_review_title):
                        print("New user review title")
                        wks.update_cell(sh_row, 11, value=last_review_date)
                        wks.update_cell(sh_row, 12, value=last_review_rating)
                        wks.update_cell(sh_row, 13, value=last_review_title)
                        send_message(
                            config['Email']['Email'],
                            config['Email']['Email_To'],
                            "New App Store Rating/Review: " +
                            str(last_review_rating) + " - " +
                            last_review_title,
                            "New rating or review was published in app store:"
                            + app_url)

        if (wks.cell(sh_row, 2).value == "Android"):
            print("Android")
            result = app(app_name, lang=lang, country=country)
            userRatingCount = result['ratings']
            averageUserRating = result['score']
            userReviewsCount = result['reviews']
            last_review_title = ""
            now = str(datetime.datetime.now())
            wks.update_cell(sh_row, 7, value=now[0:19])
            result, continuation_token = reviews(app_name,
                                                 lang=lang,
                                                 country=country,
                                                 sort=Sort.NEWEST,
                                                 count=1)

            # print("reviews count, userReviewsCount", reviews_count, userReviewsCount)
            if (reviews_count != userReviewsCount):
                print("New review")
                # save the new user average ratings and rating count
                # Update Rating and REviews fields
                wks.update_cell(sh_row, 8, value=averageUserRating)
                wks.update_cell(sh_row, 9, value=userRatingCount)
                wks.update_cell(sh_row, 10, value=userReviewsCount)

                if (len(result) > 0):
                    print("write reviews data")
                    last_review_title = result[0]['content']
                    last_review_date = result[0]['at'].strftime(
                        "%Y-%m-%d %H:%M:%S")
                    last_review_rating = result[0]['score']
                    # if it's a new review, save it and send email
                    if (review_title != last_review_title):
                        print("New review title")
                        wks.update_cell(sh_row, 11, value=last_review_date)
                        wks.update_cell(sh_row, 12, value=last_review_rating)
                        wks.update_cell(sh_row, 13, value=last_review_title)
                        send_message(
                            config['Email']['Email'],
                            config['Email']['Email_To'],
                            "App Store Rating/Review: " +
                            str(last_review_rating),
                            "New rating or review was published in app store:"
                            + app_url + '\r\n' + last_review_title)

        sh_row = sh_row + 1


if __name__ == '__main__':
    main()