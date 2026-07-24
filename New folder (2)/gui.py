"""
gui.py
------
PyQt5 GUI for the chat client.

- A small login dialog to enter host/port/username.
- A chat window with a message list, an online-users list, and an input box.
- Network callbacks arrive on a background thread, so they're marshalled
  onto the Qt main thread via a signal (required — you can't touch
  widgets directly from a non-GUI thread in Qt).
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QDialog, QFormLayout, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel,
    QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject

from chat_client import ChatClient


class LoginDialog(QDialog):
    """Small dialog to collect host, port, and username before connecting."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connect to Chat Server")
        self.setFixedWidth(320)

        self.host_input = QLineEdit("127.0.0.1")
        self.port_input = QLineEdit("5555")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. daim")

        form = QFormLayout()
        form.addRow("Host:", self.host_input)
        form.addRow("Port:", self.port_input)
        form.addRow("Username:", self.username_input)

        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(connect_btn)

    def get_values(self):
        return (
            self.host_input.text().strip(),
            self.port_input.text().strip(),
            self.username_input.text().strip(),
        )


class SignalBridge(QObject):
    """Relays network-thread events to the Qt main thread safely."""
    message_received = pyqtSignal(str, tuple)
    disconnected = pyqtSignal(str)


class ChatWindow(QWidget):
    def __init__(self, host, port, username):
        super().__init__()
        self.setWindowTitle(f"Chat - {username}")
        self.resize(560, 420)

        self.bridge = SignalBridge()
        self.bridge.message_received.connect(self._on_message_main_thread)
        self.bridge.disconnected.connect(self._on_disconnected_main_thread)

        self.client = ChatClient(
            on_message=lambda kind, payload: self.bridge.message_received.emit(kind, payload),
            on_disconnect=lambda reason: self.bridge.disconnected.emit(reason),
        )

        self._build_ui()
        self._connect_to_server(host, port, username)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        self.messages_list = QListWidget()
        splitter.addWidget(self.messages_list)

        users_panel = QWidget()
        users_layout = QVBoxLayout(users_panel)
        users_layout.addWidget(QLabel("Online"))
        self.users_list = QListWidget()
        users_layout.addWidget(self.users_list)
        splitter.addWidget(users_panel)

        splitter.setSizes([400, 140])
        main_layout.addWidget(splitter)

        input_row = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message and press Enter...")
        self.message_input.returnPressed.connect(self._send_message)
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._send_message)

        input_row.addWidget(self.message_input)
        input_row.addWidget(send_btn)
        main_layout.addLayout(input_row)

        self.status_label = QLabel("Connecting...")
        self.status_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.status_label)

    # ------------------------------------------------------------------
    # Networking
    # ------------------------------------------------------------------
    def _connect_to_server(self, host, port, username):
        try:
            self.client.connect(host, int(port), username)
            self.status_label.setText(f"Connected to {host}:{port} as {username}")
            self.status_label.setStyleSheet("color: green;")
        except (OSError, ValueError) as e:
            QMessageBox.critical(self, "Connection Failed", str(e))
            self.close()

    def _send_message(self):
        text = self.message_input.text().strip()
        if not text:
            return
        if self.client.send_chat_message(text):
            self.message_input.clear()
        else:
            self.status_label.setText("Failed to send — connection lost.")
            self.status_label.setStyleSheet("color: red;")

    # ------------------------------------------------------------------
    # Signal handlers (run on the Qt main thread)
    # ------------------------------------------------------------------
    def _on_message_main_thread(self, kind, payload):
        if kind == "MSG":
            username, timestamp, text = payload
            item = QListWidgetItem(f"[{timestamp}] {username}: {text}")
            if username == self.client.username:
                item.setForeground(Qt.blue)
            self.messages_list.addItem(item)
            self.messages_list.scrollToBottom()

        elif kind == "SYSTEM":
            (text,) = payload
            item = QListWidgetItem(f"* {text}")
            item.setForeground(Qt.gray)
            self.messages_list.addItem(item)
            self.messages_list.scrollToBottom()

        elif kind == "USERS":
            (names,) = payload
            self.users_list.clear()
            self.users_list.addItems(names)

    def _on_disconnected_main_thread(self, reason):
        self.status_label.setText(reason)
        self.status_label.setStyleSheet("color: red;")

    def closeEvent(self, event):
        self.client.disconnect()
        event.accept()


def run_app():
    app = QApplication(sys.argv)

    login = LoginDialog()
    if login.exec_() != QDialog.Accepted:
        sys.exit(0)

    host, port, username = login.get_values()
    if not host or not port or not username:
        QMessageBox.warning(None, "Missing Info", "Host, port, and username are all required.")
        sys.exit(0)

    window = ChatWindow(host, port, username)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()
