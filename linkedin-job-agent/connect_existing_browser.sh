#!/bin/bash

# Script to connect to existing Chrome browser session

echo "═══════════════════════════════════════════════════════════"
echo "    Connect to Existing Chrome Browser"
echo "═══════════════════════════════════════════════════════════"
echo

echo "To use your existing Chrome session with the LinkedIn agent:"
echo
echo "1. First, close all Chrome windows"
echo
echo "2. Start Chrome with remote debugging enabled:"
echo "   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222"
echo
echo "   Or if you use Chrome profiles:"
echo "   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --profile-directory=\"Default\""
echo
echo "3. Log into LinkedIn manually in this Chrome session"
echo
echo "4. Keep Chrome open and run the job agent"
echo
echo "═══════════════════════════════════════════════════════════"
echo
echo "Would you like to start Chrome with debugging now? (y/n)"
read -r response

if [[ "$response" == "y" ]]; then
    echo "Starting Chrome with remote debugging on port 9222..."
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 &
    echo
    echo "Chrome started. Please:"
    echo "1. Log into LinkedIn"
    echo "2. Keep this Chrome window open"
    echo "3. Run: ./run_job_search.sh test"
fi