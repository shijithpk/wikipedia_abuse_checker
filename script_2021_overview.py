#!/usr/bin/python3

from helpers2021 import *

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

# # # this is for when you just when to start from the page_id_dict file without updating the category members first
# # file_path = 'analysis_files/page_id_dict_all_start_no_growth.json' 
# # opened_json = open(file_path)
# # loaded_json = json.load(opened_json)
# # pages_dict_politics = loaded_json['pages']['politics']
# # pages_dict_nonpolitics = loaded_json['pages']['nonpolitics']
# # grab_page_histories(pages_dict_politics)
# # grab_page_histories(pages_dict_nonpolitics)

loaded_page_id_dict['pages']['politics'] = pages_dict_politics
loaded_page_id_dict['pages']['nonpolitics'] = pages_dict_nonpolitics

with open(page_id_dict_file_path, 'w', encoding='utf-8') as filex:
	json.dump(loaded_page_id_dict, filex, ensure_ascii=False)

# compile month-wise stats for 2021 overview
saved_to_disk_filename_politics = 'compiled_monthly_stats_politics.json'
compile_stats_monthly(pages_dict_politics, saved_to_disk_filename_politics)

saved_to_disk_filename_nonpolitics = 'compiled_monthly_stats_nonpolitics.json'
compile_stats_monthly(pages_dict_nonpolitics, saved_to_disk_filename_nonpolitics)

# now to create csvs based on these compiled stats for 2021 overview
create_monthly_stats_csvs()

# hate that I had to this but added a column to a csv by hand here
	#was marking out which entries have nothing to do with politics, movies, TV and sports

# now for creation of graphics from these csvs
# 	graphics for 2021 overview
create_charts_top_10()
create_charts_monthly_top_titles()
create_charts_monthly_top_titles_no_movies_tv_sports()
