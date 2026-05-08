# Real-Time Gold Price Integration - Implementation Guide

## Overview
This implementation adds real-time gold price tracking to your Jewellery Workflow System. The gold prices are displayed on all dashboards (Admin, Customer, and Owner) and update automatically every 60 seconds using WebSocket technology.

## Features

### 1. **Real-Time Price Updates**
- Gold price updates are pushed to all connected clients every 60 seconds
- WebSocket (Socket.IO) ensures bidirectional real-time communication
- No page refresh required

### 2. **Multiple API Sources with Fallback**
The system tries multiple APIs to ensure reliability:
- **metals.live**: Primary source for precious metal prices
- **metals-api.com**: Secondary source with free tier support
- **CoinDesk**: Tertiary source (Bitcoin price API also provides gold data)

### 3. **Price Display Metrics**
Each dashboard shows:
- **Gold Price per Troy Ounce** (USD) - Primary display
- **Gold Price per Gram** (USD) - Calculated automatically
- **Real-time Timestamp** - Shows when the price was last updated
- **Visual Loading State** - Animated loading indicator while fetching

### 4. **Dashboard Integration**
Gold price cards are integrated into:
- ✅ Administrator Dashboard
- ✅ Customer Dashboard
- ✅ Owner Dashboard

## Installation & Setup

### Step 1: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages:
```
Flask==2.3.3
flask-socketio==5.3.4
python-socketio==5.9.0
python-engineio==4.7.1
TinyDB==4.8.0
Werkzeug==2.3.7
requests==2.31.0
python-dotenv==1.0.0
```

### Step 2: Run the Application
```bash
python main.py
```

The application will start on `http://localhost:5000` with WebSocket support enabled.

## Files Modified/Created

### New Files:
1. **gold_price_service.py** - Core service for fetching gold prices
   - `GoldPriceService` class
   - Multiple API source handlers
   - Price caching mechanism (60-second cache)

2. **requirements.txt** - Python dependencies

### Modified Files:
1. **main.py**
   - Added Flask-SocketIO imports
   - Added gold price service integration
   - New routes: `/api/gold-price`, `/api/gold-price/refresh`
   - WebSocket handlers for real-time updates
   - Background thread for periodic price updates

2. **templates/base.html**
   - Added Socket.IO client library
   - Added real-time price update JavaScript
   - Gold price display update functions

3. **templates/admin/dashboard.html**
   - Added gold price stat card

4. **templates/customer/dashboard.html**
   - Added gold price stat card

5. **templates/owner/dashboard.html**
   - Added gold price stat card

6. **static/css/style.css**
   - Added loading animation for gold price
   - Added styling for gold price cards

## API Endpoints

### REST API Endpoints

#### Get Current Gold Price
```
GET /api/gold-price
```
**Response:**
```json
{
    "status": "success",
    "source": "metals.live",
    "gold_price_usd": 2035.50,
    "gold_price_per_gram": 65.42,
    "gold_price_per_oz": 2035.50,
    "currency": "USD",
    "timestamp": "2026-02-09T10:30:45.123456",
    "unit": "per troy ounce"
}
```

#### Force Refresh Gold Price
```
GET /api/gold-price/refresh
```
Bypasses cache and fetches fresh data from APIs.

### WebSocket Events

#### Client → Server Events
```javascript
// Request current gold price
socket.emit('request_gold_price');

// Force refresh gold price
socket.emit('request_gold_price_refresh');
```

#### Server → Client Events
```javascript
// Receive gold price update
socket.on('gold_price_update', function(data) {
    console.log('Gold Price:', data);
});

// Connection confirmation
socket.on('connection_response', function(data) {
    console.log('Connected:', data);
});
```

## Frontend Implementation

### Automatic Updates
The JavaScript in `base.html` handles:
1. **Initial Connection**: Fetches gold price when page loads
2. **Real-Time Updates**: Listens for server broadcasts every 60 seconds
3. **Display Updates**: Automatically updates all `.gold-price-value` elements
4. **Timestamp Updates**: Shows when price was last updated

### HTML Elements
The dashboard contains:
```html
<div class="stat-card success">
    <i class="fas fa-coins fa-2x mb-2"></i>
    <div class="stat-number gold-price-value loading">$---</div>
    <div>Gold Price /oz</div>
    <small class="d-block mt-2" data-gold-timestamp>Updating...</small>
</div>
```

