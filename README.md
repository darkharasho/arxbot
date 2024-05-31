![999f4280-e0ab-4dde-80cc-5c79abd212fb-ezgif com-webp-to-png-converter](https://github.com/darkharasho/arxbot/assets/144265798/36f67316-e126-4fa9-8a33-1ec3232695ac)
# arxbot

Yet Another GW2 Discord Bot


## Running Locally
### Run the bot
`poetry run python main.py`
### Get a shell console
```shell
poetry shell
PYTHONSTARTUP=main.py python
```
### Database Viewer
```shell
poetry shell
PYTHONSTARTUP=main.py python
from src.db_viewer import DBViewer

DBViewer().guilds()
DBViewer().members()
```
### Migrations
```shell
# Create
PYTHONPATH=$PWD pw_migrate create --database sqlite:///arxbot.db YOUR_MIGRATION

#Migrate
PYTHONPATH=$PWD pw_migrate migrate --database sqlite:///arxbot.db

#Rollback
PYTHONPATH=$PWD pw_migrate rollback --database sqlite:///arxbot.db

```
