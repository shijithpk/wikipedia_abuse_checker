#!/usr/bin/env python3

import json
import os
import time
import requests
from datetime import datetime,timezone
from dateutil.relativedelta import relativedelta
from dateutil import parser
import copy
from collections import defaultdict
import math
import random
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from .helpers import *
import tweepy
import configparser
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



reverted_tags_list = ['mw-reverted']
reverting_tags_list = ['mw-undo','mw-rollback','mw-manual-revert']

utc_time_now = datetime.now(timezone.utc)
utc_time_now_string = utc_time_now.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

time_run_started = utc_time_now.strftime("%b %-d, %H:%M")

time_one_year_ago = utc_time_now - relativedelta(years=1)
time_one_year_ago_string = time_one_year_ago.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

time_six_months_ago = utc_time_now - relativedelta(months=6)
time_six_months_ago_string = time_six_months_ago.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

time_three_months_ago = utc_time_now - relativedelta(months=3)
time_three_months_ago_string = time_three_months_ago.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

time_one_month_ago = utc_time_now - relativedelta(months=1)
time_one_month_ago_string = time_one_month_ago.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

time_four_weeks_ago = utc_time_now - relativedelta(weeks=4)
time_four_weeks_ago_string = time_four_weeks_ago.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

time_two_weeks_ago = utc_time_now - relativedelta(weeks=2)
time_two_weeks_ago_string = time_two_weeks_ago.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

time_one_week_ago = utc_time_now - relativedelta(weeks=1)
time_one_week_ago_string = time_one_week_ago.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

jan_1 = parser.parse("2021-01-01T00:00:00Z")
feb_1 = parser.parse("2021-02-01T00:00:00Z")
mar_1 = parser.parse("2021-03-01T00:00:00Z")
apr_1 = parser.parse("2021-04-01T00:00:00Z")
may_1 = parser.parse("2021-05-01T00:00:00Z")
jun_1 = parser.parse("2021-06-01T00:00:00Z")
jul_1 = parser.parse("2021-07-01T00:00:00Z")
aug_1 = parser.parse("2021-08-01T00:00:00Z")
sep_1 = parser.parse("2021-09-01T00:00:00Z")
oct_1 = parser.parse("2021-10-01T00:00:00Z")
nov_1 = parser.parse("2021-11-01T00:00:00Z")
dec_1 = parser.parse("2021-12-01T00:00:00Z")

api_url = 'https://en.wikipedia.org/w/api.php'
headers = {'User-Agent': 'Personal script for querying wikipedia API, owner_name: Shijith, email_id: shijithpk@gmail.com, website: https://shijith.com'}


# code below from https://stackoverflow.com/questions/47675138/how-to-override-backoff-max-while-working-with-requests-retry/
class RetryRequest(Retry):
    def __init__(self, backoff_max=Retry.BACKOFF_MAX, **kwargs):
        super().__init__(**kwargs)
        self.BACKOFF_MAX = backoff_max

    def new(self, **kwargs):
        return super().new(backoff_max=self.BACKOFF_MAX, **kwargs)

# code below from https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/