### CSS Classes
- `.gold-price-value` - Main price display element
- `.loading` - Loading animation state
- `[data-gold-timestamp]` - Timestamp display element
- `.pulse` - Animation class for loading state

## Configuration

### Cache Timeout
The gold price service caches data for **60 seconds** to reduce API calls.

To modify cache duration in `gold_price_service.py`:
```python
gold_service = GoldPriceService(cache_timeout=120)  # 120 seconds
```

### Update Frequency
Background thread broadcasts updates every **60 seconds**.

To modify update frequency in `main.py`:
```python
time.sleep(60)  # Change to desired interval in seconds
```

### Port Configuration
Application runs on port **5000** by default.

To change in `main.py`:
```python
socketio.run(app, host='0.0.0.0', port=8000, debug=True)
```

## Error Handling

### Fallback Mechanism
If one API fails, the system automatically tries the next source:
1. metals.live fails → Try metals-api
2. metals-api fails → Try CoinDesk
3. All fail → Return cached price if available
4. No cache → Return error message

### Example Error Response
```json
{
    "status": "error",
    "message": "Unable to fetch gold price",
    "error": "Connection timeout",
    "timestamp": "2026-02-09T10:30:45.123456"
}
```

## Performance Considerations

### Optimization Features
1. **Caching**: 60-second cache reduces API calls
2. **WebSocket**: Efficient bidirectional communication
3. **Broadcast**: Single server message to all clients
4. **Daemon Thread**: Background updates don't block main application

### API Rate Limits
- metals.live: No documented rate limit for free tier
- metals-api: Free tier has reasonable limits
- CoinDesk: No special rate limit for free data

## Troubleshooting

### Gold Price Not Updating
1. Check browser console for WebSocket errors
2. Verify Flask-SocketIO is installed: `pip list | grep socketio`
3. Check if `/api/gold-price` endpoint returns data
4. Restart the Flask application

### WebSocket Connection Failed
1. Ensure CORS is enabled: `SocketIO(app, cors_allowed_origins="*")`
2. Check firewall/proxy settings
3. Verify Socket.IO library is loaded in browser

### API Fetch Failures
1. Check internet connection
2. Verify all three API sources are accessible
3. Check if APIs have rate limit restrictions
4. Enable debug logging in `gold_price_service.py`

## Security Considerations

1. **Authentication**: Gold price endpoints require login (`@login_required`)
2. **CORS**: Configured to allow safe cross-origin requests
3. **HTTPS**: Recommended for production deployments
4. **Rate Limiting**: Consider adding rate limits to API endpoints

## Production Deployment

### Recommendations
1. Use a production WSGI server (Gunicorn, uWSGI)
2. Use redis for session management
3. Enable HTTPS/TLS
4. Set `debug=False` in production
5. Use environment variables for configuration
6. Monitor WebSocket connections

### Example Gunicorn Command
```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 main:app
```

## Testing

### Manual Testing
1. Log in to any dashboard
2. Observe gold price card loading
3. Wait for price to update (within 60 seconds)
4. Check timestamp updates
5. Open multiple browser tabs - all should update together

### Browser Console Testing
```javascript
// Request price from console
socket.emit('request_gold_price');

// Check received data
socket.on('gold_price_update', (data) => console.log(data));

// Force refresh
socket.emit('request_gold_price_refresh');
```

## Future Enhancements

Potential improvements:
1. Add historical price charts using Chart.js
2. Implement price alerts (notify when gold reaches certain price)
3. Support multiple currencies (EUR, GBP, INR, etc.)
4. Add price calculation for jewelry items based on weight
5. Store historical prices in database for analysis
6. Add price comparison features
7. Export price history to CSV/PDF

## Support & Maintenance

For issues or questions:
1. Check the troubleshooting section above
2. Review Flask-SocketIO documentation: https://flask-socketio.readthedocs.io/
3. Check API documentation for unavailability

## Version History

### v1.0 (Current)
- Initial implementation
- Real-time gold price updates
- Multiple API sources with fallback
- Dashboard integration for all three roles
- WebSocket broadcasts
- Price caching mechanism
