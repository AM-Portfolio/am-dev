
import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.agents.wrapper import CodexConnector
from app.core.config import settings

def test_connection():
    try:
        print(f"Testing Codex Connection...")
        print(f"Model: {settings.CODEX_MODEL}")
        print(f"Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
        
        connector = CodexConnector()
        # Simple prompt to test connectivity
        prompt = "Hello world"
        
        stdout, stderr, code = connector.run_prompt(prompt)
        
        if code == 0:
            print("SUCCESS: Connection established and response received.")
            print(f"Response: {stdout[:100]}...") # Print first 100 chars
        else:
            print(f"FAILURE: Code {code}")
            print(f"Error: {stderr}")

    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    test_connection()
