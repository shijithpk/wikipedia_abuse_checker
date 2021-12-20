#!/usr/bin/python3

# import os, sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from helpersWeekly import *

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

grab_page_histories(pages_dict_politics) 
grab_page_histories(pages_dict_nonpolitics)

loaded_page_id_dict['pages']['politics'] = pages_dict_politics
loaded_page_id_dict['pages']['nonpolitics'] = pages_dict_nonpolitics 

with open(page_id_dict_file_path, 'w', encoding='utf-8') as filex:
	json.dump(loaded_page_id_dict, filex, ensure_ascii=False)

# # this is for when you want to start from the page_id_dict file without updating category members or redownloading page histories
# page_id_dict_file_name = 'page_id_dict_all_start_no_growth.json'
# page_id_dict_file_path = 'analysis_files/' + page_id_dict_file_name
# opened_page_id_dict = open(page_id_dict_file_path)
# loaded_page_id_dict = json.load(opened_page_id_dict)
# pages_dict_politics = loaded_page_id_dict['pages']['politics']
# pages_dict_nonpolitics = loaded_page_id_dict['pages']['nonpolitics']

# compile stats
compile_stats(pages_dict_nonpolitics, 'compiled_stats_last_week_nonpolitics.json')
compile_stats(pages_dict_politics, 'compiled_stats_last_week_politics.json')

# make csvs
create_csvs('compiled_stats_last_week_politics.json', 'politics', utc_time_now)
create_csvs('compiled_stats_last_week_nonpolitics.json', 'nonpolitics', utc_time_now)

# make charts
create_charts_for_twitter()

# this is to make graphics for last week in blog color theme
create_charts_blog_style()

# tweet out charts
send_tweets()

# send email with info on when the run finished and how long it took
send_email()
