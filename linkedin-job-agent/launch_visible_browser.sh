#!/bin/bash

# Script to launch Chrome with debugging port and ensure it's visible

echo "═══════════════════════════════════════════════════════════"
echo "    Launching Visible Chrome Browser for LinkedIn Agent"
echo "═══════════════════════════════════════════════════════════"
echo

# Kill any existing Chrome processes on port 9222
echo "Checking for existing Chrome processes..."
lsof -ti:9222 | xargs kill -9 2>/dev/null

# Launch Chrome with debugging enabled and make it visible
echo "Starting Chrome with remote debugging on port 9222..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9222 \
    --no-first-run \
    --no-default-browser-check \
    --user-data-dir=/tmp/chrome-debug \
    --start-maximized \
    --window-size=1920,1080 \
    --window-position=0,0 \
    --force-device-scale-factor=1 &

# Wait for Chrome to start
sleep 3

# Use AppleScript to bring Chrome to front
osascript -e 'tell application "Google Chrome" to activate'

echo
echo "Chrome is now running and visible!"
echo "The browser window should be in the foreground."
echo
echo "Next steps:"
echo "1. Log into LinkedIn if needed"
echo "2. Keep Chrome open and visible"
echo "3. Run your LinkedIn job agent"
echo
echo "═══════════════════════════════════════════════════════════"