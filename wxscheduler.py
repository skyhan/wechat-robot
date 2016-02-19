
import functools
import schedule
import time


class WXScheduler:
    def __init__(self):
        self.DEBUG = False

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
	def job():
	    print("I'm working...")
	    return 1 / 0

	def job_that_executes_once():
	    # Do some work ...
	    return schedule.CancelJob

	schedule.every().day.at('22:30').do(job_that_executes_once)


def main():

	schedule.every(1).minutes.do(job)
	# schedule.every().hour.do(job)
	# schedule.every().day.at("10:30").do(job)

# schedule.every(10).minutes.do(job)
# schedule.every().hour.do(job)
# schedule.every().day.at("10:30").do(job)
# schedule.every().monday.do(job)
# schedule.every().wednesday.at("13:15").do(job)

	while 1:
	    schedule.run_pending()
	    time.sleep(1)

if __name__ == '__main__':
    main()