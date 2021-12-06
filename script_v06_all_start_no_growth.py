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

reverted_tags_list = ['mw-reverted']
reverting_tags_list = ['mw-undo','mw-rollback','mw-manual-revert']

utc_time_now = datetime.now(timezone.utc)
utc_time_now_string = utc_time_now.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

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

delay = random.choice([0.4, 0.5, 0.6])
time.sleep(delay)			
response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
data = response.json()
combined_users = copy.deepcopy(data)

while 'continue' in data:
	delay = random.choice([0.4, 0.5, 0.6])
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
		delay = random.choice([0.4, 0.5, 0.6])
		time.sleep(delay)
		response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
		data = response.json()

		category_members = data['query']['categorymembers']
		combined_category_members.extend(category_members)

		while 'continue' in data:
			params.update(data['continue'])
			delay = random.choice([0.4, 0.5, 0.6])
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
			delay = random.choice([0.4, 0.5, 0.6])
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

			delay = random.choice([0.4, 0.5, 0.6])
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

		delay = random.choice([0.4, 0.5, 0.6])
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
			delay = random.choice([0.4, 0.5, 0.6])
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

########################################################################################
# finally calling the functions, repeating loop till target number of pages reached
	# def compile_stats(pages_dict, saved_to_disk_filename):

category_list_indian_politics = ['Category:FA-Class_Indian_politics_articles',
								'Category:A-Class_Indian_politics_articles',
								'Category:GA-Class_Indian_politics_articles',
								'Category:B-Class_Indian_politics_articles',
								'Category:C-Class_Indian_politics_articles',
								'Category:Start-Class_Indian_politics_articles',
								'Category:Stub-Class_Indian_politics_articles'
								]
categorised_file_name_indian_politics = 'wikiproject_page_ids_categorised_indian_politics.json'
merged_file_name_indian_politics = 'wikiproject_page_ids_merged_indian_politics.json'
new_category_members_indian_politics = {}

update_wikiproject_page_ids(category_list_indian_politics, categorised_file_name_indian_politics, merged_file_name_indian_politics, new_category_members_indian_politics)

category_list_india = ['Category:FA-Class_India_articles',
					'Category:A-Class_India_articles',
					'Category:GA-Class_India_articles',
					'Category:B-Class_India_articles',
					'Category:C-Class_India_articles',
					'Category:Start-Class_India_articles',
					'Category:Stub-Class_India_articles'
					]
categorised_file_name_india = 'wikiproject_page_ids_categorised.json'
merged_file_name_india = 'wikiproject_page_ids_merged.json'
new_category_members_india = {}

update_wikiproject_page_ids(category_list_india, categorised_file_name_india, merged_file_name_india, new_category_members_india)

page_id_dict_file_name = 'page_id_dict_all_start_no_growth.json'
page_id_dict_file_path = 'analysis_files/' + page_id_dict_file_name

if page_id_dict_file_name in analysis_files_filename_list:
	opened_page_id_dict = open(page_id_dict_file_path)
	loaded_page_id_dict = json.load(opened_page_id_dict)
else:
	loaded_page_id_dict = {'pages':{'politics':{},
									'nonpolitics':{}
									}
									}
	merged_file_path_indian_politics = 'analysis_files/' + merged_file_name_indian_politics
	opened_wikiproject_page_ids_merged_indian_politics_json = open(merged_file_path_indian_politics)
	loaded_wikiproject_page_ids_merged_indian_politics_json = json.load(opened_wikiproject_page_ids_merged_indian_politics_json)
	wikiproject_page_ids_merged_indian_politics = loaded_wikiproject_page_ids_merged_indian_politics_json['pages']

	merged_file_path_india = 'analysis_files/' + merged_file_name_india
	opened_wikiproject_page_ids_merged_india_json = open(merged_file_path_india)
	loaded_wikiproject_page_ids_merged_india_json = json.load(opened_wikiproject_page_ids_merged_india_json)
	wikiproject_page_ids_merged_india = loaded_wikiproject_page_ids_merged_india_json['pages']

	wikiproject_page_ids_merged_indian_nonpolitics = copy.deepcopy(wikiproject_page_ids_merged_india)
	for page_id in wikiproject_page_ids_merged_indian_politics:
		wikiproject_page_ids_merged_indian_nonpolitics.pop(page_id, None)

	loaded_page_id_dict['pages']['politics'] = wikiproject_page_ids_merged_indian_politics
	loaded_page_id_dict['pages']['nonpolitics'] = wikiproject_page_ids_merged_indian_nonpolitics

pages_dict_politics = loaded_page_id_dict['pages']['politics']
pages_dict_nonpolitics = loaded_page_id_dict['pages']['nonpolitics']

pages_dict_politics.update(new_category_members_indian_politics)

new_category_members_nonpolitics = copy.deepcopy(new_category_members_india)
new_category_members_nonpolitics_key_list = list(new_category_members_nonpolitics.keys())
for page_id in new_category_members_nonpolitics_key_list:
	if page_id in pages_dict_politics:
		del new_category_members_nonpolitics[page_id]

pages_dict_nonpolitics.update(new_category_members_nonpolitics)

# some entries dont exist anymore, this will help in adding pages they are redirected to
pages_dict_for_addition = {}
# if there are redirects, they get added to pages_dict_for_addition
grab_page_histories(pages_dict_politics, pages_dict_for_addition) 
if len(pages_dict_for_addition) > 0:
	pages_dict_politics.update(pages_dict_for_addition)
	grab_page_histories(pages_dict_politics, pages_dict_for_addition) 
	# grabs page histories of redirects, but looping over page ids twice is very inefficient, need better method

pages_dict_for_addition = {}
grab_page_histories(pages_dict_nonpolitics, pages_dict_for_addition)
if len(pages_dict_for_addition) > 0:
	pages_dict_nonpolitics.update(pages_dict_for_addition)
	grab_page_histories(pages_dict_nonpolitics, pages_dict_for_addition)

compile_stats(pages_dict_nonpolitics, 'compiled_stats_all_start_no_growth_nonpolitics.json')
compile_stats(pages_dict_politics, 'compiled_stats_all_start_no_growth_politics.json')

loaded_page_id_dict['pages']['politics'] = pages_dict_politics
loaded_page_id_dict['pages']['nonpolitics'] = pages_dict_nonpolitics 

with open(page_id_dict_file_path, 'w', encoding='utf-8') as filex:
	json.dump(loaded_page_id_dict, filex, ensure_ascii=False)

# /home/ubuntu/work/wikipedia_sanghis/script_v05_all_start_no_growth.py

# line for cron and at jobs
	# cd /home/ubuntu/work/wikipedia_sanghis && /usr/bin/python3 ./script_v06_all_start_no_growth.py >> /home/ubuntu/work/wikipedia_sanghis/logs/`date +\%Y-\%m-\%d-\%H:\%M`_script_v06_all_start_no_growth.log 2>&1
