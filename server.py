import socket
import json
import threading

HOST = '0.0.0.0'
PORT = 5555
clients = []
game_state = {
    "player1": {"x": 300, "y": 300},
    "player2": {"x": 400, "y": 300}
}

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(2)
print(f"Serveur sur {HOST}:{PORT}")

def broadcast():
    state_json = json.dumps(game_state)
    for client in clients[:]:
        try:
            client.send(state_json.encode() + b'\n')
        except:
            clients.remove(client)

def handle_client(client_sock, player_id):
    print(f"Joueur {player_id} connecté")
    while True:
        try:
            data = client_sock.recv(1024).decode()
            if data.strip():
                inputs = json.loads(data.rstrip('\n'))
                pid = inputs.get("player_id", player_id)  # Lit le player_id du client
                game_state[pid] = {"x": inputs["x"], "y": inputs["y"]}
                broadcast()
        except:
            break
    client_sock.close()
    clients.remove(client_sock)
    print(f"Joueur {player_id} déconnecté")

client_count = 0
while client_count < 2:
    client_sock, addr = server.accept()
    clients.append(client_sock)
    threading.Thread(target=handle_client, args=(client_sock, f"player{client_count+1}"), daemon=True).start()
    client_count += 1

print("Les 2 joueurs connectés ! Serveur actif...")
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Arrêt serveur")
