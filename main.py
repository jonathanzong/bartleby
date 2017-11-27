import config
import tweepy

from flask import Flask, session, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'such secret very key!' # session key

consumer_key = config.TWITTER_CONSUMER_KEY
consumer_secret = config.TWITTER_CONSUMER_SECRET

@app.route('/')
def index():
  print('index')
  if 'access_token' in session:
    return redirect(url_for('debrief'))
  return '<a href="/login">Hello, World!</a>'

@app.route('/debrief')
def debrief():
  print('debrief')
  if 'access_token' in session:
    return 'logged in!!'
  return redirect(url_for('index'))

@app.route('/login')
def login():
  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
  try:
    redirect_url = auth.get_authorization_url()
    session['request_token'] = auth.request_token
    return redirect(redirect_url)
  except tweepy.TweepError:
      print('Error! Failed to get request token.')
      return 'Error! Failed to get request token.'

@app.route('/logout')
def logout():
  # TODO: change where access_token is stored
  del session['access_token']
  return redirect(url_for('index'))

@app.route('/oauth_authorized')
def oauth_authorized():
  print('oauth_authorized')
  verifier = request.args.get('oauth_verifier')

  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
  token = session['request_token']
  del session['request_token']
  auth.request_token = token

  try:
      auth.get_access_token(verifier)
      print(auth.access_token)
      session['access_token'] = auth.access_token # TODO: store access_token somewhere better
      return redirect(url_for('debrief'))
  except tweepy.TweepError:
      print('Error! Failed to get access token.')
      return 'Error! Failed to get access token.'
