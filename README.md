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

```

## deploy

flask run -h 0.0.0.0 -p 8000 --with-threads &
