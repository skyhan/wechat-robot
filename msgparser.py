#!/usr/bin/env python
# coding: utf-8

import pymysql.cursors
import sys,os
import ConfigParser

def parse_msg(name, content):
	# store schedule
	print('parse msg...')



cf = ConfigParser.ConfigParser()
cf.read("config.ini")

db_host = cf.get("dbconfig", "host")
db_port = cf.getint("dbconfig", "port")
db_user = cf.get("dbconfig", "user")
db_pwd = cf.get("dbconfig", "password")
db_db = cf.get("dbconfig", "db")

# Connect to the database
connection = pymysql.connect(host=db_host,
                             user=db_user,
                             password=db_pwd,
                             db=db_db,
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)

try:
    with connection.cursor() as cursor:
        # Create a new record
        sql = "INSERT INTO `UserSchedule` (`UserName`, `Schedule`, `Content`) VALUES (%s, %s, %s)"
        cursor.execute(sql, ('han', '* * * * *', '加油'))

    # connection is not autocommit by default. So you must commit to save
    # your changes.
    connection.commit()

    with connection.cursor() as cursor:
        # Read a single record
        sql = "SELECT * FROM `UserSchedule` WHERE `UserName`=%s"
        cursor.execute(sql, ('han',))
        result = cursor.fetchone()
        print(result)
finally:
    connection.close()

