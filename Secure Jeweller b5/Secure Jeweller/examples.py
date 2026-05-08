"""
Example Usage - Gold Price Service Integration
This file demonstrates how to use the gold price service in your application
"""

# Example 1: Basic Usage in Flask Routes
# ========================================

from flask import jsonify
from gold_price_service import get_gold_service

gold_service = get_gold_service()

# Endpoint: Get gold price in a route
def example_route():
    price_data = gold_service.get_gold_price()
    return jsonify(price_data)


# Example 2: Calculate Jewelry Value
# ===================================

def calculate_jewelry_value(weight_in_grams: float):
    """Calculate jewelry value based on current gold price"""
    gold_service = get_gold_service()
    price_data = gold_service.get_gold_price()
    
    if price_data.get('status') == 'success':
        price_per_gram = price_data['gold_price_per_gram']
        total_value = weight_in_grams * price_per_gram
        
        return {
            'weight': weight_in_grams,
            'price_per_gram': price_per_gram,
            'total_value': total_value,
            'currency': 'USD'
        }
    else:
        return {'error': 'Unable to fetch gold price'}

# Usage:
# value = calculate_jewelry_value(10)  # 10 grams of gold
# print(f"Value: ${value['total_value']:.2f}")


# Example 3: Update Jewelry Submission with Price
# ================================================

def submit_jewelry_with_price(title, weight, material='gold'):
    """Submit jewelry item with current gold price"""
    gold_service = get_gold_service()
    price_data = gold_service.get_gold_price()
    
    submission = {
        'title': title,
        'weight': weight,
        'material': material,
        'value_at_submission': None,
        'gold_price_usd': None,
        'gold_price_timestamp': None,
        'status': 'pending'
    }
    
    if price_data.get('status') == 'success':
        price_per_gram = price_data['gold_price_per_gram']
        submission['value_at_submission'] = weight * price_per_gram
        submission['gold_price_usd'] = price_data['gold_price_usd']
        submission['gold_price_timestamp'] = price_data['timestamp']
    
    return submission

# Usage:
# jewelry = submit_jewelry_with_price('Gold Ring', 5)
# print(f"Estimated value: ${jewelry['value_at_submission']:.2f}")


# Example 4: Fetch Price Per Gram
# ================================

def get_gold_price_per_gram():
    """Simple function to get gold price per gram"""
    gold_service = get_gold_service()
    return gold_service.get_gold_price_per_gram()

# Usage:
# price = get_gold_price_per_gram()
# print(f"Gold price: ${price:.2f}/gram")


# Example 5: Fetch Price Per Troy Ounce
# ======================================

def get_gold_price_per_oz():
    """Get gold price per troy ounce"""
    gold_service = get_gold_service()
    return gold_service.get_gold_price_per_oz()

# Usage:
# price = get_gold_price_per_oz()
# print(f"Gold price: ${price:.2f}/oz")


# Example 6: Error Handling
# ==========================

