"""Tests for AIGateway — all Anthropic calls are mocked."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_message(text: str, input_tokens: int = 100, output_tokens: int = 50):
    """Build a fake anthropic.Message."""
    msg = MagicMock()
    msg.stop_reason = "end_turn"
    msg.usage.input_tokens = input_tokens
    msg.usage.output_tokens = output_tokens
    content_block = MagicMock()
    content_block.type = "text"
    content_block.text = text
    msg.content = [content_block]
    return msg


@pytest.fixture
def gateway():
    with patch("app.services.ai_gateway.anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create = AsyncMock()
        from app.services.ai_gateway import AIGateway
        gw = AIGateway()
        gw._client = instance
        yield gw, instance


@pytest.mark.anyio
async def test_complete_returns_text(gateway):
    gw, client = gateway
    client.messages.create.return_value = _make_message("Тест ответ")
    result = await gw.complete(
        model="claude-sonnet-4-6",
        system="system",
        messages=[{"role": "user", "content": "привет"}],
        agent_name="test",
    )
    assert result["text"] == "Тест ответ"
    assert result["stop_reason"] == "end_turn"


@pytest.mark.anyio
async def test_complete_tracks_cost(gateway):
    gw, client = gateway
    client.messages.create.return_value = _make_message("ok", input_tokens=1000, output_tokens=500)
    result = await gw.complete(
        model="claude-sonnet-4-6",
        system="s",
        messages=[{"role": "user", "content": "q"}],
        agent_name="test",
    )
    # sonnet: input=$3/M, output=$15/M → 1000*3 + 500*15 = 3+7.5 = 10.5 / 1_000_000
    assert result["cost_usd"] == pytest.approx(0.0000105, rel=1e-3)


@pytest.mark.anyio
async def test_complete_logs_run(gateway):
    gw, client = gateway
    client.messages.create.return_value = _make_message("ok")
    await gw.complete(
        model="claude-sonnet-4-6",
        system="s",
        messages=[{"role": "user", "content": "q"}],
        agent_name="scout",
        hypothesis_id="abc",
    )
    assert len(gw._run_log) == 1
    log = gw._run_log[0]
    assert log["agent_name"] == "scout"
    assert log["hypothesis_id"] == "abc"
    assert log["model"] == "claude-sonnet-4-6"


@pytest.mark.anyio
async def test_get_daily_cost_accumulates(gateway):
    gw, client = gateway
    client.messages.create.return_value = _make_message("ok", input_tokens=500, output_tokens=500)
    await gw.complete(model="claude-sonnet-4-6", system="s",
                      messages=[{"role": "user", "content": "q"}], agent_name="a")
    await gw.complete(model="claude-sonnet-4-6", system="s",
                      messages=[{"role": "user", "content": "q"}], agent_name="b")
    cost = gw.get_daily_cost()
    assert cost > 0


@pytest.mark.anyio
async def test_complete_haiku_cheaper_than_sonnet(gateway):
    gw, client = gateway
    msg = _make_message("ok", input_tokens=1000, output_tokens=1000)
    client.messages.create.return_value = msg

    r_haiku = await gw.complete(model="claude-haiku-4-5-20251001", system="s",
                                messages=[{"role": "user", "content": "q"}], agent_name="a")
    r_sonnet = await gw.complete(model="claude-sonnet-4-6", system="s",
                                 messages=[{"role": "user", "content": "q"}], agent_name="b")
    assert r_haiku["cost_usd"] < r_sonnet["cost_usd"]


@pytest.mark.anyio
async def test_complete_passes_tools(gateway):
    gw, client = gateway
    client.messages.create.return_value = _make_message("ok")
    tools = [{"name": "web_search", "description": "search", "input_schema": {"type": "object"}}]
    await gw.complete(model="claude-sonnet-4-6", system="s",
                      messages=[{"role": "user", "content": "q"}],
                      tools=tools, agent_name="scout")
    call_kwargs = client.messages.create.call_args.kwargs
    assert call_kwargs["tools"] == tools
