#!/usr/bin/python3

import json
import os
import time
import requests
from datetime import datetime,timezone
from dateutil.relativedelta import relativedelta
from dateutil import parser
import copy
from collections import defaultdict
import random
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
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

time_run_started = utc_time_now.strftime("%b %-d, %H:%M") # eg. Dec 15, 15:00

time_one_month_ago = utc_time_now - relativedelta(months=1)
time_one_month_ago_string = time_one_month_ago.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

time_two_weeks_ago = utc_time_now - relativedelta(weeks=2)

time_one_week_ago = utc_time_now - relativedelta(weeks=1)

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

# this is for whenever twitter's api v2 introduces endpoint for uploading images, then we'll switch to v2 from v1.1
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

delay = random.choice([0.6, 0.7, 0.8, 0.9])
time.sleep(delay)			
response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
data = response.json()
combined_users = copy.deepcopy(data)

while 'continue' in data:
	delay = random.choice([0.6, 0.7, 0.8, 0.9])
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


########################################################################
# code for updating page ids from a wikiproject

def update_wikiproject_page_ids(category_list, categorised_file_name, merged_file_name, new_category_members):
	#new_category_members will be an empty dict

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
		cmend = utc_time_now_string_in_file

	else:
		loaded_page_ids_categorised_json = {'pages':{}}
		for category in category_list:
			loaded_page_ids_categorised_json['pages'][category] = {}

		cmend = '2001-01-01T00:00:00Z' #putting cmend at Jan 1, 2001. Wikipedia started Jan 15, 2001, so Jan 1, 2001 should be fine

	# this will get talk pages for articles that have wikiproject india tag in their code
	# you have to convert the talk ids you receive into parent ids and then add them to existing file

	for category in category_list:
		params = {
				'action': 'query',
				'format': 'json',
				'list':'categorymembers',
				'cmtitle': category,
				'cmprop': 'ids|title|timestamp',
				'cmlimit': 500,
				'cmstart': utc_time_now_string,
				'cmend': cmend,
				'cmdir': 'older',
				'cmnamespace': '0|1',
				'cmsort': 'timestamp'
				}

		combined_category_members = []

		delay = random.choice([0.6, 0.7, 0.8, 0.9])
		time.sleep(delay)
		
		response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
		data = response.json()
		category_members = data['query']['categorymembers']
		combined_category_members.extend(category_members)

		while 'continue' in data:
			params.update(data['continue'])
			delay = random.choice([0.6, 0.7, 0.8, 0.9])
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
			delay = random.choice([0.6, 0.7, 0.8, 0.9])
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

def grab_page_histories(pages_dict):

	page_ids_for_deletion = []

	for page_id, page_title in pages_dict.items():

		page_history_filename = page_id + '_page_history.json'
		page_history_filepath = 'page_histories/' + page_history_filename

		combined_pagerevisions = {
								'page_id': page_id,
								'page_title': page_title,
								'utc_time_now_string': utc_time_now_string,
								'pagerevisions_list':[]
								}
		page_revisions_endpoint = time_one_month_ago_string
		
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

		delay = random.choice([0.6, 0.7, 0.8, 0.9])
		time.sleep(delay)
		response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
		data = response.json()
		try:
			pagerevisions = data['query']['pages'][page_id]['revisions']
			combined_pagerevisions['pagerevisions_list'].extend(pagerevisions)
		except: # need this in case of redirects, the page_ids wont match
			page_ids_for_deletion.append(page_id)
			continue

		while 'continue' in data:
			delay = random.choice([0.6, 0.7, 0.8, 0.9])
			time.sleep(delay)
			params.update(data['continue'])
			response = http.get(api_url, headers=headers, params=params, timeout=(10, 20))
			data = response.json()
			try:
				pagerevisions = data['query']['pages'][page_id]['revisions']
				combined_pagerevisions['pagerevisions_list'].extend(pagerevisions)
			except:
				page_ids_for_deletion.append(page_id)
				break

		with open(page_history_filepath, 'w', encoding='utf-8') as filex:
			json.dump(combined_pagerevisions, filex, ensure_ascii=False)
		
	for page_idx in page_ids_for_deletion:
		del pages_dict[page_idx] #deleting page ids which are being redirected, redirects will already be there