# retry_strategy = Retry(
retry_strategy = RetryRequest(
    total=30,
	connect=20,
	status=20,
	backoff_factor=1,
	backoff_max = 5400,
    status_forcelist=[101, 429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

##################################################################
# preliminaries for automating tweets

config = configparser.ConfigParser(interpolation=None)
config.read('config_twitter.ini')
BEARER_TOKEN = config['info']['BEARER_TOKEN']
CONSUMER_KEY = config['info']['CONSUMER_KEY']
CONSUMER_SECRET = config['info']['CONSUMER_SECRET']
ACCESS_TOKEN = config['info']['ACCESS_TOKEN']
ACCESS_TOKEN_SECRET = config['info']['ACCESS_TOKEN_SECRET']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# for whenever twitter's api v2 introduces endpoint for uploading images, we'll switch to v2 from v1.1
# client = tweepy.Client(bearer_token=BEARER_TOKEN,
# 						consumer_key=CONSUMER_KEY,
# 						consumer_secret=CONSUMER_SECRET, 
# 						access_token=ACCESS_TOKEN, 
# 						access_token_secret=ACCESS_TOKEN_SECRET,
# 						wait_on_rate_limit=True
# 						)



###################################################################
#this part is about creating a list of bot ids

all_users_group = "bot"
all_users_limit = 500

params = {
		'action': 'query',
		'format': 'json',
		'list': 'allusers',
		'augroup': all_users_group,
		'aulimit': all_users_limit 
	}

delay = random.choice([0.5, 0.6, 0.7, 0.8, 0.9])
time.sleep(delay)			
response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
data = response.json()
combined_users = copy.deepcopy(data)

while 'continue' in data:
	delay = random.choice([0.5, 0.6, 0.7, 0.8, 0.9])
	time.sleep(delay)
	params.update(data['continue'])
	response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
	data = response.json()
	more_users = data['query']['allusers']
	combined_users['query']['allusers'].extend(more_users)

bot_dict_list = combined_users['query']['allusers']
bot_id_list = []
for dictx in bot_dict_list:
	bot_id_raw = dictx['userid']
	bot_id = str(bot_id_raw)
	bot_id_list.append(bot_id)

###################################################################
#loading some files before defining functions 

analysis_files_filename_list = os.listdir("analysis_files")
page_history_filename_list = os.listdir("page_histories")
user_history_filename_list = os.listdir("user_histories")


########################################################################
# code for updating page ids from a wikiproject

def update_wikiproject_page_ids(category_list, categorised_file_name, merged_file_name, new_category_members):
	#new_category_members will be an empty dict

	params = {
			'action': 'query',
			'format': 'json',
			'list':'categorymembers',
			'cmprop': 'ids|title|timestamp',
			'cmlimit': 500,
			'cmstart': utc_time_now_string,
			'cmdir': 'older',
			'cmnamespace': '0|1',
			'cmsort': 'timestamp'
	}
	wikiproject_page_ids_merged_filename = merged_file_name
	wikiproject_page_ids_merged_filepath  = 'analysis_files/' + wikiproject_page_ids_merged_filename
	if wikiproject_page_ids_merged_filename in analysis_files_filename_list:
		opened_page_ids_merged_json = open(wikiproject_page_ids_merged_filepath)
		loaded_page_ids_merged_json = json.load(opened_page_ids_merged_json)
	else:
		loaded_page_ids_merged_json = {'pages':{}}

	wikiproject_page_ids_categorised_filename = categorised_file_name
	wikiproject_page_ids_categorised_filepath = 'analysis_files/' + wikiproject_page_ids_categorised_filename
	if wikiproject_page_ids_categorised_filename in analysis_files_filename_list:
		opened_page_ids_categorised_json = open(wikiproject_page_ids_categorised_filepath)
		loaded_page_ids_categorised_json = json.load(opened_page_ids_categorised_json)

		utc_time_now_string_in_file = loaded_page_ids_categorised_json["utc_time_now_string"]
		params.update({'cmend': utc_time_now_string_in_file})

	else:
		loaded_page_ids_categorised_json = {'pages':{}}
		for category in category_list:
			loaded_page_ids_categorised_json['pages'][category] = {}
		#here no params update for cmend, we're getting all the category members added from the beginning

	# this will get talk pages for articles that have wikiproject india tag in their code
	# you have to convert the talk ids you receive into parent ids and then add them to existing file

	for category in category_list:
		combined_category_members = []

		params.update({'cmtitle': category})
		delay = random.choice([0.5, 0.6, 0.7, 0.8, 0.9])
		time.sleep(delay)
		response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
		data = response.json()

		category_members = data['query']['categorymembers']
		combined_category_members.extend(category_members)

		while 'continue' in data:
			params.update(data['continue'])
			delay = random.choice([0.5, 0.6, 0.7, 0.8, 0.9])
			time.sleep(delay)
			response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
			data = response.json()
			category_members = data['query']['categorymembers']
			combined_category_members.extend(category_members)

		talk_page_id_list = []
		for member in combined_category_members:
			talk_page_id = member['pageid']
			talk_page_id_list.append(talk_page_id)
		
		while talk_page_id_list: #while not an empty list
			fifty_pageid_batch = talk_page_id_list[0:50]
			fifty_pageid_batch_converted = [str(number) for number in fifty_pageid_batch]
			fifty_pageid_string = '|'.join(fifty_pageid_batch_converted)
			second_params = {
					'action':   'query',
					'format':   'json',
					'prop':     'info',
					'pageids':  fifty_pageid_string,
					'inprop': 'subjectid|associatedpage'
					}
			delay = random.choice([0.5, 0.6, 0.7, 0.8, 0.9])
			time.sleep(delay)
			response = http.get(api_url, headers=headers, params=second_params, timeout=(10, 20))
			data = response.json()
			for talk_page_id, talk_page_id_dict in data['query']['pages'].items():
				try:
					page_id_raw = talk_page_id_dict['subjectid']
					page_id = str(page_id_raw)
					page_title = talk_page_id_dict['associatedpage']
					loaded_page_ids_categorised_json['pages'][category][page_id] = page_title
					loaded_page_ids_merged_json['pages'][page_id] = page_title
					new_category_members[page_id] = page_title
				except:
					continue

			del talk_page_id_list[0:50]	

	loaded_page_ids_categorised_json["utc_time_now_string"] = utc_time_now_string
	loaded_page_ids_merged_json["utc_time_now_string"] = utc_time_now_string #just to give a timestamp to the merged json

	with open(wikiproject_page_ids_categorised_filepath, 'w', encoding='utf-8') as filex:
		json.dump(loaded_page_ids_categorised_json, filex, ensure_ascii=False)

	with open(wikiproject_page_ids_merged_filepath, 'w', encoding='utf-8') as filex:
		json.dump(loaded_page_ids_merged_json, filex, ensure_ascii=False)


#########################################################################
# code for grabbing page histories function

def grab_page_histories(pages_dict, pages_dict_for_addition):
	#pages_dict_for_addition is usually an empty dict

	page_ids_for_deletion = []

	for page_id, page_title in pages_dict.items():

		page_history_filename = page_id + '_page_history.json'
		page_history_filepath = 'page_histories/' + page_history_filename

		if page_history_filename in page_history_filename_list:
			page_history_json = open(page_history_filepath)
			combined_pagerevisions = json.load(page_history_json)
			utc_time_now_string_in_file = combined_pagerevisions['utc_time_now_string']
			utc_time_now_string_in_file_timestamp = parser.parse(utc_time_now_string_in_file)
			
			if utc_time_now_string_in_file == utc_time_now_string:
				continue
			else:
				pagerevisions_list = combined_pagerevisions['pagerevisions_list']
				pagerevisions_list_culled = []
				for revision_dict in pagerevisions_list:
					revision_timestamp_string = revision_dict['timestamp']
					revision_timestamp = parser.parse(revision_timestamp_string)
					if ((revision_timestamp >= time_one_year_ago) and (revision_timestamp < time_three_months_ago)):
						pagerevisions_list_culled.append(revision_dict)

				combined_pagerevisions['pagerevisions_list'] = pagerevisions_list_culled
				combined_pagerevisions['utc_time_now_string'] = utc_time_now_string

				# this is for the possibility that a file hasnt been updated in more than 3 months or in over a year
				if time_one_year_ago > utc_time_now_string_in_file_timestamp:
					page_revisions_endpoint = time_one_year_ago_string
				elif time_three_months_ago > utc_time_now_string_in_file_timestamp >= time_one_year_ago:
					page_revisions_endpoint = utc_time_now_string_in_file
				else:
					page_revisions_endpoint = time_three_months_ago_string
		else:
			#to get page creation timestamp
			creation_params = {
					'action':   'query',
					'format':   'json',
					'prop':     'revisions',
					'pageids':  page_id,
					'redirects': '',
					'rvlimit':  1,
					'rvdir': 'newer',
					'rvprop': 'timestamp'
					}

			delay = random.choice([0.5, 0.6, 0.7, 0.8, 0.9])
			time.sleep(delay)
			creation_response = http.get(api_url, headers=headers, params=creation_params, timeout=(10, 20))
			creation_data = creation_response.json()
			try:
				creation_timestamp = creation_data['query']['pages'][page_id]['revisions'][0]['timestamp']
				# this is the page creation timestamp
			except:
				# exception arises when page is redirected to different id
				# am putting in new id in pages_dict and deleting old one
				new_page_id_raw = creation_data['query']['pages'][list(creation_data['query']['pages'].keys())[0]]['pageid']
				new_page_id = str(new_page_id_raw)
				try:
					new_page_title = creation_data['query']['pages'][list(creation_data['query']['pages'].keys())[0]]['title']
				except:
					new_page_title = ''
				pages_dict_for_addition[new_page_id] = new_page_title
				# pages_dict[new_page_id] = new_page_title #nope, seems you cant add to a dict while iterating over it
				page_ids_for_deletion.append(page_id)
				continue

			combined_pagerevisions = {
									'page_id': page_id,
									'page_title': page_title,
									'creation_timestamp': creation_timestamp,
									'utc_time_now_string': utc_time_now_string,
									'pagerevisions_list':[]
									}
			page_revisions_endpoint = time_one_year_ago_string
		
		params = {
				'action':   'query',
				'format':   'json',
				'prop':     'revisions',
				'pageids':  page_id,
				'redirects':'',
				'rvlimit':  500,
				'rvdir':    'older',
				'rvstart':  utc_time_now_string,
				'rvend':    page_revisions_endpoint,
				'rvprop':   'ids|flags|timestamp|user|userid|size|tags' #should I leave comment/parsedcomment out?
				}

		delay = random.choice([0.5, 0.6, 0.7, 0.8, 0.9])
		time.sleep(delay)
		response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
		data = response.json()
		try:
			pagerevisions = data['query']['pages'][page_id]['revisions']
		except: # need this in case of redirects, the page_ids wont match
			new_page_id_raw = data['query']['pages'][list(data['query']['pages'].keys())[0]]['pageid']
			new_page_id = str(new_page_id_raw)
			new_page_title = data['query']['pages'][list(data['query']['pages'].keys())[0]]['title']
			pages_dict_for_addition[new_page_id] = new_page_title
			page_ids_for_deletion.append(page_id)
			continue

		combined_pagerevisions['pagerevisions_list'].extend(pagerevisions)

		while 'continue' in data:
			delay = random.choice([0.5, 0.6, 0.7, 0.8, 0.9])
			time.sleep(delay)
			params.update(data['continue'])
			response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
			data = response.json()
			try:
				pagerevisions = data['query']['pages'][page_id]['revisions']
				combined_pagerevisions['pagerevisions_list'].extend(pagerevisions)
			except:
				new_page_id_raw = data['query']['pages'][list(data['query']['pages'].keys())[0]]['pageid']
				new_page_id = str(new_page_id_raw)
				new_page_title = data['query']['pages'][list(data['query']['pages'].keys())[0]]['title']
				pages_dict_for_addition[new_page_id] = new_page_title
				page_ids_for_deletion.append(page_id)
				break

		with open(page_history_filepath, 'w', encoding='utf-8') as filex:
			json.dump(combined_pagerevisions, filex, ensure_ascii=False)
		
	for page_idx in page_ids_for_deletion:
		del pages_dict[page_idx] #deleting page ids which are being redirected, redirects have already been added

#########################################################
# code to get aggregate stats for graphics
	#analysis of the pages over last week, last month, last 6 months, last 1 year (most edits reverted and most users reverted)
	#new pages formed in the last 3 months (most edits reverted and most users reverted in last week, last month, last 3 months etc.)

def compile_stats(pages_dict, saved_to_disk_filename):

	field_list = [
			'number of edits reverted in past year',
			'number of edits reverted in past 6 months',
			'number of edits reverted in past 3 months',
			'number of edits reverted in past 1 month',
			'number of edits reverted in past 4 weeks',
			'number of edits reverted in past 2 weeks',
			'number of edits reverted in past 1 week',

			'number of users reverted in past year',
			'number of users reverted in past 6 months',
			'number of users reverted in past 3 months',
			'number of users reverted in past 1 month',
			'number of users reverted in past 4 weeks',
			'number of users reverted in past 2 weeks',
			'number of users reverted in past 1 week',

			'number of edits reverted in past 3 months -- new pages only',
			'number of edits reverted in past 1 month -- new pages only',
			'number of edits reverted in past 4 weeks -- new pages only',
			'number of edits reverted in past 2 weeks -- new pages only',
			'number of edits reverted in past 1 week -- new pages only',

			'number of users reverted in past 3 months -- new pages only',
			'number of users reverted in past 1 month -- new pages only',
			'number of users reverted in past 4 weeks -- new pages only',
			'number of users reverted in past 2 weeks -- new pages only',
			'number of users reverted in past 1 week -- new pages only'
	]

	tree = lambda: defaultdict(tree)
	page_histories_analysis_dict = tree()

	for page_id, page_title in pages_dict.items():

		page_history_filename = page_id + '_page_history.json'
		page_history_filepath = 'page_histories/' + page_history_filename

		opened_page_history_json = open(page_history_filepath)
		loaded_page_history_json = json.load(opened_page_history_json)

		creation_timestamp_string = loaded_page_history_json['creation_timestamp']
		creation_timestamp = parser.parse(creation_timestamp_string)

		pagerevisions_list = loaded_page_history_json['pagerevisions_list']

		users_reverted_past_year = []
		users_reverted_past_6_months = []
		users_reverted_past_3_months = []
		users_reverted_past_1_month = []
		users_reverted_past_4_weeks = []
		users_reverted_past_2_weeks = []
		users_reverted_past_1_week = []

		users_reverted_past_3_months_new_pages = []
		users_reverted_past_1_month_new_pages = []
		users_reverted_past_4_weeks_new_pages = []
		users_reverted_past_2_weeks_new_pages = []
		users_reverted_past_1_week_new_pages = []

		for field in field_list:
			# page_histories_analysis_dict[field][page_id]['page_title'] = page_title
			# page_histories_analysis_dict[field][page_id]['value'] = 0
			page_histories_analysis_dict[page_id]['page_title'] = page_title
			page_histories_analysis_dict[page_id][field] = 0

		for revision_dict in pagerevisions_list:
			try:
				user_name = revision_dict['user']
				user_id_raw = revision_dict['userid']
				user_id = str(user_id_raw)
			except:
				continue
			revision_timestamp_string = revision_dict['timestamp']
			revision_timestamp = parser.parse(revision_timestamp_string)
			revision_dict_tags_list = revision_dict['tags']

			if any(elem in revision_dict_tags_list for elem in reverted_tags_list):
				if user_id not in bot_id_list:

					if revision_timestamp >= time_one_year_ago:
						page_histories_analysis_dict[page_id]['number of edits reverted in past year'] += 1
						if user_name not in users_reverted_past_year: users_reverted_past_year.append(user_name)

					if revision_timestamp >= time_six_months_ago:
						page_histories_analysis_dict[page_id]['number of edits reverted in past 6 months'] += 1
						if user_name not in users_reverted_past_6_months: users_reverted_past_6_months.append(user_name)

					if revision_timestamp >= time_three_months_ago:
						page_histories_analysis_dict[page_id]['number of edits reverted in past 3 months'] += 1
						if user_name not in users_reverted_past_3_months: users_reverted_past_3_months.append(user_name)
						if creation_timestamp >= time_three_months_ago:
							page_histories_analysis_dict[page_id]['number of edits reverted in past 3 months -- new pages only'] += 1
							if user_name not in users_reverted_past_3_months_new_pages: users_reverted_past_3_months_new_pages.append(user_name)

					if revision_timestamp >= time_one_month_ago:
						page_histories_analysis_dict[page_id]['number of edits reverted in past 1 month'] += 1
						if user_name not in users_reverted_past_1_month: users_reverted_past_1_month.append(user_name)
						if creation_timestamp >= time_three_months_ago:
							page_histories_analysis_dict[page_id]['number of edits reverted in past 1 month -- new pages only'] += 1
							if user_name not in users_reverted_past_1_month_new_pages: users_reverted_past_1_month_new_pages.append(user_name)

					if revision_timestamp >= time_four_weeks_ago:
						page_histories_analysis_dict[page_id]['number of edits reverted in past 4 weeks'] += 1
						if user_name not in users_reverted_past_4_weeks: users_reverted_past_4_weeks.append(user_name)
						if creation_timestamp >= time_three_months_ago:
							page_histories_analysis_dict[page_id]['number of edits reverted in past 4 weeks -- new pages only'] += 1
							if user_name not in users_reverted_past_4_weeks_new_pages: users_reverted_past_4_weeks_new_pages.append(user_name)

					if revision_timestamp >= time_two_weeks_ago:
						page_histories_analysis_dict[page_id]['number of edits reverted in past 2 weeks'] += 1
						if user_name not in users_reverted_past_2_weeks: users_reverted_past_2_weeks.append(user_name)
						if creation_timestamp >= time_three_months_ago:
							page_histories_analysis_dict[page_id]['number of edits reverted in past 2 weeks -- new pages only'] += 1
							if user_name not in users_reverted_past_2_weeks_new_pages: users_reverted_past_2_weeks_new_pages.append(user_name)

					if revision_timestamp >= time_one_week_ago:
						page_histories_analysis_dict[page_id]['number of edits reverted in past 1 week'] += 1
						if user_name not in users_reverted_past_1_week: users_reverted_past_1_week.append(user_name)
						if creation_timestamp >= time_three_months_ago:
							page_histories_analysis_dict[page_id]['number of edits reverted in past 1 week -- new pages only'] += 1
							if user_name not in users_reverted_past_1_week_new_pages: users_reverted_past_1_week_new_pages.append(user_name)

		page_histories_analysis_dict[page_id]['number of users reverted in past year'] = len(users_reverted_past_year)
		page_histories_analysis_dict[page_id]['number of users reverted in past 6 months'] = len(users_reverted_past_6_months)
		page_histories_analysis_dict[page_id]['number of users reverted in past 3 months'] = len(users_reverted_past_3_months)
		page_histories_analysis_dict[page_id]['number of users reverted in past 1 month'] = len(users_reverted_past_1_month)
		page_histories_analysis_dict[page_id]['number of users reverted in past 4 weeks'] = len(users_reverted_past_4_weeks)
		page_histories_analysis_dict[page_id]['number of users reverted in past 2 weeks'] = len(users_reverted_past_2_weeks)
		page_histories_analysis_dict[page_id]['number of users reverted in past 1 week'] = len(users_reverted_past_1_week)
		page_histories_analysis_dict[page_id]['number of users reverted in past 3 months -- new pages only'] = len(users_reverted_past_3_months_new_pages)
		page_histories_analysis_dict[page_id]['number of users reverted in past 1 month -- new pages only'] = len(users_reverted_past_1_month_new_pages)
		page_histories_analysis_dict[page_id]['number of users reverted in past 4 weeks -- new pages only'] = len(users_reverted_past_4_weeks_new_pages)
		page_histories_analysis_dict[page_id]['number of users reverted in past 2 weeks -- new pages only'] = len(users_reverted_past_2_weeks_new_pages)
		page_histories_analysis_dict[page_id]['number of users reverted in past 1 week -- new pages only'] = len(users_reverted_past_1_week_new_pages)

	# for field in field_list:
	# 	field_dict = page_histories_analysis_dict[field]
	# 	field_dict_sorted = dict(sorted(field_dict.items(), key=lambda item: item[1]['value'], reverse=True))
	# 	page_histories_analysis_dict[field] = field_dict_sorted

	saved_to_disk_filepath = 'analysis_files/' + saved_to_disk_filename
	with open(saved_to_disk_filepath, 'w', encoding='utf-8') as filex:
		json.dump(page_histories_analysis_dict, filex, ensure_ascii=False)


###########################################################################################
# code to compile month-wise stats for 2021 overview

def compile_stats_monthly(pages_dict, saved_to_disk_filename):

	field_list = [
			'number of users reverted Jan to Nov 2021',
			'number of users reverted in Jan 2021',
			'number of users reverted in Feb 2021',
			'number of users reverted in Mar 2021',
			'number of users reverted in Apr 2021',
			'number of users reverted in May 2021',
			'number of users reverted in Jun 2021',
			'number of users reverted in Jul 2021',
			'number of users reverted in Aug 2021',
			'number of users reverted in Sep 2021',
			'number of users reverted in Oct 2021',
			'number of users reverted in Nov 2021',
			]

	tree = lambda: defaultdict(tree)
	page_histories_analysis_dict = tree()

	for page_id, page_title in pages_dict.items():

		page_history_filename = page_id + '_page_history.json'
		page_history_filepath = 'page_histories/' + page_history_filename

		try:
			opened_page_history_json = open(page_history_filepath)
		except:
			continue

		# opened_page_history_json = open(page_history_filepath)
		loaded_page_history_json = json.load(opened_page_history_json)

		pagerevisions_list = loaded_page_history_json['pagerevisions_list']

		users_reverted_jan_to_nov = []
		users_reverted_jan = []
		users_reverted_feb = []
		users_reverted_mar = []
		users_reverted_apr = []
		users_reverted_may = []
		users_reverted_jun = []
		users_reverted_jul = []
		users_reverted_aug = []
		users_reverted_sep = []
		users_reverted_oct = []
		users_reverted_nov = []

		for field in field_list:
			page_histories_analysis_dict[page_id]['page_title'] = page_title
			page_histories_analysis_dict[page_id][field] = 0

		for revision_dict in pagerevisions_list:
			try:
				user_name = revision_dict['user']
				user_id_raw = revision_dict['userid']
				user_id = str(user_id_raw)
			except:
				continue
			revision_timestamp_string = revision_dict['timestamp']
			revision_timestamp = parser.parse(revision_timestamp_string)
			revision_dict_tags_list = revision_dict['tags']

			if any(elem in revision_dict_tags_list for elem in reverted_tags_list):
				if user_id not in bot_id_list:

					if jan_1 <= revision_timestamp < dec_1:
						if user_name not in users_reverted_jan_to_nov: users_reverted_jan_to_nov.append(user_name)

					if jan_1 <= revision_timestamp < feb_1:
						if user_name not in users_reverted_jan: users_reverted_jan.append(user_name)

					if feb_1 <= revision_timestamp < mar_1:
						if user_name not in users_reverted_feb: users_reverted_feb.append(user_name)

					if mar_1 <= revision_timestamp < apr_1:
						if user_name not in users_reverted_mar: users_reverted_mar.append(user_name)

					if apr_1 <= revision_timestamp < may_1:
						if user_name not in users_reverted_apr: users_reverted_apr.append(user_name)

					if may_1 <= revision_timestamp < jun_1:
						if user_name not in users_reverted_may: users_reverted_may.append(user_name)

					if jun_1 <= revision_timestamp < jul_1:
						if user_name not in users_reverted_jun: users_reverted_jun.append(user_name)

					if jul_1 <= revision_timestamp < aug_1:
						if user_name not in users_reverted_jul: users_reverted_jul.append(user_name)

					if aug_1 <= revision_timestamp < sep_1:
						if user_name not in users_reverted_aug: users_reverted_aug.append(user_name)

					if sep_1 <= revision_timestamp < oct_1:
						if user_name not in users_reverted_sep: users_reverted_sep.append(user_name)

					if oct_1 <= revision_timestamp < nov_1:
						if user_name not in users_reverted_oct: users_reverted_oct.append(user_name)

					if nov_1 <= revision_timestamp < dec_1:
						if user_name not in users_reverted_nov: users_reverted_nov.append(user_name)

		page_histories_analysis_dict[page_id]['number of users reverted Jan to Nov 2021'] = len(users_reverted_jan_to_nov)
		page_histories_analysis_dict[page_id]['number of users reverted in Jan 2021'] = len(users_reverted_jan)
		page_histories_analysis_dict[page_id]['number of users reverted in Feb 2021'] = len(users_reverted_feb)
		page_histories_analysis_dict[page_id]['number of users reverted in Mar 2021'] = len(users_reverted_mar)
		page_histories_analysis_dict[page_id]['number of users reverted in Apr 2021'] = len(users_reverted_apr)
		page_histories_analysis_dict[page_id]['number of users reverted in May 2021'] = len(users_reverted_may)
		page_histories_analysis_dict[page_id]['number of users reverted in Jun 2021'] = len(users_reverted_jun)
		page_histories_analysis_dict[page_id]['number of users reverted in Jul 2021'] = len(users_reverted_jul)
		page_histories_analysis_dict[page_id]['number of users reverted in Aug 2021'] = len(users_reverted_aug)
		page_histories_analysis_dict[page_id]['number of users reverted in Sep 2021'] = len(users_reverted_sep)
		page_histories_analysis_dict[page_id]['number of users reverted in Oct 2021'] = len(users_reverted_oct)
		page_histories_analysis_dict[page_id]['number of users reverted in Nov 2021'] = len(users_reverted_nov)

	saved_to_disk_filepath = 'analysis_files/' + saved_to_disk_filename
	with open(saved_to_disk_filepath, 'w', encoding='utf-8') as filex:
		json.dump(page_histories_analysis_dict, filex, ensure_ascii=False)


######################################################################################
# this function below is for creating csvs with for last week, last 2 weeks etc.

def create_csvs(compiled_stats_source_name, category, datetime_object):

	merged_df_columns = [
						'page_id', 
						'page_title',
						'users_reverted_past_year',
						'users_reverted_past_6_months',
						'users_reverted_past_3_months',
						'users_reverted_past_1_month',
						'users_reverted_past_4_weeks',
						'users_reverted_past_2_weeks',
						'users_reverted_past_1_week'
						]
	merged_df = pd.DataFrame(columns=merged_df_columns)

	compiled_stats_file_path = 'analysis_files/' + compiled_stats_source_name
	opened_compiled_stats_json = open(compiled_stats_file_path)
	loaded_compiled_stats_json = json.load(opened_compiled_stats_json)

	for page_id in loaded_compiled_stats_json:
		merged_df = merged_df.append({
				'page_id': page_id,
				'page_title': loaded_compiled_stats_json[page_id]['page_title'],
				'users_reverted_past_year': loaded_compiled_stats_json[page_id]['number of users reverted in past year'],
				'users_reverted_past_6_months': loaded_compiled_stats_json[page_id]['number of users reverted in past 6 months'],
				'users_reverted_past_3_months': loaded_compiled_stats_json[page_id]['number of users reverted in past 3 months'],
				'users_reverted_past_1_month': loaded_compiled_stats_json[page_id]['number of users reverted in past 1 month'],
				'users_reverted_past_4_weeks': loaded_compiled_stats_json[page_id]['number of users reverted in past 4 weeks'],
				'users_reverted_past_2_weeks': loaded_compiled_stats_json[page_id]['number of users reverted in past 2 weeks'],
				'users_reverted_past_1_week': loaded_compiled_stats_json[page_id]['number of users reverted in past 1 week']
				}, ignore_index=True)
	
	merged_df['users_reverted_week_before_last'] = merged_df['users_reverted_past_2_weeks'] - merged_df['users_reverted_past_1_week']
	merged_df['change_from_last_week'] = merged_df['users_reverted_past_1_week'] - merged_df['users_reverted_week_before_last']

	yyyy_mm_dd_string = datetime_object.strftime("%Y-%m-%d")
	# folder_name = yyyy_mm_dd_string + '_' + category
	folder_name = yyyy_mm_dd_string
	folder_path = 'csv_storage/' + folder_name
	if not os.path.exists(folder_path):
		os.mkdir(folder_path)

	#creating only four csvs, not bothering with others for now

	merged_df.sort_values(by=['users_reverted_past_1_week','users_reverted_past_2_weeks','users_reverted_past_1_month',
							'users_reverted_past_3_months','users_reverted_past_6_months','users_reverted_past_year'],
							ascending=[False,False,False,False,False,False], inplace=True)
	df_culled = merged_df[['page_title', 'users_reverted_past_1_week']].head(10)
	df_culled_filepath = folder_path + '/' + category + '_pages_most_users_reverted_past_1_week.csv'
	df_culled.to_csv(df_culled_filepath, index=False, encoding='utf-8')

	merged_df.sort_values(by=['users_reverted_past_1_month', 'users_reverted_past_3_months',
								'users_reverted_past_6_months','users_reverted_past_year'],
							ascending=[False,False,False,False], inplace=True)
	df_culled = merged_df[['page_title', 'users_reverted_past_1_month']].head(10)
	df_culled_filepath = folder_path + '/' + category + '_pages_most_users_reverted_past_1_month.csv'
	df_culled.to_csv(df_culled_filepath, index=False, encoding='utf-8')

	merged_df.sort_values(by=['users_reverted_past_3_months','users_reverted_past_6_months','users_reverted_past_year'],
							ascending=[False,False,False], inplace=True)
	df_culled = merged_df[['page_title', 'users_reverted_past_3_months']].head(10)
	df_culled_filepath = folder_path + '/' + category + '_pages_most_users_reverted_past_3_months.csv'
	df_culled.to_csv(df_culled_filepath, index=False, encoding='utf-8')

	merged_df.sort_values(by=['change_from_last_week','users_reverted_past_1_week','users_reverted_past_2_weeks','users_reverted_past_1_month',
							'users_reverted_past_3_months','users_reverted_past_6_months','users_reverted_past_year'],
							ascending=[False,False,False,False,False,False,False], inplace=True)
	df_culled = merged_df[['page_title', 'change_from_last_week']].head(10)
	df_culled_filepath = folder_path + '/' + category + '_pages_most_users_reverted_delta_from_last_week.csv'
	df_culled.to_csv(df_culled_filepath, index=False, encoding='utf-8')


######################################################################################
# this function below is for creating month-wise CSVs for 2021 overview

def create_monthly_stats_csvs():
	category_list = ['politics','nonpolitics']
	# in actual file there will be politics and non politics sections, will have to adapt code below when file's ready
	field_dict = {
		'number of users reverted Jan to Nov 2021':{
													'csv_name':'number_users_reverted_Jan_to_Nov_2021.csv',
													'column_name':'number_users_reverted_Jan_to_Nov_2021',
													},
		'number of users reverted in Jan 2021':{
													'csv_name':'number_users_reverted_Jan_2021.csv',
													'column_name':'number_users_reverted_Jan_2021',
													},
		'number of users reverted in Feb 2021':{
													'csv_name':'number_users_reverted_Feb_2021.csv',
													'column_name':'number_users_reverted_Feb_2021',
													},
		'number of users reverted in Mar 2021':{
													'csv_name':'number_users_reverted_Mar_2021.csv',
													'column_name':'number_users_reverted_Mar_2021',
													},
		'number of users reverted in Apr 2021':{
													'csv_name':'number_users_reverted_Apr_2021.csv',
													'column_name':'number_users_reverted_Apr_2021',
													},
		'number of users reverted in May 2021':{
													'csv_name':'number_users_reverted_May_2021.csv',
													'column_name':'number_users_reverted_May_2021',
													},
		'number of users reverted in Jun 2021':{
													'csv_name':'number_users_reverted_Jun_2021.csv',
													'column_name':'number_users_reverted_Jun_2021',
													},
		'number of users reverted in Jul 2021':{
													'csv_name':'number_users_reverted_Jul_2021.csv',
													'column_name':'number_users_reverted_Jul_2021',
													},
		'number of users reverted in Aug 2021':{
													'csv_name':'number_users_reverted_Aug_2021.csv',
													'column_name':'number_users_reverted_Aug_2021',
													},
		'number of users reverted in Sep 2021':{
													'csv_name':'number_users_reverted_Sep_2021.csv',
													'column_name':'number_users_reverted_Sep_2021',
													},
		'number of users reverted in Oct 2021':{
													'csv_name':'number_users_reverted_Oct_2021.csv',
													'column_name':'number_users_reverted_Oct_2021',
													},
		'number of users reverted in Nov 2021':{
													'csv_name':'number_users_reverted_Nov_2021.csv',
													'column_name':'number_users_reverted_Nov_2021',
													},
		}

	for category in category_list:
		saved_to_disk_filename = 'compiled_monthly_stats_' + category + '.json' 

		field_column_names = [field_dict[field]['column_name'] for field in field_dict]
		merged_df_columns = ['page_id','page_title'] + field_column_names
		merged_df = pd.DataFrame(columns=merged_df_columns)

		compiled_stats_file_path = 'analysis_files/' + saved_to_disk_filename
		opened_compiled_stats_json = open(compiled_stats_file_path)
		loaded_compiled_stats_json = json.load(opened_compiled_stats_json)

		for page_id in loaded_compiled_stats_json:
			merged_df_dict = {
							'page_id': page_id,
							'page_title': loaded_compiled_stats_json[page_id]['page_title'],
							}
			for field in field_dict:
				field_column_name = field_dict[field]['column_name']
				merged_df_dict[field_column_name] = loaded_compiled_stats_json[page_id][field]
			merged_df = merged_df.append(merged_df_dict, ignore_index=True)

		folder_name = '2021_stats'
		folder_path = 'csv_storage/' + folder_name
		if not os.path.exists(folder_path):
			os.mkdir(folder_path)

		for field in field_dict:
			field_column_name = field_dict[field]['column_name']
			merged_df.sort_values(by=[field_column_name,'number_users_reverted_Jan_to_Nov_2021'],
									ascending=[False,False],
									inplace=True
									)
			# using the users over reverted whole year figures to break ties in first column

			field_csv_name = category + '_' + field_dict[field]['csv_name']
			df_culled = merged_df[['page_title', field_column_name]].head(10)
			df_culled_filepath = folder_path + '/' + field_csv_name
			df_culled.to_csv(df_culled_filepath, index=False, encoding='utf-8')


###################################################################################################
# this function is for creating graphics for last weeks and recent past in blog color theme 

def create_charts_blog_style():

	font_family = 'Rubik'
	chart_title_font_size = 21
	explanation_string_font_size = 18
	body_copy_font_size = 18
	table_line_width = 1
	table_line_color = '#444444'

	cell_height_table_header = 20 #plotly doesnt follow whatever I put here
	cell_height_table_body = 62
	copy_font_color = '#444444'
	background_color = '#e1e1e1'
	highlight_color = '#ff652f'


	yyyy_mm_dd_string = utc_time_now.strftime("%Y-%m-%d")

	category_dict = {'delta_from_last_week': {
										'chart_title': '<b>Indian pages on Wikipedia facing highest rise in vandalism*<b>',
										},
					'past_3_months': 	{
										'chart_title': '<b>Most vandalised* Indian pages on Wikipedia over past 3 months<b>',
										},
					'past_1_month': 	{
										'chart_title': '<b>Most vandalised* Indian pages on Wikipedia over past 1 month<b>',
										},						
					'past_1_week': 		{
										'chart_title': '<b>Most vandalised* Indian pages on Wikipedia last week<b>',
										}
						}	

	for category in category_dict:
		fig = make_subplots(
			rows= 1, 
			cols= 2,
			horizontal_spacing=0,
			specs = [
					[{'type': 'table'},{'type': 'table'}],
					],
		)

		column_number = 0

		for subcategory in ['politics', 'nonpolitics']:
			column_number += 1
			csv_name = subcategory + '_pages_most_users_reverted_' + category + '.csv'
			folder_name = yyyy_mm_dd_string
			folder_path = 'csv_storage/' + folder_name
			csv_path = folder_path + '/' + csv_name
			subcategory_df_raw = pd.read_csv(csv_path)
			subcategory_df_raw['rank'] = range(1,1+len(subcategory_df_raw))
			subcategory_df_raw['truncated_page_title'] = subcategory_df_raw['page_title'].apply(
				lambda x: x if len(x) <= 50 else (x[0:47] + '...')
			)

			subcategory_df_raw['combined'] = '<b>' + subcategory_df_raw['rank'].astype(str) + '.</b> ' +subcategory_df_raw['truncated_page_title'] +' (' +	subcategory_df_raw.iloc[:, 1].astype(str) + ')'
			subcategory_df = subcategory_df_raw[['combined']]

			subcategory_df_page_titles = subcategory_df['combined'].tolist()[0:5]

			if subcategory == 'politics':
				header_text = '<b>Politics Pages</b>'
			else:
				header_text = '<b>Non-Politics Pages</b>'

			fig.add_trace(
				go.Table(
					header=dict(
								values=[header_text], 
								fill_color=background_color,
								line_color=table_line_color,
								line_width = table_line_width,
								align=['center'],
								font=dict(
										color=highlight_color, 
										size=body_copy_font_size,
										family=font_family,
										),
								height= cell_height_table_header
								),
					cells=dict(
								values=[subcategory_df_page_titles],
								fill_color=background_color,
								line_color=table_line_color,
								line_width = table_line_width,
								align=['left'],
								font=dict(
										color=copy_font_color, 
										size=body_copy_font_size,
										family=font_family,
										),
								height=cell_height_table_body,
								),
								),
								row=1, 
								col=column_number
								)


		updated_date = utc_time_now.strftime("%b %-d, %Y")
		if category == 'delta_from_last_week':
			explanation_string = "*Vandalism here is measured by the growth since last week in users (figure in brackets)<br>whose edits are reverted on a page. Data as on " + updated_date
		else:
			explanation_string = "*Vandalism here is measured by the number of users (figure in brackets) whose edits<br>have been reverted on a page. Data as on " + updated_date

		fig.add_annotation(
						text=explanation_string,
						font=dict(
								color=copy_font_color,
								size=explanation_string_font_size,
								family=font_family,
								),
                  		xref="paper", 
						x=0,
						xanchor = 'left',
						yref="paper",
                   		y=0.08, 
						yanchor = 'middle',
				   		showarrow=False,
						align = 'left',
						)

		fig.update_layout(
			# autosize=True,
			height = 450, 
			width = 800,
			margin=dict(
						l=12,
						r=12,
						b=0,
						t=40,
						pad=0
					),
			title = dict(
					text = category_dict[category]['chart_title'],
					font = dict(
							color=highlight_color, 
							size=chart_title_font_size,
							family=font_family,
							),
					x = 0.5,
					xanchor = 'center',
					xref = 'container', #the option paper is just for the plotting area, container is for the whole plot
					y = 0.975,
					yanchor = 'top',
					yref = 'container', #not using container here
					),
			paper_bgcolor=background_color,
			)


		img_file_name = category + '.webp'
		img_path_currentfolder = 'image_storage/2021_overview_images/' + img_file_name
		fig.write_image(img_path_currentfolder, format='webp', scale=2)


######################################################################################################
# this function is for creating graphics for 2021 overview in blog color theme -- top 10 for the year

def create_charts_top_10():

	font_family = 'Rubik'
	# font_family = 'DejaVu Sans Mono'
	chart_title_font_size = 25
	explanation_string_font_size = 22
	# subplot_title_font_size = 18
	body_copy_font_size = 21
	table_line_width = 1
	table_line_color = '#444444'
	cell_height_table_header = 40
	cell_height_table_body = 85
	copy_font_color = '#444444'
	background_color = '#e1e1e1'
	highlight_color = '#ff652f'

	fig = make_subplots(
	rows= 1, 
	cols= 2,
	horizontal_spacing=0,
	specs = [
			[{'type': 'table'},{'type': 'table'}],
			],
	)

	column_number = 0
	category_list = ['politics', 'nonpolitics']
	for category in category_list:
		column_number += 1
		csv_path = "csv_storage/2021_stats/" + category + "_number_users_reverted_Jan_to_Nov_2021.csv"
		category_df_raw = pd.read_csv(csv_path)
		category_df_raw['rank'] = range(1,1+len(category_df_raw))
		category_df_raw['truncated_page_title'] = category_df_raw['page_title'].apply(
			lambda x: x if len(x) <= 50 else (x[0:47] + '...')
		)

		# category_df_raw['combined'] = "<b>"+category_df_raw['rank'].astype(str) + '.</b> ' + category_df_raw['page_title'] +' (' +	category_df_raw.iloc[:, 1].astype(str) + ')'
		category_df_raw['combined'] = '<b>'+ category_df_raw['rank'].astype(str) + '.</b> ' + category_df_raw['truncated_page_title'] +' (' +	category_df_raw.iloc[:, 1].astype(str) + ')'

		category_df = category_df_raw[['combined']]

		# category_df_page_titles = category_df['combined'].tolist()[0:5]
		category_df_page_titles = category_df['combined'].tolist() # including all titles

		if category == 'politics':
			header_text = '<b>Politics Pages</b>'
		else:
			header_text = '<b>Non-Politics Pages</b>'

		fig.add_trace(
			go.Table(
				header=dict(
							values=[header_text], 
							fill_color=background_color,
							line_color=table_line_color,
							line_width = table_line_width,
							align=['center'],
							font=dict(
									color=highlight_color, 
									size=body_copy_font_size,
									family=font_family,
									),
							height=cell_height_table_header
							),
				cells=dict(
							values=[category_df_page_titles],
							fill_color=background_color,
							line_color=table_line_color,
							line_width = table_line_width,
							align=['left'],
							font=dict(
									color=copy_font_color, 
									size=body_copy_font_size,
									family=font_family,
									),
							height=cell_height_table_body,
							),
							),
							row=1, 
							col=column_number
							)

	explanation_string = "*Vandalism here is the number of users (figure in brackets) whose<br>edits have been reverted on a page from Jan-Nov 2021."

	fig.add_annotation(
					text=explanation_string,
					font=dict(
							color = copy_font_color,
							size=explanation_string_font_size,
							family=font_family,
							),
					xref="paper", 
					x=0,
					xanchor = 'left',
					yref="paper",
					y=0.05, 
					yanchor = 'middle',
					showarrow=False,
					align = 'left',
					)

	fig.update_layout(
		width = 800,
		# height = 450, # for traditional 16:9
		# height = 600, # for 4:3
		height = 1067, # for 3:4
		margin=dict(
					l=25,
					r=25,
					b=0,
					t=60,
					pad=0
				),
		title = dict(
				text = '<b>Most vandalised* Indian pages on Wikipedia in 2021<b>',
				font = dict(
						color=highlight_color, 
						size=chart_title_font_size,
						family=font_family,
						),
				x = 0.5,
				xanchor = 'center',
				xref = 'container', #the option paper is just for the plotting area, container is for the whole plot
				y = 0.98,
				yanchor = 'top',
				yref = 'container', #not using container here
				),
		paper_bgcolor=background_color,
		)

	img_file_name = '2021_top_10.webp'
	folder_name = '2021_overview_images'
	folder_path = 'image_storage/' + folder_name
	if not os.path.exists(folder_path):
		os.mkdir(folder_path)
	img_path_datefolder = folder_path + '/' + img_file_name
	fig.write_image(img_path_datefolder, format='webp', scale=2)


######################################################################################################
# this function is for creating graphics for 2021 overview in blog color theme -- month-wise top 3 pages

def create_charts_monthly_top_titles():
	font_family = 'Rubik'
	# font_family = 'DejaVu Sans Mono'
	chart_title_font_size = 30
	explanation_string_font_size = 20
	# subplot_title_font_size = 18
	body_copy_font_size = 20
	table_line_width = 1
	table_line_color = '#444444'
	cell_height_table_header = 20 # doesnt matter, plotly doesnt follow it, does whatever height fits the text in
	cell_height_table_body = 25
	copy_font_color = '#444444'
	background_color = '#e1e1e1'
	highlight_color = '#ff652f'

	category_list = ['politics','nonpolitics']

	month_dict = {	'Jan': {'row':1, 'col':2}, 
					'Feb': {'row':2, 'col':1}, 
					'Mar': {'row':2, 'col':2}, 
					'Apr': {'row':3, 'col':1}, 
					'May': {'row':3, 'col':2}, 
					'Jun': {'row':4, 'col':1}, 
					'Jul': {'row':4, 'col':2}, 
					'Aug': {'row':5, 'col':1}, 
					'Sep': {'row':5, 'col':2}, 
					'Oct': {'row':6, 'col':1}, 
					'Nov': {'row':6, 'col':2},
					}

	for category in category_list:
		fig = make_subplots(
							rows= 6, 
							cols= 2,
							horizontal_spacing=0.01,
							vertical_spacing=0,
							specs = [
							[None,{'type': 'table','l':0,'r':0,'b':0,'t':0}],
							[{'type': 'table','l':0,'r':0,'b':0,'t':0},{'type': 'table','l':0,'r':0,'b':0,'t':0}],
							[{'type': 'table','l':0,'r':0,'b':0,'t':0},{'type': 'table','l':0,'r':0,'b':0,'t':0}],
							[{'type': 'table','l':0,'r':0,'b':0,'t':0},{'type': 'table','l':0,'r':0,'b':0,'t':0}],
							[{'type': 'table','l':0,'r':0,'b':0,'t':0},{'type': 'table','l':0,'r':0,'b':0,'t':0}],
							[{'type': 'table','l':0,'r':0,'b':0,'t':0},{'type': 'table','l':0,'r':0,'b':0,'t':0}],
							],
							)

		for month in month_dict:
			csv_path = "csv_storage/2021_stats/" + category + "_number_users_reverted_" + month + "_2021.csv"
			category_df_raw = pd.read_csv(csv_path)
			category_df_raw['rank'] = range(1,1+len(category_df_raw))
			category_df_raw['truncated_page_title'] = category_df_raw['page_title'].apply(
				lambda x: x if len(x) <= 50 else (x[0:47] + '...')
			)

			category_df_raw['combined'] = '<b>'+ category_df_raw['rank'].astype(str) + '.</b> ' + category_df_raw['truncated_page_title'] +' (' +	category_df_raw.iloc[:, 1].astype(str) + ')'

			category_df = category_df_raw[['combined']]

			category_df_page_titles = category_df['combined'].tolist()[0:2]

			header_text = '<b>' + month + ' 2021</b>'

			fig.add_trace(
				go.Table(
					header=dict(
								values=[header_text], 
								fill_color=background_color,
								line_color=table_line_color,
								line_width = table_line_width,
								align=['center'],
								font=dict(
										color=highlight_color, 
										size=body_copy_font_size,
										family=font_family,
										),
								height=cell_height_table_header
								),
					cells=dict(
								values=[category_df_page_titles],
								fill_color=background_color,
								line_color=table_line_color,
								line_width = table_line_width,
								align=['left'],
								font=dict(
										color=copy_font_color, 
										size=body_copy_font_size,
										family=font_family,
										),
								height=cell_height_table_body,
								),
								),
				row= month_dict[month]['row'], 
				col= month_dict[month]['col']
				)

		explanation_string = "*Vandalism here is the number of users (figure in brackets) whose<br>edits have been reverted on a page for that month."

		fig.add_annotation(
						text=explanation_string,
						font=dict(
								color = copy_font_color,
								size=explanation_string_font_size,
								family=font_family,
								),
						xref="paper", 
						x=0,
						xanchor = 'left',
						yref="paper",
						y=0.05, 
						yanchor = 'middle',
						showarrow=False,
						align = 'left',
						)
		if category == 'politics':
			title_substring = '(Politics Pages)'
		else:
			title_substring = '(Non-Politics Pages)'
		fig.update_layout(
			width = 800,
			height = 1067, # for 3:4
			margin=dict(
						l=10,
						r=10,
						b=0,
						t=20,
						pad=0
					),
			title = dict(
					text = '<b>Most vandalised* Indian<br>pages on Wikipedia for<br>every month of 2021<br>' + title_substring + '<b>',
					font = dict(
							color=highlight_color, 
							size=chart_title_font_size,
							family=font_family,
							),
					x = 0.03,
					xanchor = 'left',
					xref = 'container', #the option paper is just for the plotting area, container is for the whole plot
					y = 0.95,
					yanchor = 'top',
					yref = 'container', #not using container here
					),
			paper_bgcolor=background_color,
			)

		img_file_name = category + '_2021_monthly_top_pages.webp'
		# img_file_name = category + '_2021_monthly_top_pages.svg'
		folder_name = '2021_overview_images'
		folder_path = 'image_storage/' + folder_name
		if not os.path.exists(folder_path):
			os.mkdir(folder_path)
		img_path_datefolder = folder_path + '/' + img_file_name
		fig.write_image(img_path_datefolder, format='webp', scale=2)
		# fig.write_image(img_path_datefolder, format='svg', scale=2)

####################################################################################################
# this function is for creating weekly graphics in sparse style and monospace font for tweeting out 

def create_charts_for_twitter():

	font_family = 'DejaVu Sans Mono'
	chart_title_font_size = 21
	explanation_string_font_size = 18
	body_copy_font_size = 18
	table_line_width = 1
	table_line_color = '#333333'

	yyyy_mm_dd_string = utc_time_now.strftime("%Y-%m-%d")

	category_dict = {'delta_from_last_week': {
										# 'second_column_name': 'Growth In Reverted Users',
										'chart_title': '<b>Indian pages on Wikipedia facing highest rise in vandalism*<b>',
										},
					'past_3_months': 	{
										# 'second_column_name': 'Reverted Users',
										'chart_title': '<b>Most vandalised* Indian pages on Wikipedia over past 3 months<b>',
										},
					'past_1_month': 	{
										# 'second_column_name': 'Reverted Users',
										'chart_title': '<b>Most vandalised* Indian pages on Wikipedia over past 1 month<b>',
										},						
					'past_1_week': 		{
										# 'second_column_name': 'Reverted Users',
										'chart_title': '<b>Most vandalised* Indian pages on Wikipedia last week<b>',
										} #should I make this no. of reverted users last week?
						}
	

	for category in category_dict:
		fig = make_subplots(
			rows= 1, 
			cols= 2,
			horizontal_spacing=0,
			specs = [
					[{'type': 'table'},{'type': 'table'}],
					],
			# subplot_titles = ['Politics Pages', 'Non-Politics Pages'],
			# if you dont want to set subplot titles beforehand, you can follow instructions here -- https://stackoverflow.com/questions/63220009/how-do-i-set-each-plotly-subplot-title-during-graph-creation-loop
		)

		column_number = 0

		for subcategory in ['politics', 'nonpolitics']:
			column_number += 1
			csv_name = subcategory + '_pages_most_users_reverted_' + category + '.csv'
			folder_name = yyyy_mm_dd_string
			folder_path = 'csv_storage/' + folder_name
			csv_path = folder_path + '/' + csv_name
			subcategory_df_raw = pd.read_csv(csv_path)
			subcategory_df_raw['rank'] = range(1,1+len(subcategory_df_raw))
			subcategory_df_raw['truncated_page_title'] = subcategory_df_raw['page_title'].apply(
				lambda x: x if len(x) <= 50 else (x[0:47] + '...')
			)

			subcategory_df_raw['combined'] = subcategory_df_raw['rank'].astype(str) + '. ' +subcategory_df_raw['truncated_page_title'] +' (' +	subcategory_df_raw.iloc[:, 1].astype(str) + ')'
			# subcategory_df_raw['combined'] = '<b>' + subcategory_df_raw['rank'].astype(str) + '.</b> ' +subcategory_df_raw['page_title'] +' (' +	subcategory_df_raw.iloc[:, 1].astype(str) + ')'
			subcategory_df = subcategory_df_raw[['combined']]

			subcategory_df_page_titles = subcategory_df['combined'].tolist()[0:5]

			if subcategory == 'politics':
				header_text = 'Politics Pages'
			else:
				header_text = 'Non-Politics Pages'

			fig.add_trace(
				go.Table(
					# columnwidth = [3,1], #dont set any widths for now, let plotly figure out what's best
					# 					# oh seems columnwidth is a ratio so 2,1 is 2:1, divides width available by ratio
					header=dict(
								# values=('<b>Wikipedia Page Title</b>', second_column_name_bold), 
								# values=['<b>Wikipedia Page Title</b>'], 
								values=[header_text], 
								fill_color='white',
								line_color=table_line_color,
								line_width = table_line_width,
								# line_color='white',
								# align=['center','center'],
								align=['center'],
								font=dict(
										color='black', 
										size=body_copy_font_size,
										family=font_family,
										),
								# height=40  #this is cell height
								height=28
								),
					cells=dict(
								# values=[subcategory_df_page_titles, subcategory_df_page_values],
								values=[subcategory_df_page_titles],
								fill_color='white',
								line_color=table_line_color,
								line_width = table_line_width,
								# line_color='white',
								# align=['left','center'],
								align=['left'],
								font=dict(
										color='black', 
										size=body_copy_font_size,
										family=font_family,
										),
								height=60,
								),
								),
								row=1, 
								col=column_number
								)


		# #below is the style for the titles of the subplots
		# fig.update_annotations(font = dict(
		# 								color='black', 
		# 								size=subplot_title_font_size,
		# 								family=font_family,
		# 								)
		# 								)

		updated_date = utc_time_now.strftime("%b %-d, %Y")
		if category == 'delta_from_last_week':
			explanation_string = "*Vandalism here is measured by the growth since last week in users (no.<br>in brackets) whose edits are reverted on a page. Data as on " + updated_date
		else:
			explanation_string = "*Vandalism here is measured by the number of users (figure in brackets)<br> whose edits have been reverted on a page. Data as on " + updated_date

		fig.add_annotation(
						text=explanation_string,
						font=dict(
								color="black",
								size=explanation_string_font_size,
								family=font_family,
								),
                  		xref="paper", 
						x=0,
						xanchor = 'left',
						yref="paper",
                   		y=0.08, 
						yanchor = 'middle',
				   		showarrow=False,
						align = 'left',
						)

		fig.update_layout(
			# autosize=True,
			height = 450, 
			width = 800,
			margin=dict(
						l=12,
						r=12,
						b=0,
						t=50,
						pad=0
					),
			title = dict(
					text = category_dict[category]['chart_title'],
					font = dict(
							color='black', 
							size=chart_title_font_size,
							family=font_family,
							),
					x = 0.5,
					xanchor = 'center',
					xref = 'container', #the option paper is just for the plotting area, container is for the whole plot
					y = 0.97,
					yanchor = 'top',
					yref = 'container', #not using container here
					),
			# paper_bgcolor="LightSteelBlue",
			)


		# For adding lines or dividers between plots
		# fig.add_shape(
		# 			type="line",
		# 			xref="paper", 
		# 			yref="paper",
		# 			x0=0.5, 
		# 			y0=0, 
		# 			x1=0.5,
		# 			y1=0.8,
		# 			line=dict(
		# 				color="#FFA500", #light orange
		# 				width=1,
		# 				),
		# 			)

		img_file_name = category + '.webp'

		# two copies made, one copy is saved in current versions folder, this gets overwritten every week
		img_path_currentfolder = 'image_storage/current_versions/' + img_file_name
		fig.write_image(img_path_currentfolder, format='webp', scale=2)

		# second copy saved in folder with date the data was scraped
		#create folder with yyyy-mm-dd name in image_storage if it doesn't exist
		folder_name = yyyy_mm_dd_string
		folder_path = 'image_storage/' + folder_name
		if not os.path.exists(folder_path):
			os.mkdir(folder_path)
		img_path_datefolder = folder_path + '/' + img_file_name
		# fig.write_image(img_path_datefolder, format='webp', width=1600, height=900,scale=1)
		fig.write_image(img_path_datefolder, format='webp', scale=2)


##################################################################################################
# this function is for sending out tweets

def send_tweets():
	week_start_string = time_one_week_ago.strftime("%b %-d")
	week_end_string = utc_time_now.strftime("%b %-d")
	week_start_end_string = week_start_string + ' - ' + week_end_string

	yyyy_mm_dd_string = utc_time_now.strftime("%Y-%m-%d")
	folder_name = yyyy_mm_dd_string
	folder_path = 'csv_storage/' + folder_name

	first_csv_name = 'politics_pages_most_users_reverted_past_1_week.csv'
	first_csv_path = folder_path + '/' + first_csv_name
	first_csv_df = pd.read_csv(first_csv_path)
	top_politics_page_title = first_csv_df['page_title'].iloc[0]
	top_politics_page_value = str(first_csv_df.iloc[0, 1])

	second_csv_name = 'nonpolitics_pages_most_users_reverted_delta_from_last_week.csv'
	second_csv_path = folder_path + '/' + second_csv_name
	second_csv_df = pd.read_csv(second_csv_path)
	top_delta_nonpolitics_page_title = second_csv_df['page_title'].iloc[0]
	top_delta_nonpolitics_page_value = str(second_csv_df.iloc[0, 1])

	'''
	These are the most vandalised Indian pages on Wikipedia for last week (Dec 4 - Dec 11). Among pages related to politics, the one on '2022 Uttar Pradesh Legislative Assembly election' had the most users with edits reverted last week — 23.
	'''

	first_tweet_text = "These are the most vandalised Indian pages on Wikipedia for last week (" + week_start_end_string + "). Among pages related to politics, the one on '" + top_politics_page_title + "' had the most users with edits reverted last week — " + top_politics_page_value + "."

	'''
	These Indian pages on Wikipedia saw the highest rise in vandalism since last week. Among pages covering topics outside politics, '2022 Uttar Pradesh Legislative Assembly election' had 14 more users with edits reverted compared to last week.
	'''

	second_tweet_text = "These Indian pages on Wikipedia saw the highest rise in vandalism since last week. Among pages covering topics outside politics, '" + top_delta_nonpolitics_page_title + "' had " + top_delta_nonpolitics_page_value +" more users with edits reverted compared to last week."

	first_tweet_image_path = 'image_storage/current_versions/past_1_week.webp'
	second_tweet_image_path = 'image_storage/current_versions/delta_from_last_week.webp'

	first_tweet_image_upload_response = api.media_upload(first_tweet_image_path)
	first_tweet_media_id_string = first_tweet_image_upload_response.media_id_string

	time.sleep(2)	
	second_tweet_image_upload_response = api.media_upload(second_tweet_image_path)
	second_tweet_media_id_string = second_tweet_image_upload_response.media_id_string
	
	first_tweet_update_status = api.update_status(status=first_tweet_text, media_ids = [first_tweet_media_id_string])

	first_tweet_update_status_id_string = first_tweet_update_status._json['id_str']

	time.sleep(2)
	second_tweet_update_status = api.update_status(status=second_tweet_text, 
												media_ids = [second_tweet_media_id_string],
												in_reply_to_status_id = first_tweet_update_status_id_string,
												auto_populate_reply_metadata=True)


################################################################################################
# this function is for sending out email
	# note time started , note time ended, calculate hours for total run

def send_email():
	new_utc_time_now = datetime.now(timezone.utc)
	time_run_ended = new_utc_time_now.strftime("%b %-d %H:%M")
	time_taken_timedelta_object = new_utc_time_now - utc_time_now
	time_taken_timedelta_object_days = time_taken_timedelta_object.days
	time_taken_timedelta_object_seconds = time_taken_timedelta_object.seconds
	hours = (time_taken_timedelta_object_days * 24) + (time_taken_timedelta_object_seconds//3600)
	minutes = (time_taken_timedelta_object_seconds % 3600) // 60
	time_taken_string = str(hours) + ' hours, ' + str(minutes) + ' minutes'

	config_email = configparser.ConfigParser()
	config_email.read('config_email.ini')

	receiver_email = config_email['info']['email'] 
	sender_email = config_email['info']['sender_email'] 
	sender_password = config_email['info']['sender_password'] 

	message = MIMEMultipart()
	message["From"] = sender_email
	message["To"] = receiver_email

	message["Subject"] = "This week's wikipedia run over at " + time_run_ended

	htmlx = "<html>Run is over. Run started at {} and ended at {}, taking {}.</html>".format(time_run_started, time_run_ended, time_taken_string)
	part1 = MIMEText(htmlx, "html")
	message.attach(part1)

	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.ehlo()
	s.starttls() 
	s.login(sender_email, sender_password)
	s.sendmail(sender_email, receiver_email, message.as_string()) 
	s.quit()
