#!/usr/bin/env python3

import json
import pandas as pd
from datetime import datetime,timezone
import os

utc_time_now = datetime.now(timezone.utc)

def create_csvs(compiled_stats_source_name, category, datetime_object):
	# fields_of_interest = [		
	# 		'number of users reverted in past year',
	# 		'number of users reverted in past 6 months',
	# 		'number of users reverted in past 3 months',
	# 		'number of users reverted in past 1 month',
	# 		'number of users reverted in past 4 weeks',
	# 		'number of users reverted in past 2 weeks',
	# 		'number of users reverted in past 1 week'
	# ]

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

create_csvs('changed_compile_file.json', 'politics', utc_time_now)