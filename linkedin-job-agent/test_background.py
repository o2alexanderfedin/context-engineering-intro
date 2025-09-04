#!/usr/bin/env python
"""Test the LinkedIn job search in background to avoid blocking."""

import subprocess
import time
import os
import signal

def run_job_search():
    """Run the job search in background."""
    
    print("Starting LinkedIn job search in background...")
    
    # Prepare the command
    cmd = [
        "uv", "run", "python", "-m", "src.main", "search",
        "--resume", "resume.txt",
        "--keywords", "",  # Empty for recommended jobs
        "--auto-apply"
    ]
    
    # Run in background using subprocess.Popen
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
        universal_newlines=True
    )
    
    print(f"Process started with PID: {process.pid}")
    print("Output will stream below...")
    print("-" * 50)
    
    try:
        # Stream output in real-time
        while True:
            # Check if process is still running
            poll = process.poll()
            
            # Read stdout line by line (non-blocking)
            line = process.stdout.readline()
            if line:
                print(f"[STDOUT] {line.rstrip()}")
            
            # If process finished, break
            if poll is not None:
                # Get remaining output
                remaining_out, remaining_err = process.communicate()
                if remaining_out:
                    print(f"[STDOUT] {remaining_out}")
                if remaining_err:
                    print(f"[STDERR] {remaining_err}")
                break
            
            # Small sleep to prevent CPU spinning
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nInterrupted! Terminating background process...")
        process.terminate()
        try:
            # Give it 5 seconds to terminate gracefully
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate
            process.kill()
            process.wait()
        print("Process terminated.")
    
    print(f"\nProcess finished with exit code: {process.returncode}")

if __name__ == "__main__":
    run_job_search()