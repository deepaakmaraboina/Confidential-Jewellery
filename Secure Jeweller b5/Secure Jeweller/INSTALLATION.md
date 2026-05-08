# 🚀 Complete Installation & Setup Guide

**Real-Time Gold Price Integration for Jewellery Workflow System**

---

## 📋 PRE-INSTALLATION CHECKLIST

Before you start, make sure you have:
- [ ] Python 3.8 or higher installed
- [ ] pip package manager available
- [ ] Internet connection (for API calls)
- [ ] Access to project directory
- [ ] Visual Studio Code or similar editor (optional)

**Check Python Version:**
```bash
python --version
```

Should show `Python 3.8.0` or higher.

---

## ⚙️ STEP 1: INSTALL DEPENDENCIES

### Option A: Install All at Once (Recommended)
```bash
cd "C:\Users\Ramadevi\OneDrive\Desktop\B5 Jewellery\B5 Jewellery\Secure Jeweller"
pip install -r requirements.txt
```

### Option B: Install Individual Packages
```bash
pip install Flask==2.3.3
pip install flask-socketio==5.3.4
pip install python-socketio==5.9.0
pip install python-engineio==4.7.1
pip install TinyDB==4.8.0
pip install Werkzeug==2.3.7
pip install requests==2.31.0
pip install python-dotenv==1.0.0
```

### Verify Installation
```bash
pip list | findstr Flask
pip list | findstr socketio
```

You should see:
- Flask 2.3.3
- flask-socketio 5.3.4
- python-socketio 5.9.0

---

## ✅ STEP 2: VERIFY INSTALLATION

### Run the Test Script
This will verify everything is installed correctly:

```bash
python test_gold_price.py
```

**Expected Output:**
```
✓ TEST 1: Checking Required Imports - PASS
✓ TEST 2: Testing Gold Price Service - PASS
✓ TEST 3: Testing API Sources - PASS
✓ TEST 4: Testing Cache Mechanism - PASS
✓ TEST 5: Testing Flask App Configuration - PASS
✓ TEST 6: Testing API Endpoints - PASS

Total: 6/6 tests passed!
```

If any test fails, refer to the **Troubleshooting** section below.

---

## 🎯 STEP 3: RUN THE APPLICATION

### Start the Flask Server

**Windows (PowerShell):**
```powershell
python main.py
```

**Windows (Command Prompt):**
```cmd
python main.py
```

**Linux/Mac:**
```bash
python3 main.py
```

### Expected Console Output
```
 * Serving Flask app 'main'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
 * WARNING in werkzeug: This is a development server...
```

✅ Server is running when you see this message!

---

## 🌐 STEP 4: ACCESS THE APPLICATION

### Open in Browser
1. Go to: `http://localhost:5000`
2. You should see the Jewellery Workflow login page
3. Log in with your credentials

### Test Deployment

**Create test account (if needed):**
1. Click "Sign Up"
2. Fill in credentials
3. Select role: "customer" (for testing)
4. Click "Register"

**Log in:**
1. Use your credentials
2. Click "Login"

**Check Gold Price:**
1. You should be redirected to your dashboard
2. Look for the **Gold Price Card** (💰 symbol)
3. You should see a price like: `$2,035.50 /oz`

✅ If you see the gold price card with an actual price, your installation is successful!

---

## 🔍 STEP 5: VERIFY REAL-TIME UPDATES

### Test Real-Time Functionality

1. **Open dashboard** and note the gold price
2. **Wait 60 seconds** 
3. **Check the timestamp** below the price
4. **Time should have updated**

### Test in Multiple Tabs

1. **Open same dashboard in 2 browser tabs**
2. In browser console (F12), you might see WebSocket messages
3. **Wait 60 seconds**
4. **Both tabs should update together**

### Test Manual Refresh

1. **Open browser dev tools** (F12 → Console)
2. **Type:** `socket.emit('request_gold_price')`
3. **Press Enter**
4. **Price should update immediately**

✅ If any of these work, real-time updates are working!

---

## 📊 STEP 6: TEST ALL THREE DASHBOARDS

Create or log in as different role types and verify gold price appears:

### Administrator Dashboard
```
Log in as: Administrator user
URL: http://localhost:5000/admin/dashboard
Look for: Gold Price card at top
Expected: Price like "$2,035.50 /oz"
```

