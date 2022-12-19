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

# Read initialization parameters
config = configparser.ConfigParser()
try:
    config.read("config.ini")
except Exception as err:
    print('Cannot read INI file due to Error: %s' % (str(err)))

log.basicConfig(filename=os.path.splitext(__file__)[0] + ".log",
                level=os.environ.get("LOGLEVEL", config['Log']['Level']),
                format='%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S ')

jiraOptions = {'server': config['Jira']['URL']}
log.info("jiraOptions" + str(jiraOptions))

try:
    jira = JIRA(options=jiraOptions,
                basic_auth=(config['Jira']['Email'],
                            config['Jira']['API_Token']))
except Exception as err:
    print('Connecting to Jira failed due to:', str(err))
    exit()

issue_dict = {
    'project': {
        'id': 10012
    },
    'summary': 'Just a test issue',
    'description':
    'Some summary here and a link to https://RomaniaTravel.guide',
    'issuetype': {
        'name': 'Task'
    },
}

try:
    new_ticket = jira.create_issue(fields=issue_dict)
    log.info("Ticket " + str(new_ticket) + " was created.")
except Exception as err:
    log.debug("Creating Jira ticket failed due to: " + str(err))
