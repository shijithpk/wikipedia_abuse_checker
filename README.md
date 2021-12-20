### About the repo 

This repo contains code for a project that tracks the abuse of Wikipedia's Indian pages. Here's my [blog post](https://shijith.com/blog/wikipedia-page-abuse/) about it.

Essentially, the code looks at over 150k pages on wikipedia relating to India, checks their page histories, sees how many contributions were reverted -- a sign that a user's contribution wasn't good and possibly malicious -- tallies them for every page, notes which pages had the most users reverted, and then tweets about it at [@abuse_checker](https://twitter.com/abuse_checker) every Monday morning.

### The code, the process

Am in the middle of re-working this code at the moment. Right now querying the Wikipedia API for about 150k pages is taking way too long, around 2 days. Discovered an [API end-point](https://www.mediawiki.org/wiki/API:RecentChanges) recently that should shorten that time drastically. Will also try to incorporate 'workflow orchestration tools' like [Prefect](https://www.prefect.io/) to make the automation run smoother.

[script_weekly_v07.py](script_weekly_v07.py) has the code that runs weekly, it imports its functions from [helpersWeekly.py](helpersWeekly.py). (script_2021_overview.py was used to prepare stats and charts for my [blog post](https://shijith.com/blog/wikipedia-page-abuse/), for taking a look back at 2021 through the lens of wikipedia abuse.)

The whole process is essentially these steps:
* Find out which pages are related to India on wikipedia
* Query the API, fetch edit histories for each page
* See how many users were reverted on each page
* Create CSVs of the pages that had most users reverted
* Create charts using these CSVs and plotly library 
* Send tweets containing these charts 

### Suggestions, feedback
You can contact me at abuse_checker@shijith.com or at this Twitter handle [@abuse_checker](https://twitter.com/abuse_checker).