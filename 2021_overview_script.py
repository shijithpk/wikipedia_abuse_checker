#!/usr/bin/env python3

from .helpers import *

file_path = 'analysis_files/page_id_dict_all_start_no_growth.json' 
opened_json = open(file_path)
loaded_json = json.load(opened_json)
pages_dict_politics = loaded_json['pages']['politics']
pages_dict_nonpolitics = loaded_json['pages']['nonpolitics']

# compile month-wise stats for 2021 overview

saved_to_disk_filename_politics = 'compiled_monthly_stats_politics.json'
compile_stats_monthly(pages_dict_politics, saved_to_disk_filename_politics)

saved_to_disk_filename_nonpolitics = 'compiled_monthly_stats_nonpolitics.json'
compile_stats_monthly(pages_dict_nonpolitics, saved_to_disk_filename_nonpolitics)


# now to create csvs based on these compiled stats for recent weeks and 2021 overview

create_csvs('compiled_stats_all_start_no_growth_politics.json', 'politics', utc_time_now)
create_csvs('compiled_stats_all_start_no_growth_nonpolitics.json', 'nonpolitics', utc_time_now)

create_monthly_stats_csvs()

# now for creation of graphics from these csvs
	# graphics for 2021 overview
	# as well as graphics for last week & recent past in blog color theme

create_charts_blog_style()
create_charts_top_10()
create_charts_monthly_top_titles()
