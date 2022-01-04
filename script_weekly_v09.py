#!/usr/bin/python3

# import os, sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from helpers_v03 import *
import sched
import logging
import logging.handlers

def run_tasks():
	start_time_string = create_friday_start_time_string()
	start_time = parser.parse(start_time_string)

	# # UNCOMMENT LINE BELOW AFTER YEARLY RUN IS DONE
	# # update_json_of_page_ids(start_time_string)

	# # UNCOMMENT LINE BELOW AFTER YEARLY RUN IS DONE
	# # page_histories_directory = 'page_histories'
	# page_histories_directory = 'page_histories_2021_v3'

	# # if you're doing from page_histories_2021_v3, no grabbing of page histories
	# # grab_page_histories_recent_weeks(page_histories_directory, start_time) 

	# # compile stats
	# compile_stats(page_histories_directory, start_time)

	# # make csvs
	# create_csvs(start_time)

	# # make charts
	# create_charts_for_twitter(start_time)

	# # send email with info on when the run finished and how long it took
	# send_email(start_time)

	# UNCOMMENT LINE BELOW AFTER YEARLY RUN IS DONE
	# update github repo 
	# update_github_repo()

	# tweet out charts monday morning and retweet once at lunchtime
	# UNCOMMENT LINE BELOW AFTER YEARLY RUN IS DONE
	# tweet_time_float = create_monday_tweet_time_float_value()
	tweet_time_float = create_tuesday_tweet_time_float_value()
	s = sched.scheduler(time.time, time.sleep)
	s.enterabs(tweet_time_float, 0, send_tweets, argument=(start_time,)) 
	s.run()

# below is just code to send me an email if the script run fails for any reason
config_email = configparser.ConfigParser()
config_email.read('config_email.ini')
receiver_email = config_email['info']['email'] 
sender_email = config_email['info']['sender_email']
sender_password = config_email['info']['sender_password'] 

smtp_handler = logging.handlers.SMTPHandler(
											mailhost=("smtp.gmail.com", 587),
											fromaddr=sender_email, 
											toaddrs=receiver_email,
											subject="Error -- wikipedia abuse checker",
											credentials=(sender_email, sender_password),
											secure=()
											)
logger = logging.getLogger()
logger.addHandler(smtp_handler)

# running the tasks
try:
  run_tasks()
except Exception as e:
  logger.exception(e, stack_info=True)

# /home/ubuntu/work/wikipedia_sanghis/script_weekly_v09.py

# cd /home/ubuntu/work/wikipedia_sanghis && /usr/bin/python3 ./script_weekly_v09.py >> /home/ubuntu/work/wikipedia_sanghis/logs/`date +\%Y-\%m-\%d-\%H:\%M`_script_weekly_v09.log 2>&1