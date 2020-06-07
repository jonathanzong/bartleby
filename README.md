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


## setting up the system

- copy `_debriefing_api_keys.py` into a new file called `debriefing_api_keys.py`, which is gitignored. fill in the api keys.
- copy `config/_env.json` into `config/development.json` and `config/production.json`. these are gitingored. fill in database name and mysql user credentials



