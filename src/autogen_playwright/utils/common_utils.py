import os
import logging
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

def find_env_file() -> Path:
    """Find the .env file in the project root
    
    Returns:
        Path: Path to the .env file
        
    Raises:
        FileNotFoundError: If no .env file is found in any of the expected locations
    """
    current_dir = Path.cwd()
    
    # First check in current directory
    env_path = current_dir / '.env'
    if env_path.exists():
        return env_path
        
    # Then check in project root (up one level from examples)
    project_root = current_dir.parent if current_dir.name == 'examples' else current_dir
    env_path = project_root / '.env'
    if env_path.exists():
        return env_path
        
    # Finally check in parent directory
    env_path = project_root.parent / '.env'
    if env_path.exists():
        return env_path
        
    raise FileNotFoundError("Could not find .env file in project directories")

def load_env_from_file(env_file: str = None) -> str:
    """
    Load environment variables from .env file
    
    Args:
        env_file: Path to .env file (optional)
        
    Returns:
        Path to the loaded .env file
    """
    # Try to find .env file in current directory or parent directories
    if not env_file:
        env_file = find_dotenv(usecwd=True)
    
    # If still not found, try the default location
    if not env_file:
        default_env = Path.cwd() / '.env'
        if default_env.exists():
            env_file = str(default_env)
    
    # Load environment variables if file exists
    if env_file and Path(env_file).exists():
        logger.info(f"Loading environment from: {env_file}")
        load_dotenv(env_file)
        return env_file
    else:
        logger.warning("No .env file found. Using existing environment variables.")
        return "No .env file found"

def format_code_for_logs(content: str) -> str:
    """
    Format content for logging, highlighting Python code blocks and error messages
    
    Args:
        content: The content to format
        
    Returns:
        Formatted content with code blocks and errors highlighted
    """
    import re
    
    # Find Python code blocks (```python ... ```)
    code_blocks = re.finditer(r'```python\s*(.*?)\s*```', content, re.DOTALL)
    
    # Replace each code block with a formatted version
    formatted_content = content
    for match in code_blocks:
        code = match.group(1)
        formatted_code = f"\n{'=' * 80}\nPYTHON CODE:\n{'-' * 80}\n{code}\n{'=' * 80}"
        formatted_content = formatted_content.replace(match.group(0), formatted_code)
    
    # Highlight error messages
    error_pattern = r'(Traceback \(most recent call last\):.*?)(?=\n\n|\Z)'
    error_matches = re.finditer(error_pattern, formatted_content, re.DOTALL)
    
    for match in error_matches:
        error_text = match.group(1)
        formatted_error = f"\n{'!' * 80}\nERROR TRACEBACK:\n{'-' * 80}\n{error_text}\n{'!' * 80}"
        formatted_content = formatted_content.replace(error_text, formatted_error)
    
    return formatted_content 