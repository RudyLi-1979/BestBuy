"""
Test Gemini Chat with New Functions
Tests Store Availability, Also Bought, Advanced Search through Gemini chat
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.chat_service import ChatService
from sqlalchemy.orm import Session
from app.database import SessionLocal
import json


async def test_chat_with_store_availability():
    """Test store availability through chat"""
    print("\n" + "="*80)
    print("TEST 1: Store Availability via Chat")
    print("="*80)
    
    chat_service = ChatService()
    db = SessionLocal()
    user_id = "test_user_123"
    
    test_messages = [
        "我想找 MacBook Pro 14 吋，請問舊金山 94103 附近哪些門市有貨？",
        # Reduced to 1 query to conserve API quota
    ]
    
    for message in test_messages:
        print(f"\n👤 User: {message}")
        
        try:
            response = await chat_service.process_message(
                message=message,
                db=db,
                user_id=user_id
            )
            
            print(f"🤖 AI: {response.get('message', '')}")
            
            if response.get('function_calls'):
                print(f"\n🔧 Function Calls: {len(response['function_calls'])}")
                for call in response['function_calls']:
                    print(f"   - {call['name']}: {call['arguments']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    db.close()
    await chat_service.bestbuy_client.close()
    print("\n✅ Store availability chat test completed\n")


async def test_chat_with_also_bought():
    """Test also-bought through chat"""
    print("\n" + "="*80)
    print("TEST 2: Also Bought via Chat")
    print("="*80)
    
    chat_service = ChatService()
    db = SessionLocal()
    user_id = "test_user_123"
    
    test_messages = [
        "我想買 MacBook Pro 14 吋，其他人通常還會買什麼？",
        # Reduced to 1 query to conserve API quota
    ]
    
    for message in test_messages:
        print(f"\n👤 User: {message}")
        
        try:
            response = await chat_service.process_message(
                message=message,
                db=db,
                user_id=user_id
            )
            
            print(f"🤖 AI: {response.get('message', '')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    db.close()
    await chat_service.bestbuy_client.close()
    print("\n✅ Also-bought chat test completed\n")


async def test_chat_with_advanced_search():
    """Test advanced search through chat"""
    print("\n" + "="*80)
    print("TEST 3: Advanced Search via Chat")
    print("="*80)
    
    chat_service = ChatService()
    db = SessionLocal()
    user_id = "test_user_123"
    
    test_messages = [
        "我想找 Apple 的筆電，預算在 $2000 以下",
        "Show me Samsung Galaxy phones",  # More specific keyword
        # Reduced to 2 queries to conserve API quota
    ]
    
    for message in test_messages:
        print(f"\n👤 User: {message}")
        
        try:
            response = await chat_service.process_message(
                message=message,
                db=db,
                user_id=user_id
            )
            
            print(f"🤖 AI: {response.get('message', '')}")
            
            if response.get('function_calls'):
                print(f"\n🔧 Function Calls: {len(response['function_calls'])}")
                for call in response['function_calls']:
                    print(f"   - {call['name']}")
                    print(f"     Args: {json.dumps(call['arguments'], indent=6)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    db.close()
    await chat_service.bestbuy_client.close()
    print("\n✅ Advanced search chat test completed\n")


async def test_all_chat_features():
    """Run all chat tests"""
    print("\n" + "="*80)
    print("🧪 TESTING NEW FEATURES VIA GEMINI CHAT")
    print("="*80)
    
    try:
        # Test 1: Store Availability
        await test_chat_with_store_availability()
        
        # Test 2: Also Bought
        await test_chat_with_also_bought()
        
        # Test 3: Advanced Search
        await test_chat_with_advanced_search()
        
        print("\n" + "="*80)
        print("✅ ALL CHAT TESTS COMPLETED!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_all_chat_features())
