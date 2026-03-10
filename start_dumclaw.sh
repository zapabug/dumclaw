#!/bin/bash

echo "================================"
echo "Starting Dumclaw..."
echo "================================"

STRFRY_DIR="/home/tugajoe/strfry"
DUMCLAW_DIR="/home/tugajoe/develop/dumclaw"
PUBKEY="a706b9fc4cf02962e8760b6a9609c749d226a643529b31bb198b95cca6a5bee9"

echo "Dumclaw dir: $DUMCLAW_DIR"
echo "Strfry dir: $STRFRY_DIR"

# Create logs
mkdir -p $DUMCLAW_DIR/logs

################################
# Start Ollama
################################

echo "Starting Ollama..."

ollama serve > $DUMCLAW_DIR/logs/ollama.log 2>&1 &

sleep 2

################################
# Activate Python venv
################################

echo "Activating Python venv..."

cd $DUMCLAW_DIR || exit
source venv/bin/activate

echo "Python in use:"
which python

################################
# Start strfry relay
################################

echo "Starting strfry relay..."

cd $STRFRY_DIR || exit

./strfry relay > $DUMCLAW_DIR/logs/strfry_relay.log 2>&1 &

sleep 3

################################
# Start relay sync workers
################################

echo "Starting relay sync workers..."

./strfry sync wss://relay.damus.io \
--filter "{\"kinds\":[4,44,1059],\"#p\":[\"$PUBKEY\"]}" \
> $DUMCLAW_DIR/logs/sync_damus.log 2>&1 &

./strfry sync wss://relay.primal.net \
--filter "{\"kinds\":[4,44,1059],\"#p\":[\"$PUBKEY\"]}" \
> $DUMCLAW_DIR/logs/sync_primal.log 2>&1 &

./strfry sync wss://nos.lol \
--filter "{\"kinds\":[4,44,1059],\"#p\":[\"$PUBKEY\"]}" \
> $DUMCLAW_DIR/logs/sync_nos.log 2>&1 &

./strfry sync wss://nip17.com \
--filter "{\"kinds\":[4,44,1059],\"#p\":[\"$PUBKEY\"]}" \
> $DUMCLAW_DIR/logs/sync_nip17.log 2>&1 &

sleep 3

################################
# Start Gerald listener
################################

echo "Starting Gerald listener..."

cd $DUMCLAW_DIR || exit

python -u listener.py > logs/listener.log 2>&1 &

################################
# Start Gerald server
################################

echo "Starting Gerald server..."

python server.py \
> logs/server.log 2>&1 &

echo ""
echo "================================"
echo "Dumclaw started"
echo "Logs in:"
echo "$DUMCLAW_DIR/logs"
echo "================================"

wait
