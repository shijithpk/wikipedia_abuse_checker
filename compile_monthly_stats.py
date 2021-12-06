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

saved_to_disk_filename = 'compiled_monthly_stats.json'

bot_id_dict_filepath = 'analysis_files/bot_id_list_trial.json'
opened_bot_id_dict_json = open(bot_id_dict_filepath)
loaded_bot_id_dict_json = json.load(opened_bot_id_dict_json)
bot_id_list = loaded_bot_id_dict_json['bot_id_list']

merged_file_path_indian_politics = 'analysis_files/wikiproject_page_ids_merged_indian_politics.json' 
opened_wikiproject_page_ids_merged_indian_politics_json = open(merged_file_path_indian_politics)
loaded_wikiproject_page_ids_merged_indian_politics_json = json.load(opened_wikiproject_page_ids_merged_indian_politics_json)
pages_dict = loaded_wikiproject_page_ids_merged_indian_politics_json['pages']

def compile_stats(pages_dict, saved_to_disk_filename):

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
			'number of users reverted in Nov 2021']

	tree = lambda: defaultdict(tree)
	page_histories_analysis_dict = tree()

	for page_id, page_title in pages_dict.items():

		page_history_filename = page_id + '_page_history.json'
		page_history_filepath = 'page_histories/' + page_history_filename

		# try:
		# 	opened_page_history_json = open(page_history_filepath)
		# except:
		# 	continue

		opened_page_history_json = open(page_history_filepath)
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

compile_stats(pages_dict, saved_to_disk_filename)