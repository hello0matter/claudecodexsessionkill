import unittest
import urllib.error
import urllib.request
from unittest import mock

import session_cleaner_gui as app


class NetworkTests(unittest.TestCase):
    def test_direct_mode_tolerates_unused_invalid_proxy_fields(self):
        config = app.normalize_network_config(
            {"network_mode": "direct", "proxy_host": "", "proxy_port": "invalid"}
        )

        self.assertEqual(
            config,
            {
                "network_mode": "direct",
                "proxy_host": "127.0.0.1",
                "proxy_port": 7891,
            },
        )

    def test_proxy_mode_rejects_invalid_port(self):
        with self.assertRaisesRegex(ValueError, "代理端口必须是数字"):
            app.normalize_network_config(
                {"network_mode": "http", "proxy_host": "127.0.0.1", "proxy_port": "x"}
            )

    def test_direct_mode_ignores_environment_proxy(self):
        opener = app.build_url_opener(
            {"network_mode": "direct", "proxy_host": "127.0.0.1", "proxy_port": 7891}
        )

        proxy_handlers = [
            handler
            for handler in opener.handlers
            if isinstance(handler, urllib.request.ProxyHandler)
        ]
        self.assertEqual(proxy_handlers, [])

    def test_http_mode_configures_both_protocols(self):
        opener = app.build_url_opener(
            {"network_mode": "http", "proxy_host": "127.0.0.1", "proxy_port": 7891}
        )

        proxy_handler = next(
            handler
            for handler in opener.handlers
            if isinstance(handler, urllib.request.ProxyHandler)
        )
        self.assertEqual(
            proxy_handler.proxies,
            {
                "http": "http://127.0.0.1:7891",
                "https": "http://127.0.0.1:7891",
            },
        )

    def test_socks_mode_uses_remote_dns_handler(self):
        opener = app.build_url_opener(
            {"network_mode": "socks5h", "proxy_host": "127.0.0.1", "proxy_port": 7891}
        )

        handler = next(
            handler
            for handler in opener.handlers
            if isinstance(handler, app._SocksProxyHandler)
        )
        self.assertEqual(handler.config["network_mode"], "socks5h")

    def test_proxy_refusal_has_actionable_message(self):
        message = app.describe_network_error(
            OSError(10061, "connection refused"),
            {"network_mode": "http", "proxy_host": "127.0.0.1", "proxy_port": 7891},
        )

        self.assertIn("127.0.0.1:7891", message)
        self.assertIn("Clash", message)

    def test_anthropic_client_receives_app_proxy(self):
        with mock.patch.object(app.anthropic, "DefaultHttpxClient") as client:
            app.build_anthropic_http_client(
                {"network_mode": "socks5h", "proxy_host": "127.0.0.1", "proxy_port": 7891}
            )

        client.assert_called_once_with(
            trust_env=False,
            proxy="socks5://127.0.0.1:7891",
        )

    def test_openai_rewriter_uses_sdk_user_agent_and_retries_proxy_drop(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = (
            b'{"choices":[{"message":{"content":"ok"}}]}'
        )
        opener = mock.MagicMock()
        opener.open.side_effect = [
            urllib.error.URLError(FileNotFoundError(2, "No such file or directory")),
            response,
        ]
        logs = []
        with (
            mock.patch.object(app, "build_url_opener", return_value=opener),
            mock.patch.object(app.time, "sleep"),
        ):
            rewrite = app.make_openai_rewriter(
                "https://example.com/v1",
                "test-key",
                "test-model",
                "test-prompt",
                lambda level, text: logs.append((level, text)),
                {"network_mode": "http", "proxy_host": "127.0.0.1", "proxy_port": 7891},
            )
            result = rewrite("test")

        request = opener.open.call_args_list[0].args[0]
        self.assertEqual(result, "ok")
        self.assertEqual(request.get_header("User-agent"), app.OPENAI_USER_AGENT)
        self.assertEqual(opener.open.call_count, 2)
        self.assertTrue(any(level == "WARN" for level, _text in logs))


if __name__ == "__main__":
    unittest.main()
