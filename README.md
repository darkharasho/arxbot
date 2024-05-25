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