def safe_get_gold_price():
    """Get gold price with proper error handling"""
    try:
        gold_service = get_gold_service()
        price_data = gold_service.get_gold_price(force_refresh=True)
        
        if price_data.get('status') == 'success':
            return {
                'success': True,
                'price': price_data['gold_price_usd'],
                'source': price_data.get('source', 'unknown'),
                'timestamp': price_data['timestamp']
            }
        else:
            return {
                'success': False,
                'error': price_data.get('message', 'Unknown error'),
                'details': price_data.get('error')
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Usage:
# result = safe_get_gold_price()
# if result['success']:
#     print(f"Gold price: ${result['price']}")
# else:
#     print(f"Error: {result['error']}")


# Example 7: Database Integration
# ================================

def save_jewelry_with_price_snapshot(db, submission_data):
    """Save jewelry submission with price snapshot"""
    from datetime import datetime
    
    gold_service = get_gold_service()
    price_data = gold_service.get_gold_price()
    
    # Add price snapshot to submission
    if price_data.get('status') == 'success':
        submission_data['price_snapshot'] = {
            'gold_price_usd': price_data['gold_price_usd'],
            'gold_price_per_gram': price_data['gold_price_per_gram'],
            'source': price_data.get('source'),
            'captured_at': datetime.now().isoformat()
        }
    
    # Save to database
    result = db.table('submissions').insert(submission_data)
    return result


# Example 8: Price Comparison and Tracking
# =========================================

class GoldPriceTracker:
    """Track gold price changes over time"""
    
    def __init__(self, db):
        self.db = db
        self.price_history = db.table('gold_price_history')
        self.gold_service = get_gold_service()
    
    def record_price(self):
        """Record current gold price"""
        price_data = self.gold_service.get_gold_price(force_refresh=True)
        
        if price_data.get('status') == 'success':
            record = {
                'price_usd': price_data['gold_price_usd'],
                'price_per_gram': price_data['gold_price_per_gram'],
                'source': price_data.get('source'),
                'recorded_at': price_data['timestamp']
            }
            self.price_history.insert(record)
            return record
        return None
    
    def get_highest_price(self):
        """Get highest recorded price"""
        history = self.price_history.all()
        if history:
            highest = max(history, key=lambda x: x['price_usd'])
            return highest
        return None
    
    def get_lowest_price(self):
        """Get lowest recorded price"""
        history = self.price_history.all()
        if history:
            lowest = min(history, key=lambda x: x['price_usd'])
            return lowest
        return None
    
    def get_average_price(self):
        """Get average price from history"""
        history = self.price_history.all()
        if history:
            avg = sum(h['price_usd'] for h in history) / len(history)
            return avg
        return None

# Usage:
# from tinydb import TinyDB
# db = TinyDB('database.json')
# tracker = GoldPriceTracker(db)
# tracker.record_price()
# print(f"Average price: ${tracker.get_average_price():.2f}")


# Example 9: REST API Response Builder
# ====================================

def build_jewelry_response(jewelry_doc):
    """Build API response with current gold price"""
    gold_service = get_gold_service()
    price_data = gold_service.get_gold_price()
    
    response = {
        'id': jewelry_doc.doc_id,
        'title': jewelry_doc['title'],
        'type': jewelry_doc.get('jewellery_type'),
        'material': jewelry_doc.get('material'),
        'weight': jewelry_doc.get('weight'),
        'status': jewelry_doc.get('status'),
        'current_gold_price': None,
        'estimated_value': None
    }
    
    if price_data.get('status') == 'success':
        price_per_gram = price_data['gold_price_per_gram']
        response['current_gold_price'] = price_data['gold_price_usd']
        
        try:
            weight = float(jewelry_doc.get('weight', 0))
            response['estimated_value'] = weight * price_per_gram
        except (ValueError, TypeError):
            pass
    
    return response


# Example 10: Dashboard Statistics with Gold Price
# ================================================

def get_dashboard_stats(submissions):
    """Get dashboard stats including gold price context"""
    gold_service = get_gold_service()
    price_data = gold_service.get_gold_price()
    
    stats = {
        'total_submissions': len(submissions),
        'pending': len([s for s in submissions if s.get('status') == 'pending']),
        'approved': len([s for s in submissions if s.get('status') == 'approved']),
        'resolved': len([s for s in submissions if s.get('status') == 'resolved']),
        'gold_price_context': {}
    }
    
    if price_data.get('status') == 'success':
        stats['gold_price_context'] = {
            'current_price': price_data['gold_price_usd'],
            'currency': 'USD',
            'unit': 'per troy ounce',
            'source': price_data.get('source'),
            'updated_at': price_data['timestamp']
        }
        
        # Calculate total estimated value of submissions
        total_estimated_value = 0
        price_per_gram = price_data['gold_price_per_gram']
        
        for sub in submissions:
            try:
                weight = float(sub.get('weight', 0))
                total_estimated_value += weight * price_per_gram
            except (ValueError, TypeError):
                pass
        
        stats['total_estimated_value'] = total_estimated_value
    
    return stats

# Usage:
# stats = get_dashboard_stats(submissions)
# print(f"Total value: ${stats.get('total_estimated_value', 0):.2f}")


if __name__ == '__main__':
    # Run examples
    print("Gold Price Service Examples")
    print("=" * 50)
    
    # Example 1: Basic price fetch
    price_per_gram = get_gold_price_per_gram()
    print(f"Gold price per gram: ${price_per_gram:.2f}")
    
    # Example 2: Calculate jewelry value
    value = calculate_jewelry_value(10)
    print(f"Value of 10g gold: ${value['total_value']:.2f}")
    
    # Example 3: Safe error handling
    result = safe_get_gold_price()
    if result['success']:
        print(f"Gold price: ${result['price']:.2f}")
    
    print("\nSee comments in this file for more examples!")
