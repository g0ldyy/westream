import aiohttp
import mediaflow_proxy.handlers
import mediaflow_proxy.utils.http_utils

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, Response

from westream.utils.logger import logger
from westream.utils.models import config
from westream.utils.general import (
    check_account,
    build_url,
)


app = FastAPI(docs_url=None, redoc_url=None)


async def get_player_api(
    request: Request,
    username: str,
    password: str,
    action: str = None,
    category_id: str = None,
    vod_id: str = None,
    series_id: str = None,
    stream_id: str = None,
    limit: str = None,
):
    valid, user_data, source, proxy = check_account(username, password)
    if not valid:
        return

    if not action:
        if not proxy["enabled"]:
            return RedirectResponse(build_url(source, "player_api"))

        async with aiohttp.ClientSession() as session:
            try:
                real_data = await session.get(build_url(source, "player_api"))
                real_data = await real_data.json()
            except Exception as e:
                logger.warning(f"Can't retrieve User Data for user {username}: {e}")

        if (
            "user_info" not in real_data
            or real_data["user_info"]["auth"] != 1
            or real_data["user_info"]["status"] != "Active"
        ):
            logger.warning(
                f"Invalid/Expired source account for user {username}: {source}"
            )
            return

        server_info = real_data["server_info"]
        port = str(request.url.port) if request.url.port else "80"
        server_info.update(
            {
                "url": request.url.hostname,
                "port": port,
                "https_port": port,
                "server_protocol": request.url.scheme,  # to fix because it's always returning http and never https
                "rtmp_port": "0",
            }
        )

        return {
            "user_info": {
                "username": username,
                "password": password,
                "message": source["message"],
                "auth": 1,
                "status": "Active",
                "exp_date": user_data["exp_date"],
                "is_trial": "0",
                "active_cons": real_data["user_info"]["active_cons"],
                "created_at": str(user_data["created_at"]),
                "max_connections": real_data["user_info"]["max_connections"],
                "allowed_output_formats": real_data["user_info"][
                    "allowed_output_formats"
                ],
            },
            "server_info": server_info,
        }

    actions_with_params = {
        "get_live_categories": {},
        "get_vod_categories": {},
        "get_series_categories": {},
        "get_live_streams": {"category_id": category_id},
        "get_vod_streams": {"category_id": category_id},
        "get_series": {"category_id": category_id},
        "get_vod_info": {"vod_id": vod_id, "series_id": series_id},
        "get_series_info": {"vod_id": vod_id, "series_id": series_id},
        "get_short_epg": {"stream_id": stream_id, "limit": limit},
        "get_simple_data_table": {"stream_id": stream_id},
    }

    if action in actions_with_params:
        if not proxy["enabled"]:
            return RedirectResponse(
                build_url(source, action, **actions_with_params[action])
            )

        async with aiohttp.ClientSession() as session:
            try:
                data = await session.get(
                    build_url(source, action, **actions_with_params[action])
                )
                data = await data.json()
            except Exception as e:
                logger.warning(f"Can't retrieve Player API for user {username}: {e}")

        return data

    return


@app.get("/player_api.php")
async def player_api(
    request: Request,
    username: str,
    password: str,
    action: str = None,
    category_id: str = None,
    vod_id: str = None,
    series_id: str = None,
    stream_id: str = None,
    limit: str = None,
):
    return await get_player_api(
        request,
        username,
        password,
        action,
        category_id,
        vod_id,
        series_id,
        stream_id,
        limit,
    )


@app.post("/player_api.php")
async def player_api_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    action: str = Form(None),
    category_id: str = Form(None),
    vod_id: str = Form(None),
    series_id: str = Form(None),
    stream_id: str = Form(None),
    limit: str = Form(None),
):
    return await get_player_api(
        request,
        username,
        password,
        action,
        category_id,
        vod_id,
        series_id,
        stream_id,
        limit,
    )


@app.get("/xmltv.php")
async def xmltv(username: str, password: str):
    valid, user_data, source, proxy = check_account(username, password)
    if not valid:
        return

    url = f"{source['url']}/xmltv.php?username={source['username']}&password={source['password']}"
    if not proxy["enabled"]:
        return RedirectResponse(url)

    async with aiohttp.ClientSession() as session:
        try:
            full_epg = await session.get(url)
            full_epg = await full_epg.text()
        except Exception as e:
            logger.warning(f"Can't get Full EPG for user {username}: {source} - {e}")

            return

    return Response(full_epg, media_type="application/xml")


