import twitter_sender_api_keys
import tweepy
from time import sleep
import sys

# USAGE: python3 sample_users.py [account_name]
# example: python3 sample_users.py sigchi
account_name = sys.argv[1]

auth = tweepy.OAuthHandler(twitter_sender_api_keys.consumer_key, twitter_sender_api_keys.consumer_secret)
auth.set_access_token(twitter_sender_api_keys.access_token, twitter_sender_api_keys.access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)

print('retrieving followers of %s' % account_name)
ids = []
for page in tweepy.Cursor(api.followers_ids, screen_name=account_name).pages():
    ids.extend(page)
    print('got a page')

outfile = open('./config/experiments/samples/' + account_name + '-followers.txt', 'w')
for uid in ids:
  outfile.write("%s\n" % uid)

print('done')