#########################################################
# code to get aggregate stats for graphics
	#analysis of the pages over last week, last month (most users reverted)

def compile_stats(pages_dict, saved_to_disk_filename):

	field_list = [
			'number of users reverted in past 1 month',
			'number of users reverted in past 2 weeks',
			'number of users reverted in past 1 week',
			]

	tree = lambda: defaultdict(tree)
	page_histories_analysis_dict = tree()

	for page_id, page_title in pages_dict.items():

		page_history_filename = page_id + '_page_history.json'
		page_history_filepath = 'page_histories/' + page_history_filename

		opened_page_history_json = open(page_history_filepath)
		loaded_page_history_json = json.load(opened_page_history_json)

		pagerevisions_list = loaded_page_history_json['pagerevisions_list']

		users_reverted_past_1_month = []
		users_reverted_past_2_weeks = []
		users_reverted_past_1_week = []

		page_histories_analysis_dict[page_id]['page_title'] = page_title
		for field in field_list:	
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

					if revision_timestamp >= time_one_month_ago:
						if user_name not in users_reverted_past_1_month: users_reverted_past_1_month.append(user_name)

					if revision_timestamp >= time_two_weeks_ago:
						if user_name not in users_reverted_past_2_weeks: users_reverted_past_2_weeks.append(user_name)

					if revision_timestamp >= time_one_week_ago:
						if user_name not in users_reverted_past_1_week: users_reverted_past_1_week.append(user_name)

		page_histories_analysis_dict[page_id]['number of users reverted in past 1 month'] = len(users_reverted_past_1_month)
		page_histories_analysis_dict[page_id]['number of users reverted in past 2 weeks'] = len(users_reverted_past_2_weeks)
		page_histories_analysis_dict[page_id]['number of users reverted in past 1 week'] = len(users_reverted_past_1_week)

	saved_to_disk_filepath = 'analysis_files/' + saved_to_disk_filename
	with open(saved_to_disk_filepath, 'w', encoding='utf-8') as filex:
		json.dump(page_histories_analysis_dict, filex, ensure_ascii=False)


######################################################################################
# this function below is for creating csvs with for last week, last 2 weeks etc.