### Customer Dashboard
```
Log in as: Customer user
URL: http://localhost:5000/customer/dashboard
Look for: Gold Price card at top
Expected: Price like "$2,035.50 /oz"
```

### Owner Dashboard
```
Log in as: Jewellery Owner user
URL: http://localhost:5000/owner/dashboard
Look for: Gold Price card at top
Expected: Price like "$2,035.50 /oz"
```

✅ Gold price should appear on all three!

---

## 🐛 TROUBLESHOOTING

### Problem 1: "ModuleNotFoundError: No module named 'flask_socketio'"

**Solution:**
```bash
pip install flask-socketio==5.3.4
```

**If still failing:**
```bash
pip uninstall -y flask-socketio python-socketio python-engineio
pip install flask-socketio==5.3.4
```

### Problem 2: "Address already in use"

**Solution:** Change the port in `main.py` (last line):
```python
# Change from:
socketio.run(app, host='0.0.0.0', port=5000, debug=True)

# To:
socketio.run(app, host='0.0.0.0', port=8000, debug=True)
```

Then access at: `http://localhost:8000`

### Problem 3: Gold Price Shows "$---" (Not Updating)

**Possible Causes:**
- [ ] APIs are temporarily unavailable
- [ ] Internet connection issue
- [ ] Browser cache issue

**Solutions:**
```bash
# Restart the server:
1. Press Ctrl+C in terminal
2. Run: python main.py again

# Clear browser cache:
1. Press Ctrl+Shift+Delete
2. Clear cookies and cache
3. Reload page (F5)

# Test API directly:
# Open in browser:
http://localhost:5000/api/gold-price
# Should show JSON like:
# {"status": "success", "gold_price_usd": 2035.50, ...}
```

### Problem 4: WebSocket Connection Fails

**Check browser console (F12):**
- Should show: "Connected to real-time updates" ✓
- **If you see error:** Verify CORS in main.py:

```python
socketio = SocketIO(app, cors_allowed_origins="*")
```

**If still failing:**
- Windows Firewall might block port 5000
- Solution: Add Flask app to Windows Firewall whitelist

### Problem 5: "test_gold_price.py" Fails

**Run individually:**
```bash
# Test imports only:
python -c "from flask_socketio import SocketIO; print('OK')"

# Test gold service only:
python -c "from gold_price_service import GoldPriceService; print('OK')"

# Test main.py only:
python -c "import main; print('OK')"
```

**Each should print "OK"**

---

## 🔧 CONFIGURATION (Optional)

### Change Update Frequency
Edit `main.py` around line 690:
```python
time.sleep(60)  # Change to desired seconds
# time.sleep(30)  # For every 30 seconds
# time.sleep(300)  # For every 5 minutes
```

### Change Cache Duration
Edit `gold_price_service.py`:
```python
gold_service = GoldPriceService(cache_timeout=60)
# cache_timeout=120  # Cache for 2 minutes
# cache_timeout=300  # Cache for 5 minutes
```

### Change Server Port
Edit `main.py` (last line):
```python
socketio.run(app, host='0.0.0.0', port=5000, debug=True)
# Change 5000 to any other port (e.g., 8000, 3000)
```

---

## 📁 PROJECT STRUCTURE AFTER SETUP

```
Secure Jeweller/
├── main.py (MODIFIED - Added gold price routes)
├── gold_price_service.py (NEW - Gold price service)
├── examples.py (NEW - Code examples)
├── requirements.txt (NEW - Dependencies)
├── test_gold_price.py (NEW - Test script)
├── GOLD_PRICE_INTEGRATION.md (NEW - Full docs)
├── QUICKSTART.md (NEW - Quick start)
├── INSTALLATION.md (NEW - This file)
├── IMPLEMENTATION_SUMMARY.md (NEW - What changed)
├── hill.py (existing)
├── database.json (existing)
├── templates/
│   ├── base.html (MODIFIED - Added Socket.IO)
│   ├── admin/
│   │   └── dashboard.html (MODIFIED - Added gold price)
│   ├── customer/
│   │   └── dashboard.html (MODIFIED - Added gold price)
│   └── owner/
│       └── dashboard.html (MODIFIED - Added gold price)
├── static/
│   └── css/
│       └── style.css (MODIFIED - Added animations)
└── ...other files...
```

---

## 📝 WHAT WAS INSTALLED

