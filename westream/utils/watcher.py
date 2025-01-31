import threading
import time
import orjson
import os

from westream.utils.models import config, accounts
from westream.utils.logger import logger

lock = threading.Lock()

def load_config():
    with open("data/config.json", encoding="utf-8") as file:
        config.update(orjson.loads(file.read()))

def load_accounts():
    with open("data/accounts.json", encoding="utf-8") as file:
        accounts.update(orjson.loads(file.read()))

def refresh_data():
    load_config()
    load_accounts()

def watch_files():
    config_mtime = os.path.getmtime("data/config.json")
    accounts_mtime = os.path.getmtime("data/accounts.json")

    while True:
        time.sleep(5)

        new_config_mtime = os.path.getmtime("data/config.json")
        new_accounts_mtime = os.path.getmtime("data/accounts.json")

        if new_config_mtime != config_mtime or new_accounts_mtime != accounts_mtime:
            with lock:
                refresh_data()
                config_mtime = new_config_mtime
                accounts_mtime = new_accounts_mtime
                logger.log("WESTREAM", "Configuration and Accounts refreshed.")


threading.Thread(target=watch_files, daemon=True).start()
