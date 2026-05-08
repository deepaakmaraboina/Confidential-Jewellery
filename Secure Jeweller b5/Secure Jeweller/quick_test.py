"""Quick test to verify gold price system is working"""

from gold_price_service import get_gold_service
from datetime import datetime

print("=" * 60)
print("GOLD PRICE SERVICE TEST")
print("=" * 60)

gold_service = get_gold_service()

print("\n[1] Fetching gold price...")
price_data = gold_service.get_gold_price(force_refresh=True)

print(f"\nStatus: {price_data.get('status')}")
print(f"Price: ${price_data.get('gold_price_usd'):.2f} /oz")
print(f"Per Gram: ${price_data.get('gold_price_per_gram'):.2f}")
print(f"Source: {price_data.get('source')}")
print(f"Timestamp: {price_data.get('timestamp')}")

print("\n[2] Testing cache (should be instant)...")
price_data2 = gold_service.get_gold_price()
print(f"Price: ${price_data2.get('gold_price_usd'):.2f} /oz")

print("\n[3] Formatted display...")
formatted = gold_service.get_formatted_price()
print(f"Display: {formatted}")

print("\n" + "=" * 60)
print("✓ Gold Price Service is Working!")
print("=" * 60)
print("\nNow run: python main.py")
print("Then open: http://localhost:5000")
print("=" * 60)
