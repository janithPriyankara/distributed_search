# Distributed Search System

This project implements a distributed search system with HTTP and UDP communication, file management, node registration, and network updates.

## Structure
- `bs/` - Bootstrap server logic
- `node/` - Node logic (registration, update, request processing)
- `http/` - HTTP server/client/controllers
- `udp/` - UDP server/client/controllers
- `common/` - Shared utilities (file generator, property loader, tables)
- `main.py` - Entry point

## Getting Started
- Install Python 3.8+
- Install Flask for HTTP server: `pip install flask`
- Run `main.py` to start the system

## Features
- Node registration and network update
- File name memory and file generator
- HTTP and UDP server/client logic
- Property loader and neighbor/routing tables
