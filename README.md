# Bartleby

Bartleby is a system that delivers research ethics procedures for large-scale online studies. Using Bartleby, researchers can automatically send each of their study participants a message directing them to a website where they can learn about their involvement in research, view what data researchers collected about them, and give feedback. Most importantly, participants can use the website to opt out and request to delete their data.

The system is named after the titular character in Herman Melville’s short story Bartleby, the Scrivener. Over the course of the story, Bartleby opts out of completing various requests. Instead, he states simply that he “would prefer not to.”

Read more about the Bartleby project here: https://citizensandtech.org/2022/02/designing-and-evaluating-research-ethics-systems/
Read the peer-reviewed research paper here: https://journals.sagepub.com/doi/10.1177/20563051221077021

For questions about the Bartleby code, contact Jonathan Zong (jzong@mit.edu).

## setting up database
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

## setting up the system

- copy `_debriefing_api_keys.py` into a new file called `debriefing_api_keys.py`, which is gitignored. fill in the api keys.
- copy `config/_env.json` into `config/development.json` and `config/production.json`. these are gitingored. fill in database name and mysql user credentials
- copy `_alembic.ini` into `alembic.ini` (also gitignored) and fill in the username/password and other connection info for the database.
- copy `_passenger_wsgi.py` into `passenger_wsgi.py` (also gitignored) and fill in the env and python path.

## setting up reddit auth

to support reddit login, you need to create a reddit app (this gives you api keys)

- verify that the reddit app's oauth redirect URI is configured for the right production url: https://www.reddit.com/prefs/apps/

## loading data into the database

- modify the `_load_reddit_study.py` file to create a script that creates experiment and participant eligibility records in the database

```
  url_id='',
  experiment_name=experiment_name,
  platform='reddit',
  study_template=''
```

## templates

When you create an Experiment record in the db, you supply a `study_template` field. This should be the name of a directory in `templates/` that contains two templates: `index.html` and `debrief.html`


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
