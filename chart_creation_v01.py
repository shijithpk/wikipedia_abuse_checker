#!/usr/bin/env python3

'''
will need to put caveats in images 
will need to put last updated info in image
will need to put data for week of Jan 25 - Feb 27, 2021
'''

import json
import pandas as pd
from datetime import datetime,timezone
import os
import plotly.graph_objects as go
import re

utc_time_now = datetime.now(timezone.utc)
utc_time_now_string = utc_time_now.replace(microsecond=0).replace(tzinfo=None).isoformat() + 'Z'

def create_chart(imported_csv_path, folder_name, image_name):
	exported_img_path = 'image_storage/' + folder_name + '/' + image_name
	image_df = pd.read_csv(imported_csv_path)

	image_df_page_titles = image_df['page_title'].tolist()
	page_title_character_limit = 50
	image_df_page_titles_modified = []
	for x in image_df_page_titles:
		if len(x) < page_title_character_limit:
			image_df_page_titles_modified.append(x)
		else:
			y = x[0:(page_title_character_limit-3)] + '...'
			image_df_page_titles_modified.append(y)

	image_df_page_values = image_df.iloc[:, 1].tolist()

	csv_category = re.search(r".*reverted_(.*)\.csv", imported_csv_path).group(1)

	column_name_dict = {'delta_from_last_week': 'Growth in reverted users',
						'past_3_months': 		'No. of reverted users',
						'past_1_month': 		'No. of reverted users',						
						'past_1_week': 			'No. of reverted users' #should I make this no. of reverted users last week?
						}

	column_name = column_name_dict[csv_category]
	column_name_bold = '<b>' + column_name + '</b>'

	fig = go.Figure(data=[go.Table(
					# columnorder = [1,2], # NEED THIS??
					# columnwidth = [150,100],
				    header=dict(
								values=('<b>Wikipedia page title</b>', column_name_bold), 
                				fill_color='white',
								# line_color='darkslategray',
				                align=['left','center'],
								font=dict(color='black', 
											# size=12,
											family='Verdana'
											),
							    # height=40  #this is cell height
								),
					cells=dict(
								values=[image_df_page_titles_modified, image_df_page_values],
								fill_color='white',
								# line_color='darkslategray',
								align=['left','center'],
								font=dict(color='black', 
										# size=12,
										family= 'Verdana'
											),
								# height=30
								))])

	fig.update_layout(title = dict(
					text="Most vandalised Indian pages on wikipedia last week",
					font=dict(color='black', 
							# size=12,
							family= 'Verdana'
							),
					x = 0.5,
					xanchor = 'center',
					# xref = 'paper',
					xref = 'container',
							)
					)

	fig.update_layout(
					height=450, 
					width=800
					)

	# fig.update_traces(textposition='bottom left')
	# scaled_fig = fig.to_image(format="png", width=600, height=350, scale=2)
	# scaled_fig.write_image(exported_img_path)
	fig.write_image(exported_img_path)

create_chart('csv_storage/2021-12-02_politics/top_10_users_reverted_past_1_week.csv','current_versions','trial_image.webp')