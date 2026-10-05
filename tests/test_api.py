from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from aiohttp import web

from jack.api import API, ServiceError


@pytest.fixture
async def endpoint():
    async def respond(request):
        code = int(request.match_info["code"])
        if code == 201:
            return web.Response(text="not JSON", content_type="application/json")
        if code == 202:
            return web.json_response([])
        return web.json_response({"success": True}, status=code)

    app = web.Application()
    app.router.add_get("/{code}", respond)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"
    await runner.cleanup()


@pytest.mark.parametrize(
    ("code", "message"),
    [
        (204, "could not be found"),
        (404, "could not be found"),
        (403, "rejected access"),
        (429, "rate limited"),
        (500, "temporarily unavailable"),
        (201, "Could not read"),
        (202, "unexpected response"),
    ],
)
async def test_upstream_failures_are_safe(endpoint, code, message):
    async with aiohttp.ClientSession() as session:
        with pytest.raises(ServiceError, match=message):
            await API(session).json(f"{endpoint}/{code}")


async def test_json_success(endpoint):
    async with aiohttp.ClientSession() as session:
        assert await API(session).json(f"{endpoint}/200") == {"success": True}


async def test_key_in_header_not_url():
    api = API(MagicMock(), "fixture-secret")
    api.json = AsyncMock(return_value={"success": True, "player": {"displayname": "Player"}})
    assert await api.player("fixture-id") == {"displayname": "Player"}
    api.json.assert_awaited_once_with(
        "https://api.hypixel.net/v2/player",
        params={"uuid": "fixture-id"},
        headers={"API-Key": "fixture-secret"},
    )


async def test_missing_key_and_bad_username_do_not_call_network():
    api = API(MagicMock())
    api.json = AsyncMock()
    with pytest.raises(ServiceError, match="HYPIXEL_API_KEY"):
        await api.player("fixture-id")
    with pytest.raises(ServiceError, match="Minecraft username"):
        await api.profile("../invalid")
    api.json.assert_not_called()


async def test_missing_player_and_failed_response():
    api = API(MagicMock(), "fixture")
    api.json = AsyncMock(return_value={"success": True, "player": None})
    with pytest.raises(ServiceError, match="no Hypixel profile"):
        await api.player("fixture-id")
    api._next_request = 0
    api.json.return_value = {"success": False}
    with pytest.raises(ServiceError, match="could not complete"):
        await api.hypixel("guild", name="Example")


async def test_timeout_is_not_exposed():
    session = MagicMock()
    session.get.side_effect = TimeoutError("private details")
    with pytest.raises(ServiceError, match="Could not read") as failure:
        await API(session).json("https://example.invalid")
    assert "private details" not in str(failure.value)


@pytest.mark.parametrize("authenticated", [True, False])
async def test_redirect_does_not_forward_credential_headers(authenticated):
    received_keys = []
    runners = []

    async def destination(request):
        received_keys.append(request.headers.get("API-Key"))
        return web.json_response({"success": True})

    async def serve(handler):
        app = web.Application()
        app.router.add_get("/", handler)
        runner = web.AppRunner(app)
        runners.append(runner)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        return f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}/"

    try:
        target = await serve(destination)

        async def redirect(request):
            raise web.HTTPFound(target)

        source = await serve(redirect)
        async with aiohttp.ClientSession() as session:
            api = API(session)
            if authenticated:
                with pytest.raises(ServiceError):
                    await api.json(source, headers={"API-Key": "fixture-secret"})
                assert received_keys == []
            else:
                assert await api.json(source) == {"success": True}
                assert received_keys == [None]
    finally:
        for runner in reversed(runners):
            await runner.cleanup()
