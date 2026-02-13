"""
Simple test for Chat Service without Gemini
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.gemini_client import GeminiClient, SHOPPING_ASSISTANT_INSTRUCTION
from dotenv import load_dotenv

load_dotenv()

async def test_chat(message: str = "I want to buy an iPhone"):
    """Test Gemini chat
    
    Args:
        message: User message to test with
    """
    client = GeminiClient()
    
    print(f"Testing Gemini chat with message: '{message}'")
    print("=" * 60)
    
    try:
        response = await client.chat(
            message=message,
            system_instruction=SHOPPING_ASSISTANT_INSTRUCTION
        )
        
        print(f"\n✓ SUCCESS!")
        print(f"Message: {response.get('message', '')}")
        print(f"\nFunction calls: {len(response.get('function_calls', []))}")
        for i, call in enumerate(response.get('function_calls', []), 1):
            print(f"  {i}. {call.get('name')}: {call.get('arguments')}")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()

if __name__ == "__main__":
    # Get message from command line argument
    user_message = sys.argv[1] if len(sys.argv) > 1 else "I want to buy an iPhone"
    asyncio.run(test_chat(user_message))
