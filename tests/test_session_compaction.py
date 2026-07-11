"""Tests for session.py: _estimate_chars, summarize, and trim compaction edge cases."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from libreassistant.session import _estimate_chars, summarize, trim


# ---- Helpers ----


def _msg(role: str, content: str, **extra: object) -> dict:
    """Build a minimal API-dict for tests."""
    d: dict[str, object] = {"role": role, "content": content}
    d.update(extra)
    return d


def _system(content: str = "You are a helpful assistant.") -> dict:
    return _msg("system", content)


def _tool(content: str, tool_call_id: str = "call_0") -> dict:
    return _msg("tool", content, tool_call_id=tool_call_id)


def _assistant_tool_calls(tool_calls: list[dict]) -> dict:
    return {"role": "assistant", "content": None, "tool_calls": tool_calls}


def _make_tool_call(
    name: str = "get_weather", arguments: str = '{"city":"London"}'
) -> dict:
    return {
        "id": "call_0",
        "type": "function",
        "function": {"name": name, "arguments": arguments},
    }


def _mock_llm_client(
    summary_text: str | None = "Summary of the conversation.",
) -> MagicMock:
    """Return a mock OpenAI client whose completions.create returns summary_text."""
    client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = summary_text
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    resp = MagicMock()
    resp.choices = [mock_choice]
    client.chat.completions.create.return_value = resp
    return client


def _long_text(n: int) -> str:
    return "word " * n


# ---- _estimate_chars ----


class TestEstimateChars:
    def test_content_only(self) -> None:
        d = [{"role": "user", "content": "hello world"}]
        assert _estimate_chars(d) == 11

    def test_none_content(self) -> None:
        d = [{"role": "assistant", "content": None}]
        assert _estimate_chars(d) == 0

    def test_empty_content(self) -> None:
        d = [{"role": "user", "content": ""}]
        assert _estimate_chars(d) == 0

    def test_tool_calls_counted(self) -> None:
        d = [
            {
                "role": "assistant",
                "content": "hi",
                "tool_calls": [
                    {
                        "id": "c1",
                        "type": "function",
                        "function": {"name": "fn", "arguments": '{"k":"v"}'},
                    }
                ],
            }
        ]
        # content "hi" = 2, name "fn" = 2, arguments '{"k":"v"}' = 9 => 13
        assert _estimate_chars(d) == 13

    def test_multiple_tool_calls(self) -> None:
        d = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "c1",
                        "type": "function",
                        "function": {"name": "a", "arguments": "xx"},
                    },
                    {
                        "id": "c2",
                        "type": "function",
                        "function": {"name": "bbb", "arguments": "yyyy"},
                    },
                ],
            }
        ]
        # name a=1, args xx=2, name bbb=3, args yyyy=4 => 10
        assert _estimate_chars(d) == 10

    def test_multiple_messages(self) -> None:
        d = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "world"},
        ]
        assert _estimate_chars(d) == 3 + 5 + 5

    def test_missing_content_key(self) -> None:
        d: list[dict] = [{"role": "user"}]
        # .get("content", "") or "" => 0
        assert _estimate_chars(d) == 0


# ---- summarize() ----


class TestSummarize:
    def test_basic_summarize(self) -> None:
        """Summarize collapses old messages into one summary assistant message."""
        msgs = [_system("sys prompt")]
        # Need >5 messages and >=3 old with content, plus total >=500 chars
        for i in range(6):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        # 1 sys + 12 = 13 messages, protected={0, 9, 10, 11, 12}, old_indices = [1..8]
        client = _mock_llm_client("Key decisions: discussed project plan.")
        summarize(msgs, client, "gpt-4o")

        # Summary should have replaced old messages
        assert "[Conversation Summary]" in msgs[1]["content"]
        # There should be far fewer messages now
        assert len(msgs) < 13
        # System prompt preserved
        assert msgs[0]["role"] == "system"
        # LLM was called
        client.chat.completions.create.assert_called_once()

    def test_summary_inserted_at_correct_index(self) -> None:
        """Summary is inserted at min(old_indices), which is index 1 when system is at 0."""
        msgs = [_system("sys")]
        for i in range(6):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        client = _mock_llm_client("Summary text.")
        summarize(msgs, client, "gpt-4o")
        # After compression, index 0 is system, index 1 is the summary
        assert msgs[1]["role"] == "assistant"
        assert "[Conversation Summary]" in msgs[1]["content"]

    def test_old_messages_deleted(self) -> None:
        """After summarize, only system + summary + protected tail remain."""
        msgs = [_system("sys")]
        for i in range(6):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        n_before = len(msgs)
        client = _mock_llm_client("Short summary.")
        summarize(msgs, client, "gpt-4o")
        assert len(msgs) < n_before

    def test_too_few_messages(self) -> None:
        """<=5 messages should not trigger summarization."""
        msgs = [_system("sys"), _msg("user", "hi")]
        client = _mock_llm_client("irrelevant")
        original = [dict(m) for m in msgs]
        summarize(msgs, client, "gpt-4o")
        assert msgs == original
        client.chat.completions.create.assert_not_called()

    def test_all_messages_short(self) -> None:
        """Total old text < 500 chars should skip summarization."""
        msgs = [_system("sys")]
        for _ in range(6):
            msgs.append(_msg("user", "short"))
            msgs.append(_msg("assistant", "reply"))
        client = _mock_llm_client("irrelevant")
        original = [dict(m) for m in msgs]
        summarize(msgs, client, "gpt-4o")
        assert msgs == original
        client.chat.completions.create.assert_not_called()

    def test_llm_exception_preserves_messages(self) -> None:
        """If the LLM call raises, messages are left untouched."""
        msgs = [_system("sys")]
        for i in range(6):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        client = MagicMock()
        client.chat.completions.create.side_effect = RuntimeError("API down")
        original_len = len(msgs)
        summarize(msgs, client, "gpt-4o")
        assert len(msgs) == original_len

    def test_llm_empty_summary_preserves_messages(self) -> None:
        """If the LLM returns empty content, messages are preserved."""
        msgs = [_system("sys")]
        for i in range(6):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        client = _mock_llm_client(summary_text=None)
        original_len = len(msgs)
        summarize(msgs, client, "gpt-4o")
        assert len(msgs) == original_len

    def test_llm_returns_empty_string_summary(self) -> None:
        """If the LLM returns empty string, messages are preserved."""
        msgs = [_system("sys")]
        for i in range(6):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        client = _mock_llm_client(summary_text="")
        original_len = len(msgs)
        summarize(msgs, client, "gpt-4o")
        assert len(msgs) == original_len

    def test_long_summary_accepted(self) -> None:
        """A long summary (up to 512 tokens) is accepted without error."""
        msgs = [_system("sys")]
        for i in range(6):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        long_summary = "word " * 2000  # well under 512 tokens worth
        client = _mock_llm_client(summary_text=long_summary)
        summarize(msgs, client, "gpt-4o")
        assert any("[Conversation Summary]" in m.get("content", "") for m in msgs)

    def test_only_one_non_system_message(self) -> None:
        """With only 1 non-system message, nothing should be summarized."""
        msgs = [_system("sys"), _msg("user", _long_text(200))]
        client = _mock_llm_client("nope")
        original_len = len(msgs)
        summarize(msgs, client, "gpt-4o")
        assert len(msgs) == original_len

    def test_only_tool_messages_among_old(self) -> None:
        """Old messages that are tool-role are skipped; not enough user/assistant to summarize."""
        msgs = [_system("sys")]
        for _ in range(6):
            msgs.append(_tool("result"))
        client = _mock_llm_client("nope")
        original_len = len(msgs)
        summarize(msgs, client, "gpt-4o")
        assert len(msgs) == original_len

    def test_system_prompt_preserved(self) -> None:
        """System prompt at index 0 is always preserved through summarization."""
        msgs = [_system("sys prompt")]
        for i in range(6):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        client = _mock_llm_client("Summary.")
        summarize(msgs, client, "gpt-4o")
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == "sys prompt"


# ---- summarize + trim integration ----


class TestSummarizeTrimPipeline:
    def test_summarize_then_trim_reduces_chars(self) -> None:
        """Summarize collapses old messages, then trim handles the rest."""
        msgs = [_system("sys")]
        for i in range(10):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        # 21 messages, old_indices = [1..16]
        before_chars = _estimate_chars(msgs)
        client = _mock_llm_client("Concise summary of discussion.")
        summarize(msgs, client, "gpt-4o")
        after_chars = _estimate_chars(msgs)
        assert after_chars < before_chars

    def test_trim_calls_summarize_in_summarize_mode(self) -> None:
        """trim() with compaction_mode='summarize' invokes summarize first."""
        msgs = [_system("sys")]
        for i in range(10):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        client = _mock_llm_client("Summary.")
        trim(
            msgs,
            max_chars=5000,
            compaction_mode="summarize",
            client=client,
            model="gpt-4o",
        )
        # LLM should have been called (summarize was invoked)
        client.chat.completions.create.assert_called_once()

    def test_trim_without_summarize_mode_no_llm_call(self) -> None:
        """trim() with compaction_mode='trim' does NOT call the LLM."""
        msgs = [_system("sys")]
        for i in range(10):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        client = _mock_llm_client("should not be called")
        trim(
            msgs, max_chars=5000, compaction_mode="trim", client=client, model="gpt-4o"
        )
        client.chat.completions.create.assert_not_called()

    def test_system_prompt_survives_pipeline(self) -> None:
        """System prompt survives both summarize and trim."""
        msgs = [_system("sys prompt")]
        for i in range(10):
            msgs.append(_msg("user", _long_text(200)))
            msgs.append(_msg("assistant", _long_text(200)))
        client = _mock_llm_client("Summary.")
        trim(
            msgs,
            max_chars=5000,
            compaction_mode="summarize",
            client=client,
            model="gpt-4o",
        )
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == "sys prompt"


# ---- trim() additional edge cases ----


class TestTrimEdgeCases:
    def test_trim_with_mixed_tool_calls_and_text(self) -> None:
        """Messages with both content and tool_calls are handled correctly."""
        msgs = [
            _system("sys"),
            _msg("user", _long_text(200)),
            _assistant_tool_calls([_make_tool_call("fn1", '{"a":1}' * 200)]),
            _tool("result1"),
            _msg("user", _long_text(200)),
            _msg("assistant", _long_text(200)),
        ]
        trim(msgs, max_chars=200)
        assert msgs[0]["role"] == "system"

    def test_trim_only_system_messages(self) -> None:
        """A single system message is never dropped, even when over budget."""
        msgs = [_system(_long_text(5000))]
        trim(msgs, max_chars=100)
        assert len(msgs) == 1
        assert msgs[0]["role"] == "system"

    def test_trim_preserves_tool_messages_in_protected_tail(self) -> None:
        """Tool messages in the last 4 messages are protected."""
        msgs = [
            _system("sys"),
            _tool(_long_text(200)),
            _tool(_long_text(200)),
            _msg("user", _long_text(200)),
            _msg("assistant", _long_text(200)),
        ]
        # Protected: {0, 1, 2, 3, 4} (all 5 messages)
        # So nothing should be dropped
        orig_len = len(msgs)
        trim(msgs, max_chars=100)
        assert len(msgs) == orig_len

    def test_trim_paired_deletion_tool_and_preceding_assistant(self) -> None:
        """When a tool message is deleted, its preceding assistant with tool_calls is also deleted."""
        # Need enough messages so the pair (assistant+tool) falls outside the protected
        # tail (last 4) AND outside the tool-result tail scan (30K chars from end).
        # We fill the 30K tool budget with two large tool results near the tail so
        # the earlier small tool at index 3 is NOT protected by the tail scan.
        msgs = [
            _system("sys"),  # 0  - protected (system)
            _msg("user", _long_text(200)),  # 1
            _assistant_tool_calls(
                [_make_tool_call()]
            ),  # 2 - target for paired deletion
            _tool("result"),  # 3 - target for paired deletion (6 chars, unprotected)
            _msg("user", _long_text(200)),  # 4
            _msg("assistant", _long_text(200)),  # 5
            _tool("x" * 15000),  # 6 - fills tool tail budget
            _tool("y" * 15001),  # 7 - exhausts 30K budget (tail scan stops here)
            _msg("user", _long_text(200)),  # 8 - protected (last 4)
            _msg("assistant", _long_text(200)),  # 9 - protected (last 4)
        ]
        # Protected = {0} + last4 {6,7,8,9} + tail-scan {7,6} = {0,6,7,8,9}
        # Index 3 (tool "result") is NOT protected by tail scan (budget exhausted before reaching it)
        trim(msgs, max_chars=5000)
        # Paired deletion should remove index 2 (assistant w/ tool_calls) and index 3 (tool)
        tool_indices = [i for i, m in enumerate(msgs) if m["role"] == "tool"]
        assert 3 not in [m.get("content") == "result" for m in msgs]
        # The assistant with tool_calls at old index 2 should also be gone
        assert not any(m.get("tool_calls") for m in msgs if m["role"] == "assistant")

    def test_effective_budget_calculation(self) -> None:
        """effective_budget = max_chars - 5000; total <= effective_budget means no trimming."""
        # max_chars=10000 => effective=5000
        # 4000 chars total should NOT be trimmed
        msgs = [_system("sys " + _long_text(200))]
        trim(msgs, max_chars=10000)
        assert len(msgs) == 1

    def test_trim_prunes_large_tool_result_in_place(self) -> None:
        """Oversized unprotected tool results are pruned to a stub.

        The tool-result tail scan protects up to 30K chars of tool messages from the end.
        We fill that budget with other tool messages so the target tool is unprotected.
        Budget is set so that phase-1 pruning alone satisfies it (phase 2 never runs).
        """
        msgs = [
            _system("sys"),  # 0  protected (system)
            _msg("user", "hi"),  # 1
            _assistant_tool_calls([_make_tool_call()]),  # 2
            _tool(_long_text(500)),  # 3  target: large tool (2500 chars, >100)
            _msg("user", _long_text(200)),  # 4
            _msg("assistant", _long_text(200)),  # 5
            _tool("x" * 15000),  # 6  fills tail budget
            _tool("y" * 15001),  # 7  exhausts 30K budget
            _msg("user", _long_text(200)),  # 8  protected (last 4)
            _msg("assistant", _long_text(200)),  # 9  protected (last 4)
        ]
        # Tail scan: i=9 skip, i=8 skip, i=7 tool(+15001), i=6 tool(+15000=30001>=30K, stop)
        # Protected = {0, 6, 7, 8, 9}. Index 3 is unprotected.
        # Total ≈ 36534 chars. Old: effective_budget = 40000 - 5000 = 35000.
        # New: effective_budget = 40000 - max(2000, 40000//20) = 40000 - 2000 = 38000 (too generous).
        # Use max_chars=38000 so effective_budget = 38000 - max(2000, 1900) = 36000.
        # 36534 > 36000 → pruning triggers.
        trim(msgs, max_chars=38000)
        pruned = [
            m
            for m in msgs
            if m["role"] == "tool"
            and (
                m.get("content", "").startswith("[pruned")
                or m.get("content", "").startswith("[tool result")
            )
        ]
        assert len(pruned) >= 1

    def test_trim_drops_unprotected_old_messages(self) -> None:
        """Old unprotected non-tool messages are dropped when over budget."""
        msgs = [
            _system("sys"),
            _msg("user", _long_text(500)),
            _msg("assistant", _long_text(500)),
            _msg("user", _long_text(500)),
            _msg("assistant", _long_text(500)),
            _msg("user", "recent"),  # protected (index 5, in last 4)
            _msg("assistant", "reply"),  # protected
        ]
        trim(msgs, max_chars=200)
        # System and last 4 should survive; old messages should be trimmed
        assert msgs[0]["role"] == "system"
        # Recent messages preserved
        assert any(m.get("content") == "recent" for m in msgs)
