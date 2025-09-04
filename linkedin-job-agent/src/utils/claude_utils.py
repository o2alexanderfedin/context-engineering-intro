"""Claude AI utility functions for making API calls."""

import asyncio
from json import dumps
from typing import Optional

from claude_code_sdk import (
    ClaudeSDKClient, ClaudeCodeOptions, 
    SystemMessage, UserMessage, AssistantMessage, ResultMessage,
    TextBlock, ThinkingBlock, ToolUseBlock, ToolResultBlock
)


async def ask_claude(
    prompt: str, 
    max_retries: int = 3, 
    max_turns: int = 100, 
    system_prompt: Optional[str] = None,
    debug: bool = False
) -> str:
    """Ask Claude AI using Claude Code SDK with retry logic.
    
    Args:
        prompt: The prompt to send to Claude
        max_retries: Maximum number of retry attempts
        max_turns: Maximum number of conversation turns
        system_prompt: Optional system prompt to set context
        debug: Whether to print debug information
        
    Returns:
        The text response from Claude
        
    Raises:
        Exception: If Claude fails to respond after all retries
    """
    if system_prompt is None:
        system_prompt = "You are a helpful AI assistant. Provide accurate and well-structured responses."
        
    for attempt in range(max_retries):
        try:
            response_text = ""
            error_occurred = False
            
            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    max_turns=max_turns,
                    system_prompt=system_prompt,
                    permission_mode="bypassPermissions"
                )
            ) as client:
                await client.query(prompt)

                # Collect the full response
                async for message in client.receive_response():
                    # Handle different message types
                    if isinstance(message, SystemMessage):
                        if debug:
                            print(f"System: {dumps(message.data, indent=4)}")
                    elif isinstance(message, UserMessage):
                        if debug:
                            print(f"User: {message.content if isinstance(message.content, str) else 'blocks'}")
                            if not isinstance(message.content, str):
                                _print_content_blocks(message, debug)
                    elif isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                response_text += block.text
                                if debug:
                                    print(f"Assistant TextBlock: {block.text[:100]}...")
                            elif debug:
                                _print_content_block(block, debug)
                    elif isinstance(message, ResultMessage):
                        if message.is_error:
                            error_occurred = True
                            if debug:
                                print(f"Result Error: subtype={message.subtype}: {message.result}")
                            continue
                        # Process successful result
                        if message.subtype == 'success' and message.result:
                            response_text += message.result
                            if debug:
                                print(f"Result Success: {len(message.result)} chars")

                # If error occurred, retry
                if error_occurred and attempt < max_retries - 1:
                    await asyncio.sleep(0.5)
                    continue
                
                # Check if response looks valid
                if response_text:
                    return response_text
                elif attempt < max_retries - 1:
                    # No response, retry
                    await asyncio.sleep(0.5)
                    continue
                else:
                    return response_text
                    
        except Exception as e:
            # Check if it's a CLI not found error
            if "Claude Code not found" in str(e):
                print(f"Claude Code CLI not found, ensure it's installed: npm install -g @anthropic-ai/claude-code")
                raise
                
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
                continue
            return f"AI error after {max_retries} attempts: {e}"
    
    return "AI failed to respond after all retries"


def _print_content_blocks(message: UserMessage | AssistantMessage, debug: bool = True):
    """Print content blocks for debugging."""
    if not debug:
        return
        
    for block in message.content:
        _print_content_block(block, debug)


def _print_content_block(block, debug: bool = True):
    """Print a single content block for debugging."""
    if not debug:
        return
        
    if isinstance(block, TextBlock):
        print(f"TextBlock: {block.text[:100]}...")
    elif isinstance(block, ThinkingBlock):
        print(f"ThinkingBlock: {block.thinking[:100]}...")
    elif isinstance(block, ToolUseBlock):
        print(f"ToolUse: {block.name}({block.id})")
    elif isinstance(block, ToolResultBlock):
        print(f"ToolResult: {block.tool_use_id}")