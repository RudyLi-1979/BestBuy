"""
Test On-Demand Loading Optimization
Verifies that default searches return only 2 products and store availability is only checked when explicitly requested.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.chat_service import ChatService
from app.database import SessionLocal
import json


async def test_on_demand_loading():
    """Test on-demand loading strategy"""
    print("\n" + "="*80)
    print("ON-DEMAND LOADING OPTIMIZATION TEST")
    print("="*80)
    
    chat_service = ChatService()
    db = SessionLocal()
    user_id = "test_user_123"
    
    # Test 1: Default search should return only 2 products (no store data)
    print("\n" + "-"*80)
    print("TEST 1: Default Product Search (should return 2 products, no store data)")
    print("-"*80)
    
    message1 = sys.argv[1] if len(sys.argv) > 1 else "Show me MacBook Pro"
    print(f"\n👤 User: {message1}")
    
    try:
        response1 = await chat_service.process_message(
            message=message1,
            db=db,
            user_id=user_id
        )
        
        print(f"\n🤖 AI: {response1.get('message', '')[:500]}...")
        
        # Check both function_calls and function_results
        function_calls = response1.get('function_calls', [])
        function_results = response1.get('function_results', [])
        
        print(f"\n🔧 Function Calls: {len(function_calls)}")
        if function_calls:
            for i, call in enumerate(function_calls, 1):
                print(f"   {i}. {call['name']}: {json.dumps(call['arguments'], indent=6)}")
        
        print(f"\n📊 Function Results: {len(function_results)}")
        if function_results:
            for i, result in enumerate(function_results, 1):
                func_name = result.get('function', 'Unknown')
                func_data = result.get('result', {})
                print(f"   {i}. {func_name}:")
                if func_name == 'search_products':
                    products = func_data.get('products', [])
                    print(f"      - Found {len(products)} products")
                    for j, p in enumerate(products[:3], 1):  # Show first 3
                        print(f"         {j}. {p.get('name', 'N/A')[:60]}... (SKU: {p.get('sku', 'N/A')})")
                else:
                    print(f"      - Result: {json.dumps(func_data, indent=9)[:200]}...")
            
            # Verification
            print("\n" + "="*80)
            print("VERIFICATION:")
            has_search = any(r['function'] == 'search_products' for r in function_results)
            has_store_check = any(r['function'] == 'check_store_availability' for r in function_results)
            
            # Count products returned
            search_result = next((r for r in function_results if r['function'] == 'search_products'), None)
            product_count = len(search_result['result'].get('products', [])) if search_result else 0
            
            print(f"✓ search_products executed: {has_search}")
            print(f"✓ Products returned: {product_count} (expected: 2)")
            print(f"✓ check_store_availability executed: {has_store_check} (expected: False)")
            
            # Success criteria
            success = has_search and not has_store_check and product_count <= 2
            if success:
                print("\n🎉 SUCCESS! On-demand loading working correctly:")
                print("   - Product search executed")
                print(f"   - Returned {product_count} products (≤2)")
                print("   - Store availability NOT automatically checked")
                print("   - API calls reduced to minimum")
            else:
                print("\n⚠️  ISSUE DETECTED:")
                if not has_search:
                    print("   - search_products was not executed")
                if has_store_check:
                    print("   - check_store_availability was executed automatically (should be on-demand only)")
                if product_count > 2:
                    print(f"   - Returned {product_count} products (expected ≤2)")
        else:
            print(f"\n⚠️  No function results (may be API quota issue or Gemini asking for clarification)")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Explicit store query should trigger store availability check
    print("\n\n" + "-"*80)
    print("TEST 2: Explicit Store Query (should check store availability)")
    print("-"*80)
    
    message2 = "Where can I buy the first MacBook Pro near 94103?"
    print(f"\n👤 User: {message2}")
    
    try:
        # Build conversation history from first interaction
        conversation_history = [
            {"role": "user", "content": message1},
            {"role": "assistant", "content": response1.get('message', '')}
        ]
        
        response2 = await chat_service.process_message(
            message=message2,
            db=db,
            user_id=user_id,
            conversation_history=conversation_history
        )
        
        print(f"\n🤖 AI: {response2.get('message', '')[:500]}...")
        
        function_results2 = response2.get('function_results', [])
        print(f"\n📊 Function Results: {len(function_results2)}")
        if function_results2:
            for i, result in enumerate(function_results2, 1):
                func_name = result.get('function', 'Unknown')
                print(f"   {i}. {func_name}")
                if func_name == 'check_store_availability':
                    func_data = result.get('result', {})
                    stores = func_data.get('stores', [])
                    print(f"      - Found {len(stores)} stores")
            
            # Verification
            print("\n" + "="*80)
            print("VERIFICATION:")
            has_store_check = any(r['function'] == 'check_store_availability' for r in function_results2)
            
            print(f"✓ check_store_availability executed: {has_store_check} (expected: True)")
            
            if has_store_check:
                print("\n🎉 SUCCESS! Store availability triggered correctly on explicit request")
            else:
                print("\n⚠️  ISSUE: Store availability not triggered when user explicitly asked")
                print("    (May be API quota issue or conversation context lost)")
        else:
            print(f"\n⚠️  No function results (may be API quota issue)")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()
    await chat_service.bestbuy_client.close()
    
    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_on_demand_loading())
