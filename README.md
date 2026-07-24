# Week-2-and-3-projects-python
Python
# Config-Driven Settings App

A desktop application that manages app preferences through a single JSON
config file, with a PyQt5 GUI that is generated automatically from a schema
— no manual widget wiring required.

## Features
- Define settings once in a Python schema (type, default, validation rules)
- Auto-generated PyQt5 form: text fields, spin boxes, checkboxes, dropdowns
- Built-in validation (type checks, min/max ranges, allowed choices, required fields)
- Automatic backup of the previous config before saving
- Reset-to-defaults support

## Tech Stack
- Python (OOP)
- JSON for persistence
- PyQt5 for the GUI

## Project Structure
- `schema.py` — defines every setting and its validation rules
- `config_manager.py` — OOP class handling load/save/get/set/validate
- `gui.py` — PyQt5 form built dynamically from the schema
- `main.py` — application entry point

## Getting Started
```bash
pip install PyQt5
python main.py
```

## How It Works
Adding a new setting is as simple as adding one entry to `SETTINGS_SCHEMA`
in `schema.py` — the GUI field, its validation, and its default value are
generated automatically, with no changes needed elsewhere.
# Chat App (Client-Server)

A real-time chat application built with raw sockets and threading, with a
PyQt5 GUI client that lets multiple users message each other instantly
through a central server.

## Features
- Multi-threaded server — handles many simultaneous client connections
- Real-time message broadcasting to all connected users
- Live online-users list
- Join/leave system notifications
- Length-prefixed message protocol (no message corruption or fragmentation)
- Thread-safe GUI updates via Qt signals

## Tech Stack
- Python
- Sockets + Threading (server and client networking)
- PyQt5 for the GUI

## Project Structure
- `server.py` — multi-threaded socket server, broadcasts to all clients
- `chat_client.py` — client-side networking (connect, send, background listener)
- `gui.py` — PyQt5 login dialog + chat window
- `main.py` — client entry point

## Getting Started
```bash
pip install PyQt5

# Terminal 1 — start the server
python server.py

# Terminal 2+ — start a client for each user
python main.py
```

## How It Works
Every message is sent with a fixed-length header stating its size, so the
receiver always knows exactly how many bytes to read — this prevents TCP
from splitting or merging messages. Incoming network data is handled on a
background thread and relayed to the GUI thread through a Qt signal, since
PyQt5 widgets can only be safely updated from the main thread.
