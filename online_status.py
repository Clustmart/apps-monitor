import gspread
import urllib.request
from urllib.error import HTTPError, URLError
import datetime
import smtplib
import configparser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
from time import sleep
from random import randint

# random delay at program start (as it will be executed from crontab)
sleep(randint(18, 840))


def record_history(sheet, website, timestamp, status):
    wkh = sheet.worksheet("history")
    sh_row = 2
    while wkh.cell(sh_row, 1).value != None:
        sh_row = sh_row + 1
    wkh.update_cell(sh_row, 2, value=timestamp)
    wkh.update_cell(sh_row, 2, value=website)
    wkh.update_cell(sh_row, 3, value=status)


def main():
    print(
        str(datetime.date.today().strftime("%Y-%m-%d %H:%M"))
        + " [START] online_status.py"
    )
    # Read initialization parameters
    config = configparser.ConfigParser()
    try:
        config.read("config.ini")
    except Exception as err:
        print("Cannot read INI file due to Error: %s" % (str(err)))

    s = smtplib.SMTP_SSL(host=config["Email"]["Host"], port=config["Email"]["Port"])
    # s.starttls()
    s.ehlo()
    s.login(config["Email"]["Email"], config["Email"]["Password"])

    sa = gspread.service_account(filename="credentials.json")
    sheet = sa.open("online_status")
    wks = sheet.worksheet("stat")

    sh_row = 2
    while wks.cell(sh_row, 1).value != None:
        website = wks.cell(sh_row, 1).value
        try:
            status = urllib.request.urlopen(website).getcode()
        except HTTPError as error:
            status = error.code
        print(
            str(datetime.date.today().strftime("%Y-%m-%d %H:%M")),
            wks.cell(sh_row, 1).value,
            status,
        )
        wks.update_cell(sh_row, 3, value=status)
        now = str(datetime.datetime.now())
        wks.update_cell(sh_row, 2, value=now[0:19])
        if status != 200:
            wks.update_cell(sh_row, 4, value=now[0:19])
            record_history(sheet, website, now[0:19], status)
            # send an email at program start
            msg = MIMEMultipart()  # create a message
            # setup the parameters of the message
            msg["From"] = config["Email"]["Email"]
            msg["To"] = config["Email"]["Email_To"]
            msg["Subject"] = "ERROR " + str(status) + "accessing " + website
            # add in the message body
            msg.attach(MIMEText("Error accessing website", "plain"))
            # send the message via the server set up earlier.
            s.send_message(msg)
        sh_row = sh_row + 1
    print(
        str(datetime.date.today().strftime("%Y-%m-%d %H:%M"))
        + " [END] online_status.py"
    )


if __name__ == "__main__":
    main()