def create_csvs(compiled_stats_source_name, category, datetime_object):

	merged_df_columns = [
						'page_id', 
						'page_title',
						'users_reverted_past_1_month',
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
				'users_reverted_past_1_month': loaded_compiled_stats_json[page_id]['number of users reverted in past 1 month'],
				'users_reverted_past_2_weeks': loaded_compiled_stats_json[page_id]['number of users reverted in past 2 weeks'],
				'users_reverted_past_1_week': loaded_compiled_stats_json[page_id]['number of users reverted in past 1 week']
				}, ignore_index=True)
	
	merged_df['users_reverted_week_before_last'] = merged_df['users_reverted_past_2_weeks'] - merged_df['users_reverted_past_1_week']
	merged_df['change_from_last_week'] = merged_df['users_reverted_past_1_week'] - merged_df['users_reverted_week_before_last']

	yyyy_mm_dd_string = datetime_object.strftime("%Y-%m-%d")
	folder_name = yyyy_mm_dd_string
	folder_path = 'csv_storage/' + folder_name
	if not os.path.exists(folder_path):
		os.mkdir(folder_path)

	merged_df.sort_values(by=['users_reverted_past_1_week','users_reverted_past_2_weeks','users_reverted_past_1_month'],
							ascending=[False,False,False], inplace=True)
	df_culled = merged_df[['page_title', 'users_reverted_past_1_week']].head(10)
	df_culled_filepath = folder_path + '/' + category + '_pages_most_users_reverted_past_1_week.csv'
	df_culled.to_csv(df_culled_filepath, index=False, encoding='utf-8')

	merged_df.sort_values(by=['users_reverted_past_1_month'],
							ascending=[False], inplace=True)
	df_culled = merged_df[['page_title', 'users_reverted_past_1_month']].head(10)
	df_culled_filepath = folder_path + '/' + category + '_pages_most_users_reverted_past_1_month.csv'
	df_culled.to_csv(df_culled_filepath, index=False, encoding='utf-8')

	merged_df.sort_values(by=['change_from_last_week','users_reverted_past_1_week','users_reverted_past_2_weeks','users_reverted_past_1_month'],
						ascending=[False,False,False,False], inplace=True)
	df_culled = merged_df[['page_title', 'change_from_last_week']].head(10)
	df_culled_filepath = folder_path + '/' + category + '_pages_most_users_reverted_delta_from_last_week.csv'
	df_culled.to_csv(df_culled_filepath, index=False, encoding='utf-8')


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
										'chart_title': '<b>Indian pages on Wikipedia facing highest rise in abuse*<b>',
										},
					'past_1_month': 	{
										'chart_title': '<b>Most abused* Indian pages on Wikipedia over past 1 month<b>',
										},						
					'past_1_week': 		{
										'chart_title': '<b>Most abused* Indian pages on Wikipedia last week<b>',
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

			subcategory_df_raw['combined'] = subcategory_df_raw['rank'].astype(str) + '. ' +subcategory_df_raw['truncated_page_title'] +' (' +	subcategory_df_raw.iloc[:, 1].astype(str) + ')'
			subcategory_df = subcategory_df_raw[['combined']]

			subcategory_df_page_titles = subcategory_df['combined'].tolist()[0:5]

			if subcategory == 'politics':
				header_text = 'Politics Pages'
			else:
				header_text = 'Non-Politics Pages'

			fig.add_trace(
				go.Table(
					header=dict(
								values=[header_text], 
								fill_color='white',
								line_color=table_line_color,
								line_width = table_line_width,
								align=['center'],
								font=dict(
										color='black', 
										size=body_copy_font_size,
										family=font_family,
										),
								height=28
								),
					cells=dict(
								values=[subcategory_df_page_titles],
								fill_color='white',
								line_color=table_line_color,
								line_width = table_line_width,
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


		updated_date = utc_time_now.strftime("%b %-d, %Y")

		if category == 'delta_from_last_week':
			explanation_string = "*Abuse here is measured by the growth since last week in users (no. in<br> brackets) whose edits are reverted on a page. Data as on " + updated_date
		else:
			explanation_string = "*Abuse here is measured by the number of users (figure in brackets)<br> whose edits are reverted on a page. Data as on " + updated_date

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
		fig.write_image(img_path_datefolder, format='webp', scale=2)

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
										'chart_title': '<b>Indian pages on Wikipedia facing highest rise in abuse*<b>',
										},
					'past_1_month': 	{
										'chart_title': '<b>Most abused* Indian pages on Wikipedia over past 1 month<b>',
										},						
					'past_1_week': 		{
										'chart_title': '<b>Most abused* Indian pages on Wikipedia last week<b>',
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
			explanation_string = "*Abuse here is measured by the growth since last week in users (figure in brackets)<br> whose edits are reverted on a page. Data as on " + updated_date
		else:
			explanation_string = "*Abuse here is measured by the number of users (figure in brackets) whose edits<br> are reverted on a page. Data as on " + updated_date

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

		img_file_name = category + '.svg'
		img_path_currentfolder = 'image_storage/2021_overview_images/' + img_file_name
		fig.write_image(img_path_currentfolder, format='svg', scale=2)


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
	These are the most abused Indian pages on Wikipedia for last week (Dec 4 - Dec 11). Among pages related to politics, the one on '2022 Uttar Pradesh Legislative Assembly election' had the most users with edits reverted last week — 23.
	'''

	first_tweet_text = "These are the most abused Indian pages on Wikipedia for last week (" + week_start_end_string + "). Among pages related to politics, the one on '" + top_politics_page_title + "' had the most users with edits reverted last week — " + top_politics_page_value + "."

	'''
	These Indian pages on Wikipedia saw the highest rise in abuse since last week. Among pages covering topics outside politics, '2022 Uttar Pradesh Legislative Assembly election' had 14 more users with edits reverted compared to last week.
	'''

	second_tweet_text = "These Indian pages on Wikipedia saw the highest rise in abuse since last week. Among pages covering topics outside politics, '" + top_delta_nonpolitics_page_title + "' had " + top_delta_nonpolitics_page_value +" more users with edits reverted compared to last week."

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
	# note time started , note time ended, calculate hours for total run, put that in mail

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

