#!/usr/bin/env python3

import tweepy
import configparser

config = configparser.ConfigParser()
config.read('./config_twitter.ini')
# or config.read('config_twitter.ini')
BEARER_TOKEN = config['info']['BEARER_TOKEN']
CONSUMER_KEY = config['info']['CONSUMER_KEY']
CONSUMER_SECRET = config['info']['CONSUMER_SECRET']
ACCESS_TOKEN = config['info']['ACCESS_TOKEN']
ACCESS_TOKEN_SECRET = config['info']['ACCESS_TOKEN_SECRET']

# auth = tweepy.OAuthHandler(API_KEY, SECRET_KEY)
# auth.set_access_token(ACCESS_TOKEN, SECRET_TOKEN)
# api = tweepy.API(auth, wait_on_rate_limit=True)

client = tweepy.Client(bearer_token=BEARER_TOKEN,
						consumer_key=CONSUMER_KEY,
						consumer_secret=CONSUMER_SECRET, 
						access_token=ACCESS_TOKEN, 
						access_token_secret=ACCESS_TOKEN_SECRET,
						wait_on_rate_limit=True
						)



random_image_path = 'image_storage/current_versions/delta_from_last_week.webp'
random_text = 'test tweet with attached image'

