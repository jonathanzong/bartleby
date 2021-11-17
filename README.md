# dmca

## setting up server
```
mysqladmin -u root create debrief_study_test
mysqladmin -u root create debrief_study_development
mysqladmin -u root create debrief_study_production

mysql -u root
> CREATE USER USERNAME@localhost IDENTIFIED BY 'PASSWORD';
GRANT ALL PRIVILEGES ON debrief_study_test.* TO 'USERNAME'@'localhost';
GRANT ALL PRIVILEGES ON debrief_study_development.* TO 'USERNAME'@'localhost';
GRANT ALL PRIVILEGES ON debrief_study_production.* TO 'USERNAME'@'localhost';
flush privileges;
```

## creating config
In `config` directory, create file named `<env>.json`, e.g. `development.json`
```
{
    "host": "localhost",
    "database": "debrief_study_development",
    "user": "",
    "password": ""
}
```

In project root directory, create `alembic.ini`

In project root directory, create `twitter_api_keys.py`
```
TWITTER_CONSUMER_KEY=''
TWITTER_CONSUMER_SECRET=''
```

In project root directory, create `twitter_sender_api_keys.py`
```
consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''
```

Make folder `debrief_data` in `config/experiments` containing the debrief data json files

## running migrations
```
export CS_ENV=all
alembic upgrade head
```

## running server

```
export FLASK_APP=main.py
flask run
```

## AUTO-GENERATE ALEMBIC MIGRATION:
```
# before running this command, you should run
# export CS_ENV=all
alembic revision --autogenerate -m "MESSAGE"
```

## MIGRATING WITH ALEMBIC
```
alembic upgrade head

alembic upgrade +2

alembic downgrade -1

alembic downgrade base

```

## deploy

flask run -h 0.0.0.0 -p 8000 --with-threads &


## setting up the system

- copy `_debriefing_api_keys.py` into a new file called `debriefing_api_keys.py`, which is gitignored. fill in the api keys.
- copy `config/_env.json` into `config/development.json` and `config/production.json`. these are gitingored. fill in database name and mysql user credentials
- copy `_alembic.ini` into `alembic.ini` (also gitignored) and fill in the username/password and other connection info for the database.
- copy `_passenger_wsgi.py` into `passenger_wsgi.py` (also gitignored) and fill in the env and python path.


- verify that the reddit app's oauth redirect URI is configured for the right production url: https://www.reddit.com/prefs/apps/

- use `load_reddit_study.py` to create experiment and participant eligibility records in the database