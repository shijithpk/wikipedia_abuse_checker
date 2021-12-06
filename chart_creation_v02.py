#!/usr/bin/env python3

'''
will need to put caveats in images 
will need to put last updated info in image
will need to put data for week of Jan 25 - Feb 27, 2021
	think if we for week of XX to XX, we dont need last updated right?
need to put caveat at end
am not able to get a 1600x900 image from this image, not able to scale things
	is autosize the reason why images are not scaling?
do we need another fig.update_layout() function call at the end?
why am i not getting a fixed cell height?
'''

import json
import pandas as pd
from datetime import datetime,timezone
import os
import plotly.graph_objects as go
import re
from plotly.subplots import make_subplots
from dateutil import parser


# font_family = 'Verdana'
font_family = 'DejaVu Sans Mono'

utc_time_now = datetime.now(timezone.utc)
# utc_time_now_string = utc_time_now.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

#imported_csv_path, folder_name, image_name

def create_charts():

	# yyyy_mm_dd_string = utc_time_now.strftime("%Y-%m-%d")
	yyyy_mm_dd_string = "2021-12-03"


	category_dict = {'delta_from_last_week': {'second_column_name': 'Reverted users Δ',
											'chart_title': 'Indian pages on Wikipedia with most growth in vandalism since last week',
											},
					'past_3_months': 	{'second_column_name': 'Reverted users',
										'chart_title': 'Most vandalised Indian pages on Wikipedia over past 3 months',
										},
					'past_1_month': 	{'second_column_name': 'Reverted users',
										'chart_title': 'Most vandalised Indian pages on Wikipedia past month',
										},						
					'past_1_week': 		{'second_column_name': 'Reverted users',
										'chart_title': 'Most vandalised Indian pages on Wikipedia last week',
										} #should I make this no. of reverted users last week?
						}


	for category in category_dict:
		fig = make_subplots(
			rows= 1, 
			cols= 2,
			horizontal_spacing=0.02,
			specs = [
					[{'type': 'table'},{'type': 'table'}],
					],
			subplot_titles = ['Political', 'Non-Political']
			# if you dont want to set subplot titles beforehand, you can follow instructions here -- https://stackoverflow.com/questions/63220009/how-do-i-set-each-plotly-subplot-title-during-graph-creation-loop
		)

		column_number = 0

		for subcategory in ['politics', 'nonpolitics']:
			column_number += 1
			csv_name = subcategory + '_pages_most_users_reverted_' + category + '.csv'
			folder_name = yyyy_mm_dd_string
			folder_path = 'csv_storage/' + folder_name
			csv_path = folder_path + '/' + csv_name
			subcategory_df = pd.read_csv(csv_path)

			subcategory_df_page_titles = subcategory_df['page_title'].tolist()
			# Do this if you want to limit page titles to a specific character limit
			# page_title_character_limit = 50
			# subcategory_df_page_titles_modified = []
			# for x in subcategory_df_page_titles:
			# 	if len(x) < page_title_character_limit:
			# 		subcategory_df_page_titles_modified.append(x)
			# 	else:
			# 		y = x[0:(page_title_character_limit-3)] + '...' # adding ellipsis to show tite's been trimmed
			# 		subcategory_df_page_titles_modified.append(y)

			subcategory_df_page_values = subcategory_df.iloc[:, 1].tolist()
			second_column_name = category_dict[category]['second_column_name']
			second_column_name_bold = '<b>' + second_column_name + '</b>'

			fig.add_trace(
				go.Table(
					columnwidth = [3,1], #dont set any widths for now, let plotly figure out what's best
												# oh seems columnwidth is a ratio so 2,1 is 2:1, divides width available by ratio
					header=dict(
								values=('<b>Wikipedia page title</b>', second_column_name_bold), 
								fill_color='white',
								line_color='darkslategray',
								align=['center','center'],
								font=dict(
										color='black', 
										size=12,
										family=font_family,
										),
								height=40  #this is cell height, dont specify for now
								),
					cells=dict(
								values=[subcategory_df_page_titles, subcategory_df_page_values],
								fill_color='white',
								line_color='darkslategray',
								align=['left','center'],
								font=dict(
										color='black', 
										size=12,
										family=font_family,
										),
								height=21,
								),
								),
								row=1, 
								col=column_number
								)

		updated_date = utc_time_now.strftime("%b %-d, %Y")
		bottom_string = "<b>Note</b>: Vandalism here is measured by the number of unique usernames—who aren't <br>bots—whose edits have been reverted on a page. Data as on " + updated_date
		# NEED TO ADD THIS NOTEX SOMEHOW
		# fig.update_traces(textposition='bottom left') # USE THIS??

		fig.add_annotation(
						text=bottom_string,
                  		xref="paper", 
						x=0,
						xanchor = 'left',
						yref="paper",
                   		y=0.06, 
						yanchor = 'middle',
				   		showarrow=False,
						align = 'left',
						)


		#below is the style for the titles of the subplots
		fig.update_annotations(font = dict(
										color='black', 
										# size=12,
										family=font_family,
										)
										)

		fig.update_layout(
			# autosize=True,
			height = 450, 
			width = 800,
			margin=dict(
						l=15,
						r=15,
						b=0,
						t=60,
						pad=0
					),
			title = dict(
					text = category_dict[category]['chart_title'],
					font = dict(
							color='black', 
							# size=12,
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


		# For adding lines or dividers between plots
		# fig.add_shape(
		# 			type="line",
		# 			xref="paper", 
		# 			yref="paper",
		# 			x0=0.5, 
		# 			y0=0, 
		# 			x1=0.5,
		# 			y1=0.8,
		# 			line=dict(
		# 				color="#FFA500", #light orange
		# 				width=1,
		# 				),
		# 			)

		img_file_name = category + '.webp'

		# two copies made, one copy is saved in current versions folder, this gets overwritten every week
		img_path_currentfolder = 'image_storage/current_versions/' + img_file_name
		fig.write_image(img_path_currentfolder)

		# second copy saved in folder with date the data was scraped
		#create folder with yyyy-mm-dd name in image_storage if it doesn't exist
		folder_name = yyyy_mm_dd_string
		folder_path = 'image_storage/' + folder_name
		if not os.path.exists(folder_path):
			os.mkdir(folder_path)
		img_path_datefolder = folder_path + '/' + img_file_name
		# fig.write_image(img_path_datefolder, format='webp', width=1600, height=900,scale=1)
		fig.write_image(img_path_datefolder, format='webp')


create_charts()


