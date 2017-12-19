import twitter_api_keys
import tweepy
import json
import os
import datetime

from flask import Flask, session, request, redirect, url_for, render_template

from utils.common import DbEngine
from app.models import *
from app.forms import *

app = Flask(__name__)
app.secret_key = 'such secret very key!' # session key

consumer_key = twitter_api_keys.TWITTER_CONSUMER_KEY
consumer_secret = twitter_api_keys.TWITTER_CONSUMER_SECRET

ENV = os.environ['CS_ENV'] = "development" # TODO

CONFIG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config")
db_session = DbEngine(CONFIG_DIR + "/{env}.json".format(env=ENV)).new_session()

sce = TwitterDMCADebriefExperimentController(
    experiment_name='twitter_dmca_debrief_experiment',
    db_session=db_session
  )

def is_logged_in():
  return 'user' in session

@app.route('/')
def index():
  if is_logged_in():
    return redirect(url_for('begin'))
  return render_template('01-index.html')

@app.route('/begin', methods=('GET', 'POST'))
def begin():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']

  if sce.has_completed_study(user):
    return redirect(url_for('complete'))

  # handle form submission
  form = TweetRemovedForm()
  if form.validate_on_submit():
    results_dict = request.form.to_dict()
    del results_dict['csrf_token']
    results_dict['twitter_user_id'] = user['id']

    sce.insert_or_update_survey_result(user, results_dict)

    twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    twitter_user_metadata.tweet_removed = (results_dict['tweet_removed'] == 'true')

    # assign a randomization based on whether tweet_removed

    if results_dict['tweet_removed'] == 'true':
      randomization = db_session.query(Randomization).filter_by(stratum='Removed').filter_by(assigned=False).order_by(Randomization.id).first()
    else:
      randomization = db_session.query(Randomization).filter_by(stratum='Not Removed').filter_by(assigned=False).order_by(Randomization.id).first()
    randomization.assigned = True
    twitter_user_metadata.assignment_json = json.dumps(randomization.__dict__).encode('utf-8')
    db_session.commit()

    return redirect(url_for('tweet_intervention'))
  return render_template('02-begin.html', user=user, form=form)

@app.route('/tweet-intervention')
def tweet_intervention():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']

  if sce.has_completed_study(user):
    return redirect(url_for('complete'))

  return render_template('03-tweet-intervention.html', user=user)

@app.route('/tweet-debrief', methods=('GET', 'POST'))
def tweet_debrief():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']

  if sce.has_completed_study(user):
    return redirect(url_for('complete'))

  # handle form submission
  form = WouldClickTweetForm()
  if form.validate_on_submit():
    results_dict = request.form.to_dict()
    del results_dict['csrf_token']
    results_dict['twitter_user_id'] = user['id']

    sce.insert_or_update_survey_result(user, results_dict)

    return redirect(url_for('debrief'))
  return render_template('04-tweet-debrief.html', user=user, form=form)

@app.route('/debrief', methods=('GET', 'POST'))
def debrief():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']

  if sce.has_completed_study(user):
    return redirect(url_for('complete'))

  # TODO: look up conditions for user by user['id'],
  #       conditionally render template

  # handle form submission
  form = SurveyForm()
  if form.validate_on_submit():
    results_dict = request.form.to_dict()
    del results_dict['csrf_token']
    results_dict['twitter_user_id'] = user['id']

    sce.insert_or_update_survey_result(user, results_dict)

    return redirect(url_for('complete'))
  return render_template('05-debrief.html', user=user, form=form)

@app.route('/complete')
def complete():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']

  if not sce.has_completed_study(user):
    survey_result = db_session.query(TwitterUserSurveyResult).filter_by(twitter_user_id=user['id']).first()
    if survey_result is not None:
      # mark user complete
      twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
      twitter_user_metadata.completed_study_at = datetime.datetime.now()
      db_session.commit()
    else:
      # how did they even get here
      return redirect(url_for('begin'))

  return render_template('06-complete.html')

@app.route('/ineligible')
def ineligible():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']

  # TODO: if actually eligible, redirect to begin

  return render_template('ineligible.html')

@app.route('/login')
def login():
  callback_url = url_for('oauth_authorized', _external=True)
  auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
  try:
    redirect_url = auth.get_authorization_url()
    session['request_token'] = auth.request_token
    return redirect(redirect_url)
  except tweepy.TweepError:
    return 'Error! Failed to get request token.'

@app.route('/logout')
def logout():
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

    today = datetime.datetime.now()
    created = user.created_at
    account_age = today.year - created.year - ((today.month, today.day) < (created.month, created.day))

    # TODO: store access_token?
    session['user'] = {
      'id': user.id,
      'screen_name': user.screen_name,
      'default_profile_image': user.default_profile_image,
      'statuses_count': user.statuses_count,
      'verified': user.verified,
      'created_at': user.created_at.isoformat(),
      'lang': user.lang,
      'account_age': account_age
    }
    user = session['user']

    # create user if not exists
    maybe_twitter_user = db_session.query(TwitterUser).filter_by(id=user['id']).first()
    if maybe_twitter_user is None:
      twitter_user = TwitterUser(id=user['id'],
                                 screen_name=user['screen_name'],
                                 created_at=user['created_at'],
                                 lang=user['lang'])
      db_session.add(twitter_user)
    maybe_twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    if maybe_twitter_user_metadata is None:
      # TODO look for their lumen data, redirect them to ineligible if missing
      twitter_user_metadata = TwitterUserMetadata(twitter_user_id=user['id'],
                                                  user_json=json.dumps(user).encode('utf-8'))
      db_session.add(twitter_user_metadata)
    if maybe_twitter_user is None or maybe_twitter_user_metadata is None:
      db_session.commit()

    return redirect(url_for('begin'))
  except tweepy.TweepError:
    return 'Error! Failed to get access token.'

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('index'))
