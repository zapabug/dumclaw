#!/bin/bash

echo "================================"
echo "Stopping Dumclaw..."
echo "================================"

echo "Stopping Gerald server..."
pkill -f "server.py"

echo "Stopping Gerald listener..."
pkill -f "listener.py"

echo "Stopping strfry sync workers..."
pkill -f "strfry sync"

echo "Stopping strfry relay..."
pkill -f "strfry relay"

echo "Stopping Ollama..."
pkill -f "ollama serve"

echo ""
echo "================================"
echo "Dumclaw stopped"
echo "================================"
