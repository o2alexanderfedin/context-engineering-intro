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
    json_start = result.find('{')
    json_end = result.rfind('}') + 1
    
    # Also check for array format
    if json_start < 0:
        json_start = result.find('[')
        json_end = result.rfind(']') + 1
    
    if json_start >= 0 and json_end > json_start:
        json_str = result[json_start:json_end]
        try:
            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e
    
    raise ValueError(f"No JSON found in text: {result[:200] if result else 'empty'}")