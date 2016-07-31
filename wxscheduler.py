#!/usr/bin/env python
# coding: utf-8

import functools
import schedule
import time

import msgparser
import wxbot
import datetime

class WXScheduler:
    def __init__(self):
        self.DEBUG = False
        self.robot = wxbot.WXBot()

    def catch_exceptions(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                job_func(*args, **kwargs)
            except:
                import traceback
                print(traceback.format_exc())
        return wrapper

    @catch_exceptions
    def job(self):
        print("I'm working...")
        schedule_list = msgparser.list_schedule()
        for schedule in schedule_list:
            now = datetime.datetime.now()
            print(now)
            print(schedule)

    def job_that_executes_once(self):
        # Do some work ...
        return schedule.CancelJob

    def schedule(self):
        schedule.every(1).minutes.do(self.job)

        while 1:
            schedule.run_pending()
            time.sleep(1)


if __name__ == '__main__':
    scheduler = WXScheduler()
    scheduler.schedule()



# schedule.every(1).minutes.do(WXScheduler.job)
# schedule.every().hour.do(job)
# schedule.every().day.at("10:30").do(job)

# schedule.every(10).minutes.do(job)
# schedule.every().hour.do(job)
# schedule.every().day.at("10:30").do(job)
# schedule.every().monday.do(job)
# schedule.every().wednesday.at("13:15").do(job)
# schedule.every().day.at('22:30').do(job_that_executes_once)