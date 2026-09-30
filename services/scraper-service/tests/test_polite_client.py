import httpx
import pytest

from app.services.polite_client import PoliteClient, ScraperPausedError


class FakeTime:
    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def clock(self):
        return self.now

    async def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def make_client(handler, fake, **overrides):
    params = dict(
        min_delay=4.0, jitter=0.0, max_retries=2, backoff_base=30.0,
        cooldown_seconds=7200, max_cooldown_seconds=86400, daily_budget=100,
    )
    params.update(overrides)
    return PoliteClient(
        **params,
        transport=httpx.MockTransport(handler),
        sleep=fake.sleep,
        clock=fake.clock,
    )


@pytest.mark.asyncio
async def test_spaces_consecutive_requests():
    fake = FakeTime()
    client = make_client(lambda req: httpx.Response(200, json={"ok": 1}), fake)

    await client.get_json("https://x/graphql")
    await client.get_json("https://x/graphql")
    await client.get_json("https://x/graphql")

    assert fake.sleeps == [4.0, 4.0]
    assert client.requests_today == 3


@pytest.mark.asyncio
async def test_403_pauses_everything_without_retrying():
    fake = FakeTime()
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(403)

    client = make_client(handler, fake)

    with pytest.raises(ScraperPausedError):
        await client.get_json("https://x/graphql")
    assert len(calls) == 1
    assert client.pause_remaining_seconds() == 7200

    # Pendant la pause, plus aucune requête ne part.
    with pytest.raises(ScraperPausedError):
        await client.get_json("https://x/graphql")
    assert len(calls) == 1

    # Après le cooldown, ça repart ; un nouveau blocage double la pause.
    fake.now += 7200
    with pytest.raises(ScraperPausedError):
        await client.get_json("https://x/graphql")
    assert client.pause_remaining_seconds() == 14400


@pytest.mark.asyncio
async def test_retries_429_with_retry_after_then_succeeds():
    fake = FakeTime()
    responses = [
        httpx.Response(429, headers={"Retry-After": "90"}),
        httpx.Response(200, json={"data": 1}),
    ]
    client = make_client(lambda req: responses.pop(0), fake)

    assert await client.get_json("https://x/graphql") == {"data": 1}
    assert 90 in fake.sleeps
    assert not client.is_paused()


@pytest.mark.asyncio
async def test_persistent_429_trips_breaker():
    fake = FakeTime()
    client = make_client(lambda req: httpx.Response(429), fake)

    with pytest.raises(ScraperPausedError):
        await client.get_json("https://x/graphql")
    assert client.pause_remaining_seconds() > 0
    assert fake.sleeps.count(30.0) == 1 and fake.sleeps.count(60.0) == 1


@pytest.mark.asyncio
async def test_daily_budget():
    fake = FakeTime()
    client = make_client(lambda req: httpx.Response(200, json={}), fake, daily_budget=2)

    await client.get_json("https://x/graphql")
    await client.get_json("https://x/graphql")
    with pytest.raises(ScraperPausedError):
        await client.get_json("https://x/graphql")


@pytest.mark.asyncio
async def test_success_resets_block_counter():
    fake = FakeTime()
    responses = [httpx.Response(403), httpx.Response(200, json={})]
    client = make_client(lambda req: responses.pop(0), fake)

    with pytest.raises(ScraperPausedError):
        await client.get_json("https://x/graphql")
    fake.now += 7200
    await client.get_json("https://x/graphql")
    assert client.consecutive_blocks == 0
