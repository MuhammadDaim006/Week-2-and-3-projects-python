"""
chat_client.py
--------------
Client-side networking. Handles the socket connection to the server,
sends messages, and runs a background thread that listens for incoming
messages so the GUI never blocks.

Uses the same length-prefixed protocol as server.py.
"""

import socket
import threading

HEADER_LENGTH = 10


class ChatClient:
    def __init__(self, on_message=None, on_disconnect=None):
        """
        on_message(kind, payload_tuple)  -> called for every incoming message
            kind == "MSG"    -> payload_tuple = (username, timestamp, text)
            kind == "SYSTEM" -> payload_tuple = (text,)
            kind == "USERS"  -> payload_tuple = (list_of_usernames,)
        on_disconnect(reason: str) -> called when the connection drops
        """
        self.sock = None
        self.connected = False
        self.username = None
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self._listen_thread = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    def connect(self, host, port, username, timeout=5):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((host, port))
        self.sock.settimeout(None)  # blocking mode for the listen loop

        self.username = username
        self._send_raw(username)  # first message = username handshake

        self.connected = True
        self._listen_thread = threading.Thread(target=self._listen, daemon=True)
        self._listen_thread.start()

    def disconnect(self):
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------
    def send_chat_message(self, text):
        if not self.connected:
            return False
        return self._send_raw(text)

    def _send_raw(self, text):
        try:
            data = text.encode("utf-8")
            header = f"{len(data):<{HEADER_LENGTH}}".encode("utf-8")
            self.sock.sendall(header + data)
            return True
        except OSError:
            self.connected = False
            return False

    # ------------------------------------------------------------------
    # Receiving (runs on background thread)
    # ------------------------------------------------------------------
    def _recv_exact(self, n):
        chunks = []
        remaining = n
        while remaining > 0:
            try:
                chunk = self.sock.recv(remaining)
            except OSError:
                return None
            if not chunk:
                return None
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _listen(self):
        while self.connected:
            header = self._recv_exact(HEADER_LENGTH)
            if header is None:
                break
            try:
                msg_len = int(header.decode("utf-8").strip())
            except ValueError:
                break
            body = self._recv_exact(msg_len)
            if body is None:
                break

            raw = body.decode("utf-8")
            self._dispatch(raw)

        self.connected = False
        if self.on_disconnect:
            self.on_disconnect("Connection to server lost.")

    def _dispatch(self, raw):
        parts = raw.split("|")
        kind = parts[0]

        if kind == "MSG" and len(parts) >= 4:
            username, timestamp, text = parts[1], parts[2], "|".join(parts[3:])
            if self.on_message:
                self.on_message("MSG", (username, timestamp, text))

        elif kind == "SYSTEM" and len(parts) >= 2:
            text = "|".join(parts[1:])
            if self.on_message:
                self.on_message("SYSTEM", (text,))

        elif kind == "USERS" and len(parts) >= 2:
            names = parts[1].split(",") if parts[1] else []
            if self.on_message:
                self.on_message("USERS", (names,))
