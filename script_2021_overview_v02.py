#!/usr/bin/python3

from helpers_v03 import *

jan_1_2022_string = "2022-01-01T00:00:00+0530"

update_json_of_page_ids(jan_1_2022_string)

page_histories_directory = 'page_histories_2021_v3'

grab_page_histories_whole_year(jan_1_2022_string, page_histories_directory)

# compile month-wise stats for 2021 overview
compile_stats_monthly(page_histories_directory)

# now to create csvs based on these compiled stats for 2021 overview
create_monthly_stats_csvs()

# hate that I had to this but added a column to a csv by hand here
	#was marking out which entries have nothing to do with politics, movies, TV and sports

# # now for creation of graphics from these csvs
# # 	graphics for 2021 overview
# create_charts_top_10()
# create_charts_monthly_top_titles()
# create_charts_monthly_top_titles_no_movies_tv_sports()
