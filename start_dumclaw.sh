#!/bin/bash

echo "================================"
echo "Starting Dumclaw..."
echo "================================"

STRFRY_DIR="/home/tugajoe/strfry"
DUMCLAW_DIR="/home/tugajoe/develop/dumclaw"
PUBKEY="a706b9fc4cf02962e8760b6a9609c749d226a643529b31bb198b95cca6a5bee9"

echo "Dumclaw dir: $DUMCLAW_DIR"
echo "Strfry dir: $STRFRY_DIR"

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
echo "Python in use: $(which python)"

################################
# 1. Start strfry relay
################################
echo "Starting strfry relay..."
cd $STRFRY_DIR || exit
./strfry relay > $DUMCLAW_DIR/logs/strfry_relay.log 2>&1 &
sleep 3

################################
# 2. Start strfry monitor
################################
echo "Starting strfry monitor..."
cd $STRFRY_DIR || exit
./strfry monitor > $DUMCLAW_DIR/logs/strfry_monitor.log 2>&1 &

################################
# 3. Start relay sync workers
################################
echo "Starting relay sync workers..."
cd $STRFRY_DIR || exit

./strfry sync wss://relay.damus.io --filter "{\"kinds\":[4,1059],\"#p\":[\"$PUBKEY\"]}" > $DUMCLAW_DIR/logs/sync_damus.log 2>&1 &
./strfry sync wss://relay.primal.net --filter "{\"kinds\":[4,1059],\"#p\":[\"$PUBKEY\"]}" > $DUMCLAW_DIR/logs/sync_primal.log 2>&1 &
./strfry sync wss://nos.lol --filter "{\"kinds\":[4,1059],\"#p\":[\"$PUBKEY\"]}" > $DUMCLAW_DIR/logs/sync_nos.log 2>&1 &
./strfry sync wss://nip17.com --filter "{\"kinds\":[4,1059],\"#p\":[\"$PUBKEY\"]}" > $DUMCLAW_DIR/logs/sync_nip17.log 2>&1 &

sleep 3

################################
# 3.5 Start live bridge (republishes so events reach Gerald in real time)
################################
echo "Starting Gerald live bridge..."
cd $DUMCLAW_DIR || exit
python3 -u bridge.py > logs/bridge.log 2>&1 &
sleep 2

################################
# 4. Start Gerald listener
################################
echo "Starting Gerald listener..."
cd $DUMCLAW_DIR || exit
python3 -u listener.py > logs/listener.log 2>&1 &

################################
# 5. Start Gerald server
################################
echo "Starting Gerald server..."
python server.py > logs/server.log 2>&1 &

echo ""
echo "================================"
echo "Dumclaw started"
echo "================================"
echo ""
echo "Start order:"
echo "  1. strfry relay"
echo "  2. strfry monitor"
echo "  3. sync workers (damus, primal, nos, nip17)"
echo "  3.5 live bridge (republishes for real-time)"
echo "  4. Gerald listener"
echo "  5. Gerald server"
echo ""
echo "Logs in: $DUMCLAW_DIR/logs"
echo "================================"

wait