#!/usr/bin/env python
# coding: utf-8

import pymysql.cursors
import sys,os
import ConfigParser


cf = ConfigParser.ConfigParser()
cf.read("config.ini")

db_host = cf.get("dbconfig", "host")
db_port = cf.getint("dbconfig", "port")
db_user = cf.get("dbconfig", "user")
db_pwd = cf.get("dbconfig", "password")
db_db = cf.get("dbconfig", "db")

connection = pymysql.connect(host=db_host,
                                 user=db_user,
                                 password=db_pwd,
                                 db=db_db,
                                 charset='utf8',
                                 cursorclass=pymysql.cursors.DictCursor)

def connect_db():
    # Connect to the database
    connection = pymysql.connect(host=db_host,
                                 user=db_user,
                                 password=db_pwd,
                                 db=db_db,
                                 charset='utf8',
                                 cursorclass=pymysql.cursors.DictCursor)


def parse_msg(name, content):
    # store schedule
    print('parse msg...')


def add_schedule(name, content, schedule):
    try:
        with connection.cursor() as cursor:
            # Create a new record
            sql = "INSERT INTO `UserSchedule` (`UserName`, `Schedule`, `Content`, `IsEnable`) VALUES (%s, %s, %s, 1)"
            cursor.execute(sql, (name, schedule, content))
    
        # connection is not autocommit by default. So you must commit to save
        # your changes.
        connection.commit()
    finally:
        pass
        # connection.close()

def get_schedule(name):
    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT * FROM `UserSchedule` WHERE `UserName` = %s AND `IsEnable` = 1"
            cursor.execute(sql, (name,))
            result = cursor.fetchall()
            return result
    finally:
        pass
    #     connection.close()

def list_schedule():
    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT * FROM `UserSchedule` WHERE `IsEnable` = 1"
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
    finally:
        pass
    #     connection.close()    

if __name__ == '__main__':
    add_schedule('han', 'test', '14:20')
    get_schedule('han')
    list_schedule()
