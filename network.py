import json
import socket
import threading


class NetworkClient:
    def __init__(self, host="127.0.0.1", port=5555):
        self.host = host
        self.port = port
        self.sock = None
        self.player_id = None
        self.state = {"players": {}, "events": [], "connected": 0}
        self.connected = False
        self._lock = threading.Lock()
        self._buffer = ""

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.connected = True
        threading.Thread(target=self._receive_loop, daemon=True).start()

    def send_player_state(self, player_state, event_type=None):
        if not self.connected or not self.sock:
            return

        message = {
            "type": "update",
            "player": player_state,
        }
        if event_type:
            message["event"] = event_type

        self._send(message)

    def get_state(self):
        with self._lock:
            return {
                "players": {
                    key: value.copy()
                    for key, value in self.state.get("players", {}).items()
                },
                "events": [event.copy() for event in self.state.get("events", [])],
                "connected": self.state.get("connected", 0),
            }

    def close(self):
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass

    def _send(self, message):
        try:
            payload = json.dumps(message).encode("utf-8") + b"\n"
            self.sock.sendall(payload)
        except OSError:
            self.connected = False

    def _receive_loop(self):
        while self.connected:
            try:
                data = self.sock.recv(4096).decode("utf-8")
                if not data:
                    break
                self._buffer += data
                while "\n" in self._buffer:
                    line, self._buffer = self._buffer.split("\n", 1)
                    if line:
                        self._handle_message(json.loads(line))
            except (OSError, json.JSONDecodeError):
                break
        self.connected = False

    def _handle_message(self, message):
        if message.get("type") == "welcome":
            self.player_id = message.get("player_id")
            return

        if message.get("type") != "state":
            return

        with self._lock:
            self.state = {
                "players": message.get("players", {}),
                "events": message.get("events", []),
                "connected": message.get("connected", 0),
            }
