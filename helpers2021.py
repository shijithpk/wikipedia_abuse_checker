#!/usr/bin/env python3

import json
import os
import time
import requests
from dateutil import parser
import copy
from collections import defaultdict
import random
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

reverted_tags_list = ['mw-reverted']
reverting_tags_list = ['mw-undo','mw-rollback','mw-manual-revert']

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

utc_time_now_string = "2021-12-01T00:00:00Z"
utc_time_now = dec_1

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
page_history_filename_list = os.listdir("page_histories_2021_v2")

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
		cmend = '2001-01-01T00:00:00Z' #putting a cmend at Jan 1, 2001. Wikipedia started Jan 15, 2001
		for category in category_list:
			loaded_page_ids_categorised_json['pages'][category] = {}

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
		page_history_filepath = 'page_histories_2021_v2/' + page_history_filename

		if page_history_filename in page_history_filename_list:
			page_history_json = open(page_history_filepath)
			combined_pagerevisions = json.load(page_history_json)
			utc_time_now_string_in_file = combined_pagerevisions['utc_time_now_string']
			page_revisions_endpoint = utc_time_now_string_in_file
			combined_pagerevisions['utc_time_now_string'] = utc_time_now_string

		else:
			combined_pagerevisions = {
									'page_id': page_id,
									'page_title': page_title,
									'utc_time_now_string': utc_time_now_string,
									'pagerevisions_list':[]
									}
			page_revisions_endpoint = "2021-01-01T00:00:00Z" #Jan 1, 2021 12 am UTC. Not IST but wont make much difference
		
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
		del pages_dict[page_idx] #deleting page ids which are being redirected, redirects have already been added

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
		page_history_filepath = 'page_histories_2021_v2/' + page_history_filename

		try:
			opened_page_history_json = open(page_history_filepath)
		except:
			print('this page title {} with this page id {} not there in page_histories_2021_v2'.format(page_title, page_id))
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
# this function below is for creating month-wise CSVs for 2021 overview

def create_monthly_stats_csvs():
	category_list = ['politics','nonpolitics']
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
			# df_culled = merged_df[['page_title', field_column_name]].head(10)
			df_culled = merged_df[['page_title', field_column_name]].head(60)
			df_culled_filepath = folder_path + '/' + field_csv_name
			df_culled.to_csv(df_culled_filepath, index=False, encoding='utf-8')


######################################################################################################
# this function is for creating graphics for 2021 overview in blog color theme -- top 10 for the year

def create_charts_top_10():

	font_family = 'Rubik'
	chart_title_font_size = 25
	explanation_string_font_size = 22
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

		category_df_raw['combined'] = '<b>'+ category_df_raw['rank'].astype(str) + '.</b> ' + category_df_raw['truncated_page_title'] +' (' +	category_df_raw.iloc[:, 1].astype(str) + ')'

		category_df = category_df_raw[['combined']]

		category_df_page_titles = category_df['combined'].head(10).tolist() # including all 10 titles

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

	explanation_string = "*Abuse here is the number of users (figure in brackets) whose<br>edits have been reverted on a page from Jan-Nov 2021."

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
				text = '<b>Most abused* Indian pages on Wikipedia in 2021<b>',
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

	img_file_name = '2021_top_10.svg'
	folder_name = '2021_overview_images'
	folder_path = 'image_storage/' + folder_name
	img_path_datefolder = folder_path + '/' + img_file_name
	fig.write_image(img_path_datefolder, format='svg', scale=2)


######################################################################################################
# this function is for creating graphics for 2021 overview in blog color theme -- month-wise top 3 pages

def create_charts_monthly_top_titles():
	font_family = 'Rubik'
	chart_title_font_size = 30
	explanation_string_font_size = 20
	body_copy_font_size = 20
	table_line_width = 1
	table_line_color = '#444444'
	cell_height_table_header = 20 # doesnt matter, plotly doesnt follow it, uses the height that will fit the text in
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

			category_df_page_titles = category_df['combined'].tolist()[0:3]

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

		explanation_string = "*Abuse here is the number of users (figure in brackets) whose<br>edits have been reverted on a page for that month."

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
					text = '<b>Most abused* Indian<br>pages on Wikipedia for<br>every month of 2021<br>' + title_substring + '<b>',
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
		folder_name = '2021_overview_images'
		folder_path = 'image_storage/' + folder_name
		if not os.path.exists(folder_path):
			os.mkdir(folder_path)
		img_path_datefolder = folder_path + '/' + img_file_name
		fig.write_image(img_path_datefolder, format='webp', scale=2)

		img_file_name = category + '_2021_monthly_top_pages.svg'
		folder_name = '2021_overview_images'
		folder_path = 'image_storage/' + folder_name
		img_path_datefolder = folder_path + '/' + img_file_name
		fig.write_image(img_path_datefolder, format='svg', scale=2)

######################################################################################################
# this function is for creating graphics for 2021 overview in blog color theme -- month-wise top 3 pages, no cricket and no movies

def create_charts_monthly_top_titles_no_movies_tv_sports():
	font_family = 'Rubik'
	chart_title_font_size = 30
	explanation_string_font_size = 20
	body_copy_font_size = 20
	table_line_width = 1
	table_line_color = '#444444'
	cell_height_table_header = 20 # doesnt matter, plotly doesnt follow it, uses the height that will fit the text in
	cell_height_table_body = 25
	copy_font_color = '#444444'
	background_color = '#e1e1e1'
	highlight_color = '#ff652f'

	category_list = ['nonpolitics']

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
			category_df_raw_with_cricket_movies = pd.read_csv(csv_path)
			category_df_raw = category_df_raw_with_cricket_movies[category_df_raw_with_cricket_movies['interesting']=='YES']
			category_df_raw['rank'] = range(1,1+len(category_df_raw))
			category_df_raw['truncated_page_title'] = category_df_raw['page_title'].apply(
				lambda x: x if len(x) <= 50 else (x[0:47] + '...')
			)

			category_df_raw['combined'] = '<b>'+ category_df_raw['rank'].astype(str) + '.</b> ' + category_df_raw['truncated_page_title'] +' (' +	category_df_raw.iloc[:, 1].astype(str) + ')'

			category_df = category_df_raw[['combined']]

			category_df_page_titles = category_df['combined'].tolist()[0:3]

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

		explanation_string = "*Abuse here is the number of users (figure in brackets) whose<br>edits have been reverted on a page for that month."

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
			title_substring = '(Outside politics, movies, tv & sports)'
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
					text = '<b>Most abused* Indian<br>pages on Wikipedia for<br>every month of 2021<br>' + title_substring + '<b>',
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

		img_file_name = category + '_2021_monthly_top_pages_no_movies_tv_sports.webp'
		folder_name = '2021_overview_images'
		folder_path = 'image_storage/' + folder_name
		if not os.path.exists(folder_path):
			os.mkdir(folder_path)
		img_path_datefolder = folder_path + '/' + img_file_name
		fig.write_image(img_path_datefolder, format='webp', scale=2)

		img_file_name = category + '_2021_monthly_top_pages_no_movies_tv_sports.svg'
		folder_name = '2021_overview_images'
		folder_path = 'image_storage/' + folder_name
		img_path_datefolder = folder_path + '/' + img_file_name
		fig.write_image(img_path_datefolder, format='svg', scale=2)