@app.get("/get.php")
async def get(request: Request, username: str, password: str, type: str, output: str):
    valid, user_data, source, proxy = check_account(username, password)
    if not valid:
        return

    url = f"{source['url']}/get.php?username={source['username']}&password={source['password']}&type={type}&output={output}"
    if not proxy["enabled"]:
        return RedirectResponse(url)

    async with aiohttp.ClientSession() as session:
        try:
            playlist = await session.get(url)
            playlist_file = await playlist.text()

            host = source["url"].split("://")[1]
            playlist_file = (
                playlist_file.replace(
                    host,
                    f"{request.url.hostname}:{request.url.port if request.url.port else '80'}",
                )
                .replace(source["username"], username)
                .replace(source["password"], username)
            )
        except Exception as e:
            logger.warning(f"Can't get Playlist for user {username}: {source} - {e}")

            return

    filename = config["playlist_filename"].replace("<USERNAME>", username)

    return Response(
        playlist_file,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def handle_streaming(request: Request, username: str, download_url: str):
    return await mediaflow_proxy.handlers.handle_stream_request(
        request.method,
        download_url,
        mediaflow_proxy.utils.http_utils.get_proxy_headers(request),
    )


@app.get("/{username}/{password}/{filename}")
async def live(request: Request, username: str, password: str, filename: str):
    valid, user_data, source, proxy = check_account(username, password)
    if not valid:
        return

    download_url = (
        f"{source['url']}/{source['username']}/{source['password']}/{filename}"
    )
    if not proxy["enabled"] or (proxy["enabled"] and proxy["except_streams"]):
        return RedirectResponse(download_url)

    return await handle_streaming(request, username, download_url)


@app.get("/timeshift/{username}/{password}/{duration}/{start}/{filename}")
async def live(request: Request, username: str, password: str, duration: str, start: str, filename: str):
    valid, user_data, source, proxy = check_account(username, password)
    if not valid:
        return

    download_url = (
        f"{source['url']}/timeshift/{source['username']}/{source['password']}/{duration}/{start}/{filename}"
    )
    if not proxy["enabled"] or (proxy["enabled"] and proxy["except_streams"]):
        return RedirectResponse(download_url)

    return await handle_streaming(request, username, download_url)


@app.get("/hlsr/{token}/{username}/{password}/{id1}/{id2}/{filename}")
async def hlsr(
    request: Request,
    token: str,
    username: str,
    password: str,
    id1: str,
    id2: str,
    filename: str,
):
    valid, user_data, source, proxy = check_account(username, password)
    if not valid:
        return

    download_url = (
        f"{source['url']}/live/{source['username']}/{source['password']}/{filename}"
    )
    if not proxy["enabled"] or (proxy["enabled"] and proxy["except_streams"]):
        return RedirectResponse(download_url)

    return await handle_streaming(request, username, download_url)


@app.get("/{content_type}/{username}/{password}/{filename}")
async def content_stream(
    request: Request, content_type: str, username: str, password: str, filename: str
):
    if content_type not in ["live", "movie", "series"]:
        return

    valid, user_data, source, proxy = check_account(username, password)
    if not valid:
        return

    download_url = f"{source['url']}/{content_type}/{source['username']}/{source['password']}/{filename}"
    if not proxy["enabled"] or (proxy["enabled"] and proxy["except_streams"]):
        return RedirectResponse(download_url)

    if ".m3u8" in filename:
        async with aiohttp.ClientSession() as session:
            try:
                playlist = await session.get(download_url)
                if "?token" in str(playlist.url):
                    playlist_file = await playlist.text()
                    playlist_file = playlist_file.replace(
                        source["username"], username
                    ).replace(source["password"], username)

                    return Response(
                        playlist_file,
                        headers={
                            "Content-Disposition": f'attachment; filename="{filename}"'
                        },
                    )
            except Exception as e:
                logger.warning(
                    f"Can't get Playlist for user {username}: {source} - {e}"
                )

                return

    return await handle_streaming(request, username, download_url)
