import twitter_api_keys
import tweepy

from flask import Flask, session, request, redirect, url_for, render_template

app = Flask(__name__)
app.secret_key = 'such secret very key!' # session key

consumer_key = twitter_api_keys.TWITTER_CONSUMER_KEY
consumer_secret = twitter_api_keys.TWITTER_CONSUMER_SECRET

def is_logged_in():
  # TODO
  return 'user' in session

@app.route('/')
def index():
  if is_logged_in():
    return redirect(url_for('debrief'))
  return render_template('index.html')

@app.route('/debrief')
def debrief():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']
  # TODO: look up conditions for user by user.id,
  #       conditionally render template
  return render_template('debrief.html', user=user)

@app.route('/login')
def login():
  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
  try:
    redirect_url = auth.get_authorization_url()
    session['request_token'] = auth.request_token
    return redirect(redirect_url)
  except tweepy.TweepError:
    return 'Error! Failed to get request token.'

@app.route('/logout')
def logout():
  # TODO: will store more things in the future
  del session['user']

  return redirect(url_for('index'))

@app.route('/oauth_authorized')
def oauth_authorized():
  verifier = request.args.get('oauth_verifier')

  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
  token = session['request_token']
  del session['request_token']
  auth.request_token = token

  try:
    auth.get_access_token(verifier)
    api = tweepy.API(auth)
    user = api.me()

    # TODO: store access_token?
    session['user'] = {'id': user.id, 'screen_name': user.screen_name}

    return redirect(url_for('debrief'))
  except tweepy.TweepError:
    return 'Error! Failed to get access token.'
