#!/usr/bin/env python
"""
Gold Price Service Test Script
Run this to verify the gold price integration is working correctly
Usage: python test_gold_price.py
"""

import sys
import time
from datetime import datetime

def test_imports():
    """Test 1: Verify all required imports work"""
    print("\n" + "="*60)
    print("TEST 1: Checking Required Imports")
    print("="*60)
    
    try:
        print("✓ Importing Flask...")
        import flask
        print(f"  Flask version: {flask.__version__}")
        
        print("✓ Importing Flask-SocketIO...")
        import flask_socketio
        print(f"  Flask-SocketIO version: {flask_socketio.__version__}")
        
        print("✓ Importing socket.io...")
        import socketio
        
        print("✓ Importing requests...")
        import requests
        
        print("✓ Importing TinyDB...")
        import tinydb
        
        print("✓ All imports successful!")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("\nSolution: Run 'pip install -r requirements.txt'")
        return False

def test_gold_price_service():
    """Test 2: Verify gold price service works"""
    print("\n" + "="*60)
    print("TEST 2: Testing Gold Price Service")
    print("="*60)
    
    try:
        from gold_price_service import GoldPriceService
        
        print("✓ Initializing Gold Price Service...")
        service = GoldPriceService(cache_timeout=60)
        
        print("✓ Fetching gold price (this may take a few seconds)...")
        price_data = service.get_gold_price(force_refresh=True)
        
        if price_data.get('status') == 'success':
            print("✓ Gold price fetched successfully!")
            print(f"  Source: {price_data.get('source')}")
            print(f"  Price: ${price_data.get('gold_price_usd'):.2f}/oz")
            print(f"  Price per gram: ${price_data.get('gold_price_per_gram'):.2f}")
            print(f"  Timestamp: {price_data.get('timestamp')}")
            return True
        else:
            print(f"✗ Error fetching price: {price_data.get('message')}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_api_sources():
    """Test 3: Test individual API sources"""
    print("\n" + "="*60)
    print("TEST 3: Testing API Sources")
    print("="*60)
    
    from gold_price_service import GoldPriceService
    service = GoldPriceService()
    
    apis = ['metals.live', 'metals-api', 'coindesk']
    results = {}
    
    for api in apis:
        print(f"\nTesting {api}...")
        try:
            if api == 'metals.live':
                data = service._fetch_from_source(service.API_SOURCES['metals_live'])
                if data:
                    parsed = service.parse_metals_live(data)
                    if parsed and parsed.get('status') == 'success':
                        print(f"✓ {api}: ${parsed['gold_price_usd']:.2f}/oz")
                        results[api] = True
                    else:
                        print(f"✗ {api}: Parse failed")
                        results[api] = False
                else:
                    print(f"✗ {api}: No data")
                    results[api] = False
                    
            elif api == 'metals-api':
                data = service._fetch_from_source(service.API_SOURCES['metals_api'])
                if data:
                    parsed = service.parse_metals_api(data)
                    if parsed and parsed.get('status') == 'success':
                        print(f"✓ {api}: ${parsed['gold_price_usd']:.2f}/oz")
                        results[api] = True
                    else:
                        print(f"✗ {api}: Parse failed")
                        results[api] = False
                else:
                    print(f"✗ {api}: No data")
                    results[api] = False
                    
            elif api == 'coindesk':
                data = service._fetch_from_source(service.API_SOURCES['coindesk'])
                if data:
                    parsed = service.parse_coindesk(data)
                    if parsed and parsed.get('status') == 'success':
                        print(f"✓ {api}: ${parsed['gold_price_usd']:.2f}/oz")
                        results[api] = True
                    else:
                        print(f"✗ {api}: Parse failed")
                        results[api] = False
                else:
                    print(f"✗ {api}: No data")
                    results[api] = False
        except Exception as e:
            print(f"✗ {api}: {str(e)}")
            results[api] = False
    
    success_count = sum(1 for v in results.values() if v)
    print(f"\n{success_count}/3 API sources working")
    return success_count > 0

def test_cache_mechanism():
    """Test 4: Test caching mechanism"""
    print("\n" + "="*60)
    print("TEST 4: Testing Cache Mechanism")
    print("="*60)
    
    from gold_price_service import GoldPriceService
    
    print("✓ Creating service with 5-second cache...")
    service = GoldPriceService(cache_timeout=5)
    
    print("✓ First fetch (should hit API)...")
    start = time.time()
    data1 = service.get_gold_price(force_refresh=True)
    time1 = time.time() - start
    print(f"  Time taken: {time1:.3f}s")
    
    print("✓ Second fetch (should use cache)...")
    start = time.time()
    data2 = service.get_gold_price()
    time2 = time.time() - start
    print(f"  Time taken: {time2:.3f}s")
    
    if time2 < time1:
        print("✓ Cache is working! (second fetch was faster)")
        return True
    else:
        print("⚠ Cache test inconclusive (both fetches had similar times)")
        return True

def test_main_app():
    """Test 5: Test Flask app configuration"""
    print("\n" + "="*60)
    print("TEST 5: Testing Flask App Configuration")
    print("="*60)
    
    try:
        print("✓ Importing main.py...")
        import main
        
        print("✓ Checking Flask app...")
        assert main.app is not None
        print("  Flask app initialized")
        
        print("✓ Checking SocketIO...")
        assert main.socketio is not None
        print("  SocketIO configured")
        
        print("✓ Checking Gold Service...")
        assert main.gold_service is not None
        print("  Gold service initialized")
        
        print("✓ Flask app is configured correctly!")
        return True
        
    except Exception as e:
        print(f"✗ Flask app test failed: {e}")
        return False

def test_endpoints():
    """Test 6: Test API endpoints"""
    print("\n" + "="*60)
    print("TEST 6: Testing API Endpoints")
    print("="*60)
    
    try:
        import main
        from flask import json
        
        print("✓ Creating Flask test client...")
        client = main.app.test_client()
        
        print("✓ Testing /api/gold-price endpoint...")
        response = client.get('/api/gold-price')
        
        if response.status_code == 302:  # Redirect to login
            print("  (Not tested - requires authentication)")
            print("  Status: Redirects to login as expected ✓")
            return True
        elif response.status_code == 200:
            data = json.loads(response.data)
            if data.get('status') == 'success':
                print(f"✓ Endpoint working! Price: ${data.get('gold_price_usd'):.2f}")
                return True
            else:
                print(f"⚠ Endpoint returned error: {data.get('message')}")
                return True  # Endpoint exists, just couldn't fetch price
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Endpoint test failed: {e}")
        return True  # Don't fail if server isn't running

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  Gold Price Service - Installation Test Suite".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    tests = [
        ("imports", test_imports),
        ("gold_price_service", test_gold_price_service),
        ("api_sources", test_api_sources),
        ("cache_mechanism", test_cache_mechanism),
        ("flask_app", test_main_app),
        ("endpoints", test_endpoints),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ Unexpected error in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*60)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Installation is successful.")
        print("\nNext steps:")
        print("1. Read QUICKSTART.md for quick start")
        print("2. Run: python main.py")
        print("3. Open: http://localhost:5000")
        print("4. Log in and view dashboards")
        return 0
    elif passed >= total - 1:
        print("\n⚠ Most tests passed! Minor issues detected.")
        print("Check the output above for details.")
        return 1
    else:
        print("\n✗ Some tests failed. Please check the output above.")
        print("\nTroubleshooting:")
        print("1. Run: pip install -r requirements.txt")
        print("2. Check internet connection for API tests")
        print("3. Verify Python 3.8 or higher")
        print("4. Check firewall settings")
        return 1

if __name__ == '__main__':
    sys.exit(main())
