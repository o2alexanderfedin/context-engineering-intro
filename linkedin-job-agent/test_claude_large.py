#!/usr/bin/env python
"""Test claude-eng with large input."""

import subprocess
import tempfile
import os

# Create a large test prompt
large_text = "A" * 500000  # 500KB of text

prompt = f"""Extract data from this text.

Text:
{large_text}

Just return: {{"found": "yes"}}"""

# Write to temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
    tmp_file.write(prompt)
    tmp_path = tmp_file.name

print(f"Created temp file: {tmp_path}")
print(f"Prompt size: {len(prompt)} chars")

# Try different approaches
claude_path = os.path.expanduser("~/claude-eng")

print("\n1. Testing with cat and pipe:")
cmd = f"cat '{tmp_path}' | {claude_path}"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
print(f"  Return code: {result.returncode}")
print(f"  Stdout length: {len(result.stdout)}")
print(f"  Stderr: {result.stderr[:200] if result.stderr else 'None'}")

print("\n2. Testing with input redirect:")
cmd = f"{claude_path} < '{tmp_path}'"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
print(f"  Return code: {result.returncode}")
print(f"  Stdout length: {len(result.stdout)}")
print(f"  Stderr: {result.stderr[:200] if result.stderr else 'None'}")

print("\n3. Testing with file argument:")
result = subprocess.run([claude_path, "-f", tmp_path], capture_output=True, text=True, timeout=30)
print(f"  Return code: {result.returncode}")
print(f"  Stdout length: {len(result.stdout)}")
print(f"  Stderr: {result.stderr[:200] if result.stderr else 'None'}")

# Clean up
os.unlink(tmp_path)
print("\nTemp file cleaned up")