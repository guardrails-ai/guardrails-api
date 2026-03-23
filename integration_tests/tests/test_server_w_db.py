import openai
import os
import unittest
import asyncio
from guardrails import AsyncGuard, Guard
from guardrails.hub import TwoWords


class TestApiWithPostgresDB(unittest.TestCase):
    def setUp(self):
        self.guard = Guard(name="test-db-guard", base_url="http://localhost:8000").use(
            TwoWords(on_fail="fix")
        )

        self.guard.save()

    def test_guard_validation(self):
        guard = Guard.load(name="test-db-guard", api_key="auth-stub")
        if not guard:
            raise RuntimeError("Guard did not load properly!")

        else:
            validation_outcome = guard.validate("France is wonderful in the spring")
            self.assertTrue(validation_outcome.validation_passed)
            self.assertEqual(validation_outcome.validated_output, "France is")

    def test_async_guard_validation(self):
        guard = AsyncGuard.load(name="test-db-guard", api_key="auth-stub")

        if not guard:
            raise RuntimeError("Guard did not load properly!")

        validation_outcome = asyncio.run(
            guard(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "Tell me about Oranges in 5 words"}
                ],
                temperature=0.0,
            )
        )

        self.assertTrue(validation_outcome.validation_passed)  # type: ignore # noqa: E712
        self.assertEqual(validation_outcome.validated_output, "Citrus fruit,")  # type: ignore

    def test_async_streaming_guard_validation(self):
        guard = AsyncGuard.load(name="test-db-guard", api_key="auth-stub")

        if not guard:
            raise RuntimeError("Guard did not load properly!")

        async def run_guard():
            async_iterator = await guard(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "Tell me about Oranges in 5 words"}
                ],
                stream=True,
                temperature=0.0,
            )
            full_output = ""
            async for validation_chunk in async_iterator:  # type: ignore
                full_output += validation_chunk.validated_output
            return full_output

        output = asyncio.run(run_guard())

        self.assertEqual(output, "Citrus fruit,")

    def test_sync_streaming_guard_validation(self):
        # FIXME: ser/deser of async iterators
        os.environ["GUARD_HISTORY_ENABLED"] = "false"
        guard = Guard.load(name="test-db-guard", api_key="auth-stub")

        if not guard:
            raise RuntimeError("Guard did not load properly!")

        iterator = guard(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Tell me about Oranges in 5 words"}],
            stream=True,
            temperature=0.0,
        )

        full_output = ""
        for validation_chunk in iterator:
            full_output += validation_chunk.validated_output  # type: ignore

        self.assertEqual(full_output, "Citrus fruit,")

    def test_server_guard_llm_integration(self):
        guard = Guard.load(name="test-db-guard", api_key="auth-stub")
        if not guard:
            raise RuntimeError("Guard did not load properly!")
        messages = [{"role": "user", "content": "Tell me about Oranges in 5 words"}]

        validation_outcome = guard(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.0,
        )
        # True because of fix behaviour
        self.assertTrue(validation_outcome.validation_passed)  # type: ignore
        self.assertTrue("Citrus fruit" in validation_outcome.validated_output)  # type: ignore

    def test_server_openai_llm_integration(self):
        # OpenAI compatible Guardrails API Guard
        openai.base_url = f"http://127.0.0.1:8000/guards/{self.guard.id}/openai/v1/"

        openai.api_key = os.getenv("OPENAI_API_KEY") or "some key"
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Write 5 words of prose."}],
            temperature=0.0,
        )
        self.assertTrue("Whispers of" in completion.choices[0].message.content)  # type: ignore
        self.assertTrue((completion.guardrails.get("validation_passed")))  # type: ignore
