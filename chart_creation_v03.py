#!/usr/bin/env python3

'''
am not able to get a 1600x900 image from this image, not able to scale things
	is autosize the reason why images are not scaling?
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
chart_title_font_size = 21
explanation_string_font_size = 18
# subplot_title_font_size = 18
body_copy_font_size = 18
table_line_width = 1
table_line_color = '#333333'


utc_time_now = datetime.now(timezone.utc)
# utc_time_now_string = utc_time_now.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

#imported_csv_path, folder_name, image_name

def create_charts():

	# yyyy_mm_dd_string = utc_time_now.strftime("%Y-%m-%d")
	yyyy_mm_dd_string = "2021-12-03"


	category_dict = {'delta_from_last_week': {
										# 'second_column_name': 'Growth In Reverted Users',
										'chart_title': '<b>Indian pages on Wikipedia facing highest rise in vandalism*<b>',
										},
					'past_3_months': 	{
										# 'second_column_name': 'Reverted Users',
										'chart_title': '<b>Most vandalised* Indian pages on Wikipedia over past 3 months<b>',
										},
					'past_1_month': 	{
										# 'second_column_name': 'Reverted Users',
										'chart_title': '<b>Most vandalised* Indian pages on Wikipedia over past 1 month<b>',
										},						
					'past_1_week': 		{
										# 'second_column_name': 'Reverted Users',
										'chart_title': '<b>Most vandalised* Indian pages on Wikipedia last week<b>',
										} #should I make this no. of reverted users last week?
						}
	

	for category in category_dict:
		fig = make_subplots(
			rows= 1, 
			cols= 2,
			horizontal_spacing=0,
			specs = [
					[{'type': 'table'},{'type': 'table'}],
					],
			# subplot_titles = ['Politics Pages', 'Non-Politics Pages'],
			# if you dont want to set subplot titles beforehand, you can follow instructions here -- https://stackoverflow.com/questions/63220009/how-do-i-set-each-plotly-subplot-title-during-graph-creation-loop
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

			subcategory_df_raw['combined'] = subcategory_df_raw['rank'].astype(str) + '. ' +subcategory_df_raw['page_title'] +' (' +	subcategory_df_raw.iloc[:, 1].astype(str) + ')'
			# subcategory_df_raw['combined'] = '<b>' + subcategory_df_raw['rank'].astype(str) + '.</b> ' +subcategory_df_raw['page_title'] +' (' +	subcategory_df_raw.iloc[:, 1].astype(str) + ')'
			subcategory_df = subcategory_df_raw[['combined']]

			subcategory_df_page_titles = subcategory_df['combined'].tolist()[0:5]
			# Do this if you want to limit page titles to a specific character limit
			# page_title_character_limit = 50
			# subcategory_df_page_titles_modified = []
			# for x in subcategory_df_page_titles:
			# 	if len(x) < page_title_character_limit:
			# 		subcategory_df_page_titles_modified.append(x)
			# 	else:
			# 		y = x[0:(page_title_character_limit-3)] + '...' # adding ellipsis to show tite's been trimmed
			# 		subcategory_df_page_titles_modified.append(y)

			# subcategory_df_page_values = subcategory_df.iloc[:, 1].tolist()[0:5]
			# second_column_name = category_dict[category]['second_column_name']
			# second_column_name_bold = '<b>' + second_column_name + '</b>'

			if subcategory == 'politics':
				header_text = 'Politics Pages'
			else:
				header_text = 'Non-Politics Pages'

			fig.add_trace(
				go.Table(
					# columnwidth = [3,1], #dont set any widths for now, let plotly figure out what's best
					# 					# oh seems columnwidth is a ratio so 2,1 is 2:1, divides width available by ratio
					header=dict(
								# values=('<b>Wikipedia Page Title</b>', second_column_name_bold), 
								# values=['<b>Wikipedia Page Title</b>'], 
								values=[header_text], 
								fill_color='white',
								line_color=table_line_color,
								line_width = table_line_width,
								# line_color='white',
								# align=['center','center'],
								align=['center'],
								font=dict(
										color='black', 
										size=body_copy_font_size,
										family=font_family,
										),
								# height=40  #this is cell height
								height=28
								),
					cells=dict(
								# values=[subcategory_df_page_titles, subcategory_df_page_values],
								values=[subcategory_df_page_titles],
								fill_color='white',
								line_color=table_line_color,
								line_width = table_line_width,
								# line_color='white',
								# align=['left','center'],
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


		# #below is the style for the titles of the subplots
		# fig.update_annotations(font = dict(
		# 								color='black', 
		# 								size=subplot_title_font_size,
		# 								family=font_family,
		# 								)
		# 								)

		updated_date = utc_time_now.strftime("%b %-d, %Y")
		if category == 'delta_from_last_week':
			explanation_string = "*Vandalism here is measured by the growth since last week in users (no.<br>in brackets) whose edits are reverted on a page. Data as on " + updated_date
		else:
			explanation_string = "*Vandalism here is measured by the number of users (figure in brackets)<br> whose edits have been reverted on a page. Data as on " + updated_date

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
			# autosize=True,
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
		fig.write_image(img_path_currentfolder, format='webp', scale=2)

		# second copy saved in folder with date the data was scraped
		#create folder with yyyy-mm-dd name in image_storage if it doesn't exist
		folder_name = yyyy_mm_dd_string
		folder_path = 'image_storage/' + folder_name
		if not os.path.exists(folder_path):
			os.mkdir(folder_path)
		img_path_datefolder = folder_path + '/' + img_file_name
		# fig.write_image(img_path_datefolder, format='webp', width=1600, height=900,scale=1)
		fig.write_image(img_path_datefolder, format='webp', scale=2)


create_charts()


