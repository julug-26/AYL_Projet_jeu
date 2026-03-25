import socket
import threading
import json

SERVER_IP = '127.0.0.1'  # On teste en local d'abord
PORT = 5555

received_state = {}
lock = threading.Lock()

def receive_loop(sock):
    buffer = ""
    while True:
        try:
            data = sock.recv(4096).decode('utf-8')
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line:
                    state = json.loads(line)
                    with lock:
                        received_state.update(state)
                    print("Etat recu:", state)
        except Exception as e:
            print(f"Erreur reception: {e}")
            break

def connect_to_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, PORT))
    print(f"Connecté au serveur {SERVER_IP}:{PORT}")
    recv_thread = threading.Thread(target=receive_loop, args=(sock,))
    recv_thread.daemon = True
    recv_thread.start()
    return sock

def send_input(sock, input_dict):
    try:
        data = json.dumps(input_dict) + "\n"
        sock.send(data.encode('utf-8'))
    except Exception as e:
        print(f"Erreur envoi: {e}")

if __name__ == "__main__":
    sock = connect_to_server()
    send_input(sock, {"x": 150, "y": 200, "action": None})
    input("Appuie sur Entrée pour quitter...\n")
    sock.close()