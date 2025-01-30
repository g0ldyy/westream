import orjson

config = orjson.loads(open("data/config.json", encoding="utf-8").read())
accounts = orjson.loads(open("data/accounts.json", encoding="utf-8").read())
