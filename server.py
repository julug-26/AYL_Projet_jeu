import argparse
import json
import socket
import threading
import time


DEFAULT_PLAYERS = {
    "player1": {"x": 300, "y": 300, "direction": 0, "frame": 0, "flip": False},
    "player2": {"x": 400, "y": 300, "direction": 0, "frame": 0, "flip": False},
}


class GameServer:
    def __init__(self, host="0.0.0.0", port=5555):
        self.host = host
        self.port = port
        self.clients = {}
        self.players = {key: value.copy() for key, value in DEFAULT_PLAYERS.items()}
        self.events = []
        self.next_event_id = 1
        self.current_room = "salle1"
        self.enemies = []
        self.lock = threading.Lock()
        self.running = True

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(2)
        server.settimeout(0.5)
        print(f"Serveur lance sur {self.host}:{self.port}")

        threading.Thread(target=self._broadcast_loop, daemon=True).start()

        try:
            while self.running:
                try:
                    client_sock, addr = server.accept()
                except socket.timeout:
                    continue
                player_id = self._next_player_id()
                if not player_id:
                    self._send(client_sock, {"type": "error", "message": "Partie complete"})
                    client_sock.close()
                    continue

                with self.lock:
                    self.clients[player_id] = client_sock

                print(f"{player_id} connecte depuis {addr[0]}:{addr[1]}")
                self._send(client_sock, {"type": "welcome", "player_id": player_id})
                threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, player_id),
                    daemon=True,
                ).start()
        except KeyboardInterrupt:
            print("Arret serveur")
        finally:
            self.running = False
            server.close()

    def start_in_background(self):
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        time.sleep(0.2)
        return thread

    def stop(self):
        self.running = False

    def _next_player_id(self):
        with self.lock:
            for player_id in ("player1", "player2"):
                if player_id not in self.clients:
                    return player_id
        return None

    def _handle_client(self, client_sock, player_id):
        buffer = ""
        while self.running:
            try:
                data = client_sock.recv(4096).decode("utf-8")
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line:
                        self._handle_message(player_id, json.loads(line))
            except (OSError, json.JSONDecodeError):
                break

        with self.lock:
            if self.clients.get(player_id) is client_sock:
                del self.clients[player_id]
        client_sock.close()
        print(f"{player_id} deconnecte")

    def _handle_message(self, player_id, message):
        if message.get("type") != "update":
            return

        player = message.get("player", {})
        with self.lock:
            self.players[player_id] = {
                "x": int(player.get("x", self.players[player_id]["x"])),
                "y": int(player.get("y", self.players[player_id]["y"])),
                "direction": int(player.get("direction", 0)),
                "frame": int(player.get("frame", 0)),
                "flip": bool(player.get("flip", False)),
            }

            new_room = message.get("room")
            if new_room:
                self.current_room = new_room

            enemies = message.get("enemies")
            if enemies is not None:
                self.enemies = enemies

            event_type = message.get("event")
            if event_type:
                self.events.append({
                    "id": self.next_event_id,
                    "player_id": player_id,
                    "type": event_type,
                })
                self.next_event_id += 1
                self.events = self.events[-20:]

    def _broadcast_loop(self):
        while self.running:
            self._broadcast_state()
            time.sleep(1 / 30)

    def _broadcast_state(self):
        with self.lock:
            message = {
                "type": "state",
                "players": {key: value.copy() for key, value in self.players.items()},
                "events": [event.copy() for event in self.events],
                "connected": len(self.clients),
                "room": self.current_room,
                "enemies": list(self.enemies),
            }
            clients = list(self.clients.items())

        for player_id, client in clients:
            try:
                self._send(client, message)
            except OSError:
                with self.lock:
                    if self.clients.get(player_id) is client:
                        del self.clients[player_id]

    def _send(self, client_sock, message):
        payload = json.dumps(message).encode("utf-8") + b"\n"
        client_sock.sendall(payload)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serveur reseau pour What's Next")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5555)
    args = parser.parse_args()

    GameServer(args.host, args.port).start()