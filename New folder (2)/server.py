"""
server.py
---------
Multi-threaded socket chat server.

- Accepts multiple client connections at once.
- Each client is handled on its own thread.
- Broadcasts every message to all connected clients.
- Uses a simple length-prefixed protocol so messages of any size
  are received cleanly (no partial-message issues over TCP).

Run with: python server.py [host] [port]
Defaults: 127.0.0.1 5555
"""

import socket
import threading
import sys
import time

HEADER_LENGTH = 10  # bytes reserved for message length prefix


class ChatServer:
    def __init__(self, host="127.0.0.1", port=5555):
        self.host = host
        self.port = port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # client_socket -> username
        self.clients = {}
        self.clients_lock = threading.Lock()

        self.running = False

    # ------------------------------------------------------------------
    # Networking helpers
    # ------------------------------------------------------------------
    @staticmethod
    def send_message(sock, text):
        """Send a length-prefixed UTF-8 message. Returns False on failure."""
        try:
            data = text.encode("utf-8")
            header = f"{len(data):<{HEADER_LENGTH}}".encode("utf-8")
            sock.sendall(header + data)
            return True
        except OSError:
            return False

    @staticmethod
    def receive_message(sock):
        """Receive one length-prefixed message. Returns None on disconnect."""
        try:
            header = ChatServer._recv_exact(sock, HEADER_LENGTH)
            if header is None:
                return None
            msg_len = int(header.decode("utf-8").strip())
            body = ChatServer._recv_exact(sock, msg_len)
            if body is None:
                return None
            return body.decode("utf-8")
        except (OSError, ValueError):
            return None

    @staticmethod
    def _recv_exact(sock, n):
        """Read exactly n bytes, or return None if the connection closed."""
        chunks = []
        remaining = n
        while remaining > 0:
            chunk = sock.recv(remaining)
            if not chunk:
                return None
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    # ------------------------------------------------------------------
    # Server lifecycle
    # ------------------------------------------------------------------
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.running = True
        print(f"[SERVER] Listening on {self.host}:{self.port}")

        try:
            while self.running:
                client_socket, addr = self.server_socket.accept()
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True,
                )
                thread.start()
        except OSError:
            pass  # socket closed during shutdown
        finally:
            self.stop()

    def stop(self):
        self.running = False
        with self.clients_lock:
            for sock in list(self.clients.keys()):
                sock.close()
            self.clients.clear()
        try:
            self.server_socket.close()
        except OSError:
            pass
        print("[SERVER] Stopped.")

    # ------------------------------------------------------------------
    # Client handling
    # ------------------------------------------------------------------
    def _handle_client(self, client_socket, addr):
        # First message from a new client is expected to be their username.
        username = self.receive_message(client_socket)
        if username is None:
            client_socket.close()
            return

        with self.clients_lock:
            self.clients[client_socket] = username

        print(f"[SERVER] {username} connected from {addr}")
        self._broadcast(f"SYSTEM|{username} joined the chat.", exclude=None)
        self._broadcast_user_list()

        try:
            while self.running:
                message = self.receive_message(client_socket)
                if message is None:
                    break
                timestamp = time.strftime("%H:%M:%S")
                self._broadcast(f"MSG|{username}|{timestamp}|{message}", exclude=None)
        finally:
            self._disconnect_client(client_socket, username)

    def _disconnect_client(self, client_socket, username):
        with self.clients_lock:
            if client_socket in self.clients:
                del self.clients[client_socket]
        try:
            client_socket.close()
        except OSError:
            pass
        print(f"[SERVER] {username} disconnected")
        self._broadcast(f"SYSTEM|{username} left the chat.", exclude=None)
        self._broadcast_user_list()

    def _broadcast(self, text, exclude=None):
        with self.clients_lock:
            dead = []
            for sock in self.clients:
                if sock is exclude:
                    continue
                if not self.send_message(sock, text):
                    dead.append(sock)
            for sock in dead:
                self.clients.pop(sock, None)

    def _broadcast_user_list(self):
        with self.clients_lock:
            names = ",".join(self.clients.values())
        self._broadcast(f"USERS|{names}", exclude=None)


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555
    server = ChatServer(host, port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
