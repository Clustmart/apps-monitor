#####################################################################
# Sync the sqlite datanase with supabase
#
#####################################################################
# Version: 0.1.3
# Email: paul.wasicsek@gmail.com
# Status: dev
#####################################################################
import sqlite3
import configparser
import datetime
import logging as log
import os
import json
from supabase import create_client

# global variables
today = datetime.date.today().strftime("%Y-%m-%d")
column_names = []

# Read initialization parameters
config = configparser.ConfigParser()
try:
    config.read("config.ini")
except Exception as err:
    print("Cannot read INI file due to Error: %s" % (str(err)))

SUPABASE_URL = config["Supabase"]["URL"]
SUPABASE_KEY = config["Supabase"]["Key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

#
# Connect to the database
#
database = config["Database"]["DB_Name"]
try:
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
except Exception as err:
    print("Connecting to DB failed due to: %s\n" % (str(err)))

log.basicConfig(
    filename=config["Log"]["File"],
    level=os.environ.get("LOGLEVEL", config["Log"]["Level"]),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S ",
)


#
# Execute query and populates ? with param.
#
def execute(query, param=""):
    log.debug("SQL:" + query)
    if len(param) > 0:
        log.debug("Param:" + str(param))
    try:
        return_value = cursor.execute(query, param)
        if query.startswith("UPDATE") or query.startswith("INSERT"):
            cursor.execute("COMMIT")
        else:
            return return_value
    except Exception as err:
        print("Query Failed: %s\nError: %s" % (query, str(err)))


#
# Checks if a record already exists in the tabel
# Returns:
#   1 - record exists
#   0 - record doesn't exist
#
def exists(query):
    result = sfirst_row(query)
    log.debug("Exists SQL result: " + str(result[0]))
    return result[0]


#
# Get the column names for a given table
#
def read_column_names(table_name):
    global column_names

    result = execute('select * from ' + table_name)
    column_names = [description[0] for description in result.description]


#
# Read all entries from a sqlite3 table and save them into a json main_list
# Store the list to Supabase
#
def add_from_sqlite_table(table_name):
    global column_names

    main_list = []
    read_column_names(table_name)
    # print(str(column_names))
    # read all database entries
    query = "SELECT * FROM " + table_name
    execute(query)
    result = cursor.fetchall()

    for entry in result:
        row_id = 0
        rowA = '{'
        for name in column_names:
            if (row_id > 0):
                rowA = rowA + ","
            result = str(entry[row_id])
            # result = result.replace("\", "\\")
            # result = result.replace('"', '\"')
            result = result.translate(str.maketrans({'"': r"\"", "\\": r"\\"}))
            rowA = rowA + '"' + name + '":"' + result + '"'
            row_id = row_id + 1
        rowA = rowA + '}'
        json_data = json.loads(rowA, strict=False)
        main_list.append(json_data)
    data = supabase.table(table_name).insert(main_list).execute()


def delete_table_content(table_name):
    data = supabase.table(table_name).delete().neq('id', -1).execute()


def delete_table_content_null(table_name):
    data = supabase.table(table_name).delete().eq('id', 0).execute()


def main():
    log.info("Supabase sync start")
    log.info("Delete table applications")
    delete_table_content_null('applications')
    log.info("Import table applications")
    add_from_sqlite_table('applications')
    # delete_table_content_null('applications_list')
    # add_from_sqlite_table('applications_list')
    # delete_table_content_null('countries')
    # add_from_sqlite_table('countries')
    # delete_table_content_null('languages')
    # add_from_sqlite_table('languages')
    log.info("Delete table reviews")
    delete_table_content_null('reviews')
    add_from_sqlite_table('reviews')
    log.info("Import table reviews")
    # delete_table_content_null('stores')
    # add_from_sqlite_table('stores')


if __name__ == "__main__":
    main()
