import unittest

from services.llm import FallbackLLM, TextResponse


class _FailingLLM:
    async def ainvoke(self, prompt):
        raise RuntimeError("primary unavailable")


class _WorkingLLM:
    async def ainvoke(self, prompt):
        return TextResponse(f"fallback:{prompt}")


class LLMFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_primary_failure_uses_krill_adapter(self):
        llm = FallbackLLM(_FailingLLM(), _WorkingLLM())
        response = await llm.ainvoke("ping")
        self.assertEqual(response.content, "fallback:ping")
        self.assertEqual(llm.last_provider, "krill")

    async def test_fallback_can_be_the_only_provider(self):
        llm = FallbackLLM(None, _WorkingLLM())
        response = await llm.ainvoke("ping")
        self.assertEqual(response.content, "fallback:ping")
        self.assertEqual(llm.last_provider, "krill")


if __name__ == "__main__":
    unittest.main()
