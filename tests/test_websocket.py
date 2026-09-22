"""Exercise WebSocket access controls and the existing call-handler boundary."""
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from careline import main


class CallSocketTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)  # No CUDA/Mongo lifespan for transport tests.
        self.sessions = patch.dict(main.SESSIONS, {"test-call": object()}, clear=True)
        self.sessions.start()
        self.access = patch.object(main, "ACCESS_KEY", "")
        self.access.start()
        self.addCleanup(self.sessions.stop)
        self.addCleanup(self.access.stop)
        self.addCleanup(self.client.close)

    def connect(self, **kwargs):
        return self.client.websocket_connect("/api/calls/test-call/ws", **kwargs)

    def test_turn_and_end_use_existing_handlers(self):
        turn = AsyncMock(return_value={"reply": "Hello", "alert": None, "concern_score": 0})
        end = AsyncMock(return_value={"facts": [], "summary": "Done", "concern_score": 0})
        with patch.object(main, "call_turn", turn), patch.object(main, "call_end", end):
            with self.connect() as ws:
                self.assertEqual(ws.receive_json()["type"], "ready")
                ws.send_json({"type": "turn", "text": "I slept well."})
                self.assertEqual(ws.receive_json()["reply"], "Hello")
                self.assertEqual(turn.await_args.args[0], "test-call")
                self.assertEqual(turn.await_args.args[1].text, "I slept well.")
                ws.send_json({"type": "end"})
                self.assertEqual(ws.receive_json()["type"], "ended")
                end.assert_awaited_once_with("test-call")

    def test_invalid_messages_do_not_break_connection(self):
        with self.connect() as ws:
            ws.receive_json()
            for raw in ["not json", "[]", '{"type":"unknown"}', '{"type":"turn"}']:
                ws.send_text(raw)
                self.assertEqual(ws.receive_json()["status"], 400)
            ws.send_json({"type": "ping"})
            self.assertEqual(ws.receive_json(), {"type": "pong"})

    def test_oversized_message_closes(self):
        with self.connect() as ws:
            ws.receive_json()
            ws.send_text("x" * 8193)
            with self.assertRaises(WebSocketDisconnect) as error:
                ws.receive_json()
            self.assertEqual(error.exception.code, 1009)

    def test_existing_turn_limits_apply(self):
        with self.connect() as ws:
            ws.receive_json()
            for text in ["   ", "x" * 801]:
                ws.send_json({"type": "turn", "text": text})
                self.assertEqual(ws.receive_json()["status"], 400)

    def test_binary_message_closes_without_server_error(self):
        with self.connect() as ws:
            ws.receive_json()
            ws.send_bytes(b"{}")
            with self.assertRaises(WebSocketDisconnect) as error:
                ws.receive_json()
            self.assertEqual(error.exception.code, 1003)

    def test_unknown_call_rejected(self):
        with self.assertRaises(WebSocketDisconnect):
            with self.client.websocket_connect("/api/calls/missing/ws"):
                pass

    def test_cross_origin_rejected(self):
        with self.assertRaises(WebSocketDisconnect):
            with self.connect(headers={"origin": "https://unrelated.example"}):
                pass

    def test_shared_access_requires_cookie(self):
        with patch.object(main, "ACCESS_KEY", "test-access-key-long"):
            with self.assertRaises(WebSocketDisconnect):
                with self.connect():
                    pass
            self.client.cookies.set(main.ACCESS_COOKIE, main._access_cookie_value())
            with self.connect(headers={"origin": "http://testserver"}) as ws:
                self.assertEqual(ws.receive_json()["type"], "ready")

    def test_disconnect_keeps_call_available_for_reconnection(self):
        with self.connect() as ws:
            ws.receive_json()
        self.assertIn("test-call", main.SESSIONS)
        with self.connect() as ws:
            self.assertEqual(ws.receive_json()["type"], "ready")


if __name__ == "__main__":
    unittest.main()
