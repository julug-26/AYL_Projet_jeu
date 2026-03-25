import socket
import json
import threading
import pygame

sock = None
game_state = {}
last_send = 0

def connect_to_server(ip='127.0.0.1', port=5555):
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    print(f"✅ Connecté à {ip}:{port}")
    threading.Thread(target=receive_loop, daemon=True).start()

def send_inputs(inputs):
    global last_send
    if sock and sock.fileno() >= 0:
        now = pygame.time.get_ticks()
        if now - last_send > 50:  # 20 FPS réseau (anti-spam)
            try:
                sock.send(json.dumps(inputs).encode() + b'\n')
                last_send = now
            except:
                pass  # Ignore erreurs

def receive_loop():
    global game_state, sock
    buffer = ""
    while sock and sock.fileno() >= 0:
        try:
            data = sock.recv(1024).decode()
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                msg, buffer = buffer.split('\n', 1)
                try:
                    game_state = json.loads(msg)
                except:
                    pass  # JSON foireux
        except:
            break