### Python Packages
- **Flask 2.3.3** - Web framework
- **flask-socketio 5.3.4** - WebSocket support
- **python-socketio 5.9.0** - Socket.IO protocol
- **python-engineio 4.7.1** - Engine.IO protocol
- **requests 2.31.0** - HTTP library (for API calls)
- **TinyDB 4.8.0** - Database (already used)
- **Werkzeug 2.3.7** - WSGI utilities

### New Files Added
1. Gold price service module
2. Test script  
3. Documentation (4 files)
4. Example code file

### Files Modified
- main.py (API endpoints + WebSocket)
- base.html (Socket.IO + JavaScript)
- 3 dashboard templates (gold price cards)
- style.css (animations)

---

## ✨ FEATURES NOW ENABLED

✅ Real-time gold price on all dashboards
✅ Automatic updates every 60 seconds  
✅ Multiple API sources with fallback
✅ Price per troy ounce + per gram
✅ Real-time timestamp
✅ Beautiful loading animations
✅ WebSocket broadcasts to all users
✅ 60-second cache for efficiency
✅ Authentication required (secure)
✅ Production-ready code

---

## 🚀 NEXT STEPS

### After Successful Installation

1. **Read Quick Start:** `QUICKSTART.md`
2. **Review Documentation:** `GOLD_PRICE_INTEGRATION.md`
3. **Check Examples:** `examples.py`
4. **Customize:** Adjust frequencies/formats as needed
5. **Deploy:** Follow production guidelines

### Extend the System

Want to add more features? See `examples.py` for:
- Calculate jewelry value based on gold price
- Track price changes over time
- Create price alerts
- Export price history
- Multi-currency support

---

## 📞 QUICK REFERENCE

### Start Application
```bash
python main.py
```

### Stop Application
Press `Ctrl+C` in the terminal

### Run Tests
```bash
python test_gold_price.py
```

### Access Application
```
http://localhost:5000
```

### API Endpoints
```
GET /api/gold-price          - Get current price
GET /api/gold-price/refresh  - Force refresh
```

### Check Logs
- Look in terminal where you ran `python main.py`
- Check browser console (F12) for JavaScript errors

---

## 💡 TIPS

- 💾 **Save changes** in your files after customization
- 🔄 **Restart server** (Ctrl+C then `python main.py`) after changing code
- 🧹 **Clear browser cache** (Ctrl+Shift+Delete) if changes don't appear
- 📱 **Test mobile** by accessing `http://<your-ip>:5000` from phone
- 📊 **Monitor** the terminal for any error messages
- 🌐 **Check internet** if APIs aren't responding

---

## ✅ SUCCESS INDICATORS

You've successfully installed when you see:

1. ✅ Test script passes all 6 tests
2. ✅ Server starts without errors
3. ✅ Login page loads at `http://localhost:5000`
4. ✅ Gold price card appears on dashboard
5. ✅ Price shows actual value (not $--)
6. ✅ Timestamp updates every 60 seconds
7. ✅ No errors in browser console

---

## 📖 Documentation Files

After installation, read these in order:

1. **QUICKSTART.md** (5 min read)
   - Quick start guide
   - Basic usage
   - Common customizations

2. **GOLD_PRICE_INTEGRATION.md** (15 min read)
   - Complete technical reference
   - API documentation
   - Configuration options
   - Troubleshooting guide

3. **IMPLEMENTATION_SUMMARY.md** (10 min read)
   - What was changed
   - Files modified
   - Technology stack
   - Deployment notes

4. **examples.py** (Reference)
   - 10 real-world code examples
   - How to integrate with your code
   - Patterns and best practices

---

## 🎓 LEARNING PATH

### Beginner
1. Read QUICKSTART.md
2. Install dependencies
3. Run application
4. Test it works

### Intermediate
1. Read GOLD_PRICE_INTEGRATION.md
2. Look at examples.py
3. Try modifying configurations
4. Test API endpoints

### Advanced
1. Read source code in gold_price_service.py
2. Modify main.py to add features
3. Create custom extensions
4. Deploy to production

---

## 🎉 CONGRATULATIONS!

You have successfully installed the **Real-Time Gold Price Integration**!

Your jewellery workflow system now displays live gold prices on administrator, customer, and owner dashboards with automatic updates every 60 seconds.

**Enjoy! 💎✨**

---

**Last Updated:** February 9, 2026  
**Version:** 1.0  
**Status:** ✅ Production Ready
