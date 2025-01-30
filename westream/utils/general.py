import orjson
import time

from westream.utils.logger import logger
from westream.utils.models import accounts


def check_account(username: str, password: str):
    if username not in accounts:
        logger.info(f"No account found for {username}")

        return False, None, None, None

    user_data = accounts[username]
    user_password = user_data["password"]
    if password != user_password:
        logger.info(
            f"Invalid password for user {username} ({user_password} > {password})"
        )

        return False, user_data, None, None

    time_now = time.time()
    exp_date = user_data["exp_date"]
    if exp_date is not None and time_now > exp_date:
        del accounts[username]

        with open("data/accounts.json", "wb") as file:
            file.write(orjson.dumps(accounts, option=orjson.OPT_INDENT_2))

        logger.info(f"{username}'s account expired ({time_now} > {exp_date})")

        return False, user_data, None, None

    source = user_data["source"]
    proxy = user_data["proxy"]

    return True, user_data, source, proxy


def build_url(source, action, **params):
    base_url = f"{source['url']}/player_api.php?username={source['username']}&password={source['password']}&action={action}"
    if params:
        base_url += "&" + "&".join(
            f"{key}={value}" for key, value in params.items() if value is not None
        )
    return base_url
