import uvicorn

from westream.utils.models import config

if __name__ == "__main__":
    uvicorn.run(
        "westream.main:app",
        host=config["fastapi_host"],
        port=config["fastapi_port"],
        proxy_headers=True,
        workers=config["fastapi_workers"],
    )
