#!/usr/bin/env python3
"""Test AI extraction directly."""

import subprocess
import json
import os

# Sample HTML from a LinkedIn job card
sample_html = """
<div class="job-card-list__entity-lockup">
    <div class="job-card-list__title">Senior Software Engineer</div>
    <div class="job-card-list__company-name">Google</div>
    <div class="job-card-list__location">Mountain View, CA</div>
    <div class="job-card-list__job-id" data-job-id="123456789">123456789</div>
</div>
"""

# Test the AI extraction
claude_path = os.path.expanduser("~/claude-eng")

if os.path.exists(claude_path):
    print(f"✅ Found claude-eng at {claude_path}")
    
    prompt = f"""Extract ALL job information from this LinkedIn job card HTML.
Return ONLY valid JSON with these keys:
- job_id: the job ID number
- title: exact job title
- company: company name
- location: job location

HTML:
{sample_html}"""
    
    print("Calling claude-eng...")
    try:
        result = subprocess.run(
            [claude_path, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout}")
        
        if result.returncode == 0 and result.stdout:
            # Try to parse JSON
            response = result.stdout
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                job_data = json.loads(json_str)
                print(f"✅ Parsed JSON: {job_data}")
            else:
                print("❌ No JSON found in response")
        else:
            print(f"❌ Error: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("❌ Timeout!")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print(f"❌ claude-eng not found at {claude_path}")