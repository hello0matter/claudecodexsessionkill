import json
import os
import queue
import tempfile
import unittest
from unittest import mock

import session_cleaner_gui as app


class CrossPlatformTests(unittest.TestCase):
    def test_config_persists_api_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")
            with mock.patch.object(app, "CONFIG_PATH", path):
                app.save_config({"backend": "openai", "api_key": "secret"})
                with open(path, encoding="utf-8") as config_file:
                    saved = json.load(config_file)
                loaded = app.load_config()

        self.assertEqual(saved, {"backend": "openai", "api_key": "secret"})
        self.assertEqual(loaded["api_key"], "secret")

    def test_resolve_api_key_prefers_environment(self):
        cfg = {"api_key": "saved-key"}
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            self.assertEqual(app.resolve_api_key(cfg), "env-key")
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            self.assertEqual(app.resolve_api_key(cfg), "saved-key")

    def test_cli_scan_writes_cleaned_copy(self):
        record = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "抱歉，我无法帮助。"}],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "session.jsonl")
            with open(source, "w", encoding="utf-8") as session_file:
                session_file.write(json.dumps(record, ensure_ascii=False) + "\n")

            result = app.main(["scan", source, "--write"])
            output = os.path.join(tmp, "session.cleaned.jsonl")
            with open(output, encoding="utf-8") as cleaned_file:
                cleaned = json.loads(cleaned_file.readline())

        self.assertEqual(result, 0)
        self.assertEqual(
            cleaned["message"]["content"][0]["text"], app.FALLBACK_REPLACEMENT
        )

    def test_worker_can_stop_and_join(self):
        with tempfile.TemporaryDirectory() as tmp:
            worker = app.Worker(
                roots=[tmp],
                patterns=app.DEFAULT_REFUSAL_PATTERNS,
                strip_thinking=True,
                in_place=False,
                use_ai=False,
                poll_interval=0.01,
                debounce=0.0,
                log_q=queue.Queue(),
            )
            worker.start()
            worker.stop()
            worker.join(timeout=2)

        self.assertFalse(worker.is_alive())


if __name__ == "__main__":
    unittest.main()
