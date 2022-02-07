#!/usr/bin/python3

import json
import pandas as pd

# grouping pages based on which wikiprojects they're associated with
wikiproject_grouping_dict = {
							'religion':{
										'all_of_these':[],
										'one_of_these':["Religion","Mythology","Hinduism","Islam","Christianity","Sikhism","Buddhism","Jainism","Zoroastrianism","Judaism",],
										'none_of_these':["Biography"],
										'page_id_list':[],
										},
							'thinkers':{
										'all_of_these':["Biography",
														"Philosophy",
														],
										'one_of_these':[# "Hinduism","Islam","Christianity","Sikhism","Buddhism",					"Jainism","Judaism", 
														# "Socialism",
														# "Conservatism",
														# "Sociology",
														# 'Alternative Views',
														# 'Libertarianism',
														# 'Atheism',
														# 'Human rights',
														# 'Politics',
														],
										'none_of_these':[],
										'page_id_list':[],
							},
							'historical_figures':{
										'all_of_these':["Biography","India/Indian history workgroup"],
										'one_of_these':[],
										'none_of_these':[],
										'page_id_list':[],
							},
							'historical_incidents':{
										'all_of_these':["India/Indian history workgroup"],
										'one_of_these':[],
										'none_of_these':["Biography"],
										'page_id_list':[],
							},
							'food_and_drink':{
										'all_of_these':["Food and drink"],
										'one_of_these':[],
										'none_of_these':["Biography"],
										'page_id_list':[],
							},
							'celebrities':{
										'all_of_these':["Biography"],
										'one_of_these':[],
										'none_of_these':["India/Indian history workgroup"],
										'page_id_list':[],
							}
							}


category_collection_json_filepath = 'analysis_files/category_collections_joined.json'

opened_file = open(category_collection_json_filepath)
category_collection_json_dict = json.load(opened_file)
category_collection_json_keys_list = list(category_collection_json_dict['pages'].keys())
for page_id in category_collection_json_keys_list:
	page_title = category_collection_json_dict['pages'][page_id]['page_title']
	category_list = category_collection_json_dict['pages'][page_id]['category_list']
	if category_list:
		for grouping in wikiproject_grouping_dict:
			all_of_these_wikiprojects = wikiproject_grouping_dict[grouping]['all_of_these']
			one_of_these_wikiprojects = wikiproject_grouping_dict[grouping]['one_of_these']
			none_of_these_wikiprojects = wikiproject_grouping_dict[grouping]['none_of_these']
			if (
				(all(item in category_list for item in all_of_these_wikiprojects) if all_of_these_wikiprojects else True) and \
				(any(item in category_list for item in one_of_these_wikiprojects) if one_of_these_wikiprojects else True) and \
				((not any(item in category_list for item in none_of_these_wikiprojects)) if none_of_these_wikiprojects else True)
				):
				wikiproject_grouping_dict[grouping]['page_id_list'].append(page_id)

wikiproject_grouping_dict_file_path = 'analysis_files/wikiproject_grouping.json'
with open(wikiproject_grouping_dict_file_path, 'w', encoding='utf-8') as filex:
	json.dump(wikiproject_grouping_dict, filex, ensure_ascii=False)

# # now compile stats for page ids falling under each wikiproject grouping

compiled_monthly_stats_politics_filepath = 'analysis_files/compiled_monthly_stats_politics.json'
opened_monthly_stats_politics = open(compiled_monthly_stats_politics_filepath)
loaded_monthly_stats_politics = json.load(opened_monthly_stats_politics)

compiled_monthly_stats_nonpolitics_filepath = 'analysis_files/compiled_monthly_stats_nonpolitics.json'
opened_monthly_stats_nonpolitics = open(compiled_monthly_stats_nonpolitics_filepath)
loaded_monthly_stats_nonpolitics = json.load(opened_monthly_stats_nonpolitics)

# CHECK IF THERE ARE IDS COMMON TO ALL THREE LISTS
	# pretty sure gandhi will be in historical figures and thinkers 

for grouping in wikiproject_grouping_dict:
	df_for_saving = pd.DataFrame(columns=['page_id','page_title','users_reverted_2021'])
	page_id_list = wikiproject_grouping_dict[grouping]['page_id_list']
	for page_id in page_id_list:
		# if page_id in loaded_monthly_stats_politics:
		try:
			users_reverted_jan_to_dec_for_page = loaded_monthly_stats_politics[page_id]['number of users reverted Jan to Dec 2021']
		except:
			try:
				users_reverted_jan_to_dec_for_page = loaded_monthly_stats_nonpolitics[page_id]['number of users reverted Jan to Dec 2021']
			except:
				continue
		page_title = category_collection_json_dict['pages'][page_id]['page_title']
		df_for_saving = df_for_saving.append({
											'page_id': page_id,
											'page_title': page_title,
											'users_reverted_2021': users_reverted_jan_to_dec_for_page,
											}, ignore_index=True)

	df_for_saving.sort_values(by=['users_reverted_2021'], ascending=[False], inplace=True)
	df_for_saving_top_60 = df_for_saving.head(60)
	df_for_saving_top_60_filepath = 'csv_storage/2021_stats/' + grouping + '_most_users_reverted_2021.csv'
	df_for_saving_top_60.to_csv(df_for_saving_top_60_filepath, index=False, encoding='utf-8')
