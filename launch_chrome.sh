#!/usr/bin/env bash
# Script to launch Google Chrome with Remote Debugging enabled on macOS

PORT=9222
PROFILE_DIR="$HOME/.chrome-job-agent"

echo "========================================================"
echo "🚀 Launching Google Chrome with Remote Debugging (Port $PORT)"
echo "Profile directory: $PROFILE_DIR"
echo "========================================================"

mkdir -p "$PROFILE_DIR"

# Check if port 9222 is already open
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Chrome is already running with remote debugging on port $PORT!"
    exit 0
fi

# Launch Google Chrome with remote debugging enabled
nohup "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=$PORT \
  --user-data-dir="$PROFILE_DIR" \
  --no-first-run \
  --no-default-browser-check \
  "https://www.linkedin.com/jobs" > /dev/null 2>&1 &

CHROME_PID=$!
echo "Chrome started (PID: $CHROME_PID)."
echo "Waiting for Chrome to initialize remote debugging port..."

for i in {1..10}; do
    if curl -s "http://localhost:$PORT/json/version" > /dev/null 2>&1; then
        echo "✅ Connected! Chrome is ready for the agent to control."
        echo "Note: If this is your first time, log into LinkedIn in this Chrome window."
        exit 0
    fi
    sleep 1
done

echo "⚠️ Chrome launched, but port $PORT did not respond yet. Please check the Chrome window."
