"""JSON utility functions for parsing AI responses."""

import json
import re
from typing import Any, Dict, Union


def extract_json_from_text(text: str) -> Union[Dict[str, Any], list]:
    """Extract and parse JSON from text, handling markdown code blocks.
    
    Args:
        text: Text that may contain JSON, possibly wrapped in markdown code blocks
        
    Returns:
        Parsed JSON as a dictionary or list
        
    Raises:
        ValueError: If JSON cannot be extracted or parsed
    """
    result = text
    
    # Extract JSON from markdown if needed (Claude returns JSON in ```json blocks)
    if '```json' in result:
        json_match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1).strip()
    elif '```' in result:
        code_match = re.search(r'```\s*(.*?)\s*```', result, re.DOTALL)
        if code_match:
            result = code_match.group(1).strip()
    
    # Try to parse JSON from response
    # Find the first complete JSON object by matching braces
    json_start = result.find('{')
    if json_start >= 0:
        brace_count = 0
        json_end = json_start
        
        for i in range(json_start, len(result)):
            if result[i] == '{':
                brace_count += 1
            elif result[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
        
        if brace_count == 0:  # Found complete JSON object
            json_str = result[json_start:json_end]
            try:
                parsed = json.loads(json_str)
                return parsed
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}") from e
    
    # Also check for array format
    array_start = result.find('[')
    if array_start >= 0:
        bracket_count = 0
        array_end = array_start
        
        for i in range(array_start, len(result)):
            if result[i] == '[':
                bracket_count += 1
            elif result[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    array_end = i + 1
                    break
        
        if bracket_count == 0:  # Found complete JSON array
            json_str = result[array_start:array_end]
            try:
                parsed = json.loads(json_str)
                return parsed
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}") from e
    
    raise ValueError(f"No JSON found in text: {result[:200] if result else 'empty'}")