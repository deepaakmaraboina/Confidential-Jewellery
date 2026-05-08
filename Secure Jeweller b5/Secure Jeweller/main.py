import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from tinydb import TinyDB, Query
from datetime import datetime
from functools import wraps
import io
import threading
import time
import json

from hill import hill_encrypt, hill_decrypt, encrypt_file_content, decrypt_file_content
from gold_price_service import get_gold_service

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'jewellery-secret-key-2024')
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize gold price service
gold_service = get_gold_service()

db = TinyDB('database.json')
users_table = db.table('users')
submissions_table = db.table('submissions')
messages_table = db.table('messages')
files_table = db.table('files')
logs_table = db.table('logs')
feedback_table = db.table('feedback')
images_table = db.table('images')

UPLOAD_FOLDER = 'uploads'
ENCRYPTED_FOLDER = 'encrypted'
CUSTOMER_IMAGES_FOLDER = 'static/customer_images'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
os.makedirs(CUSTOMER_IMAGES_FOLDER, exist_ok=True)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to access this page.', 'warning')
                return redirect(url_for('login'))
            if session.get('role') != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_action(user_id, action, details=""):
    logs_table.insert({
        'user_id': user_id,
        'action': action,
        'details': details,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        role = request.form.get('role')
        
        User = Query()
        if users_table.search(User.email == email):
            flash('Email already registered!', 'danger')
            return redirect(url_for('signup'))
        
        users_table.insert({
            'name': name,
            'email': email,
            'password': generate_password_hash(password),
            'phone': phone,
            'address': address,
            'role': role,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        })
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        User = Query()
        user = users_table.search(User.email == email)
        
        if user and check_password_hash(user[0]['password'], password):
            session['user_id'] = user[0].doc_id
            session['name'] = user[0]['name']
            session['email'] = user[0]['email']
            session['role'] = user[0]['role']
            
            log_action(user[0].doc_id, 'login', f"User {email} logged in")
            flash(f'Welcome back, {user[0]["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_action(session['user_id'], 'logout', f"User {session['email']} logged out")
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ==================== PASSWORD RESET ROUTES ====================

reset_requests_table = db.table('reset_requests')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        User = Query()
        user = users_table.search(User.email == email)
        
        if user:
            # Create a reset request
            reset_requests_table.insert({
                'user_id': user[0].doc_id,
                'email': email,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            })
            flash('Password reset request submitted. Please wait for administrator approval.', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email not found!', 'danger')
    
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('password')
        
        User = Query()
        user = users_table.search(User.email == email)
        
        if not user:
            flash('Email not found!', 'danger')
            return redirect(url_for('reset_password'))
            
        ResetRequest = Query()
        # Find approved request for this user
        request_entry = reset_requests_table.search(
            (ResetRequest.email == email) & (ResetRequest.status == 'approved')
        )
        
        if request_entry:
            # Update password
            users_table.update({
                'password': generate_password_hash(new_password)
            }, doc_ids=[user[0].doc_id])
            
            # Remove the request (or mark as completed)
            reset_requests_table.remove(doc_ids=[request_entry[0].doc_id])
            
            log_action(user[0].doc_id, 'reset_password', "Password reset successfully")
            flash('Password has been reset successfully! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('No approved reset request found for this email.', 'warning')
            
    return render_template('reset_password.html')

@app.route('/admin/password_requests')
@role_required('administrator')
def admin_password_requests():
    requests = reset_requests_table.all()
    # Join with user details if needed, for now just show email
    return render_template('admin/password_requests.html', requests=requests)

@app.route('/admin/password_requests/approve/<int:req_id>', methods=['POST'])
@role_required('administrator')
def admin_approve_password_request(req_id):
    reset_requests_table.update({
        'status': 'approved',
        'approved_at': datetime.now().isoformat()
    }, doc_ids=[req_id])
    
    flash('Password reset request approved.', 'success')
    return redirect(url_for('admin_password_requests'))

@app.route('/admin/password_requests/reject/<int:req_id>', methods=['POST'])
@role_required('administrator')
def admin_reject_password_request(req_id):
    reset_requests_table.remove(doc_ids=[req_id])
    flash('Password reset request rejected/deleted.', 'warning')
    return redirect(url_for('admin_password_requests'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'administrator':
        return redirect(url_for('admin_dashboard'))
    elif role == 'jewellery_owner':
        return redirect(url_for('owner_dashboard'))
    else:
        return redirect(url_for('customer_dashboard'))

@app.route('/admin/dashboard')
@role_required('administrator')
def admin_dashboard():
    users = users_table.all()
    submissions = submissions_table.all()
    return render_template('admin/dashboard.html', users=users, submissions=submissions)

@app.route('/admin/users')
@role_required('administrator')
def admin_users():
    users = users_table.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/delete/<int:user_id>')
@role_required('administrator')
def admin_delete_user(user_id):
    users_table.remove(doc_ids=[user_id])
    log_action(session['user_id'], 'delete_user', f"Deleted user ID: {user_id}")
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/submissions')
@role_required('administrator')
def admin_submissions():
    submissions = submissions_table.all()
    return render_template('admin/submissions.html', submissions=submissions)

@app.route('/admin/submissions/approve/<int:sub_id>', methods=['POST'])
@role_required('administrator')
def admin_approve_submission(sub_id):
    submissions_table.update({
        'status': 'approved',
        'approved_by': session['user_id'],
        'approved_at': datetime.now().isoformat()
    }, doc_ids=[sub_id])
    
    log_action(session['user_id'], 'approve_submission', f"Approved submission {sub_id}")
    flash('Submission approved successfully!', 'success')
    return redirect(url_for('admin_submissions'))

@app.route('/admin/submissions/reject/<int:sub_id>', methods=['POST'])
@role_required('administrator')
def admin_reject_submission(sub_id):
    rejection_reason = request.form.get('rejection_reason', '')
    submissions_table.update({
        'status': 'rejected',
        'rejected_by': session['user_id'],
        'rejected_at': datetime.now().isoformat(),
        'rejection_reason': rejection_reason
    }, doc_ids=[sub_id])
    
    log_action(session['user_id'], 'reject_submission', f"Rejected submission {sub_id}")
    flash('Submission rejected.', 'warning')
    return redirect(url_for('admin_submissions'))

@app.route('/admin/resolution')
@role_required('administrator')
def admin_resolution():
    submissions = submissions_table.all()
    return render_template('admin/resolution.html', submissions=submissions)

@app.route('/admin/resolution/update/<int:sub_id>', methods=['POST'])
@role_required('administrator')
def admin_update_resolution(sub_id):
    status = request.form.get('status')
    resolution_notes = request.form.get('resolution_notes')
    
    submissions_table.update({
        'status': status,
        'resolution_notes': resolution_notes,
        'resolved_at': datetime.now().isoformat() if status == 'resolved' else None
    }, doc_ids=[sub_id])
    
    log_action(session['user_id'], 'update_resolution', f"Updated submission {sub_id} to {status}")
    flash('Resolution updated successfully!', 'success')
    return redirect(url_for('admin_resolution'))

@app.route('/admin/logs')
@role_required('administrator')
def admin_logs():
    logs = logs_table.all()
    logs.reverse()
    return render_template('admin/logs.html', logs=logs)

@app.route('/admin/reports')
@role_required('administrator')
def admin_reports():
    users = users_table.all()
    submissions = submissions_table.all()
    
    stats = {
        'total_users': len(users),
        'total_submissions': len(submissions),
        'pending': len([s for s in submissions if s.get('status') == 'pending']),
        'in_progress': len([s for s in submissions if s.get('status') == 'in_progress']),
        'resolved': len([s for s in submissions if s.get('status') == 'resolved']),
        'administrators': len([u for u in users if u.get('role') == 'administrator']),
        'owners': len([u for u in users if u.get('role') == 'jewellery_owner']),
        'customers': len([u for u in users if u.get('role') == 'customer'])
    }
    
    return render_template('admin/reports.html', stats=stats)

@app.route('/owner/dashboard')
@role_required('jewellery_owner')
def owner_dashboard():
    Submission = Query()
    submissions = submissions_table.search(Submission.owner_id == session['user_id'])
    return render_template('owner/dashboard.html', submissions=submissions)

@app.route('/owner/submit', methods=['GET', 'POST'])
@role_required('jewellery_owner')
def owner_submit():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        jewellery_type = request.form.get('jewellery_type')
        weight = request.form.get('weight')
        material = request.form.get('material')
        estimated_value = request.form.get('estimated_value')
        
        submissions_table.insert({
            'owner_id': session['user_id'],
            'owner_name': session['name'],
            'title': title,
            'description': description,
            'jewellery_type': jewellery_type,
            'weight': weight,
            'material': material,
            'estimated_value': estimated_value,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        })
        
        log_action(session['user_id'], 'submit_jewellery', f"Submitted: {title}")
        flash('Jewellery submission created successfully!', 'success')
        return redirect(url_for('owner_dashboard'))
    
    return render_template('owner/submit.html')

@app.route('/owner/track')
@role_required('jewellery_owner')
def owner_track():
    Submission = Query()
    submissions = submissions_table.search(Submission.owner_id == session['user_id'])
    return render_template('owner/track.html', submissions=submissions)

@app.route('/owner/communication')
@role_required('jewellery_owner')
def owner_communication():
    Message = Query()
    messages = messages_table.search(
        (Message.sender_id == session['user_id']) | 
        (Message.receiver_id == session['user_id'])
    )
    
    User = Query()
    customers = users_table.search(User.role == 'customer')
    admins = users_table.search(User.role == 'administrator')
    
    return render_template('owner/communication.html', 
                         messages=messages, 
                         customers=customers,
                         admins=admins)

@app.route('/owner/send_message', methods=['POST'])
@role_required('jewellery_owner')
def owner_send_message():
    receiver_id = int(request.form.get('receiver_id'))
    content = request.form.get('content')
    is_encrypted = request.form.get('encrypt') == 'on'
    
    if is_encrypted:
        encrypted_content = hill_encrypt(content)
    else:
        encrypted_content = content
    
    messages_table.insert({
        'sender_id': session['user_id'],
        'sender_name': session['name'],
        'receiver_id': receiver_id,
        'content': encrypted_content,
        'original_content': content if is_encrypted else None,
        'is_encrypted': is_encrypted,
        'timestamp': datetime.now().isoformat()
    })
    
    log_action(session['user_id'], 'send_message', f"Sent message to user {receiver_id}")
    flash('Message sent successfully!', 'success')
    return redirect(url_for('owner_communication'))

@app.route('/owner/files', methods=['GET', 'POST'])
@role_required('jewellery_owner')
def owner_files():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!', 'danger')
            return redirect(url_for('owner_files'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'danger')
            return redirect(url_for('owner_files'))
        
        recipient_id = request.form.get('recipient_id')
        description = request.form.get('description')
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        original_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{filename}")
        file.save(original_path)
        
        with open(original_path, 'rb') as f:
            original_content = f.read()
        
        encrypted_content = encrypt_file_content(original_content)
        encrypted_filename = f"encrypted_{timestamp}_{filename}.enc"
        encrypted_path = os.path.join(ENCRYPTED_FOLDER, encrypted_filename)
        
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_content)
        
        files_table.insert({
            'owner_id': session['user_id'],
            'owner_name': session['name'],
            'recipient_id': int(recipient_id) if recipient_id else None,
            'original_filename': filename,
            'original_path': original_path,
            'encrypted_filename': encrypted_filename,
            'encrypted_path': encrypted_path,
            'description': description,
            'uploaded_at': datetime.now().isoformat()
        })
        
        log_action(session['user_id'], 'upload_file', f"Uploaded and encrypted: {filename}")
        flash('File uploaded and encrypted successfully!', 'success')
        return redirect(url_for('owner_files'))
    
    File = Query()
    files = files_table.search(File.owner_id == session['user_id'])
    
    User = Query()
    customers = users_table.search(User.role == 'customer')
    
    return render_template('owner/files.html', files=files, customers=customers)

@app.route('/owner/download_encrypted/<int:file_id>')
@role_required('jewellery_owner')
def owner_download_encrypted(file_id):
    file_record = files_table.get(doc_id=file_id)
    if file_record and file_record['owner_id'] == session['user_id']:
        return send_file(file_record['encrypted_path'], 
                        as_attachment=True,
                        download_name=file_record['encrypted_filename'])
    flash('File not found!', 'danger')
    return redirect(url_for('owner_files'))

@app.route('/owner/profile', methods=['GET', 'POST'])
@role_required('jewellery_owner')
def owner_profile():
    User = Query()
    user = users_table.get(doc_id=session['user_id'])
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        users_table.update({
            'name': name,
            'phone': phone,
            'address': address
        }, doc_ids=[session['user_id']])
        
        session['name'] = name
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('owner_profile'))
    
    return render_template('owner/profile.html', user=user)

@app.route('/customer/dashboard')
@role_required('customer')
def customer_dashboard():
    Submission = Query()
    submissions = submissions_table.search(Submission.status == 'approved')
    return render_template('customer/dashboard.html', submissions=submissions)

@app.route('/customer/browse')
@role_required('customer')
def customer_browse():
    Submission = Query()
    submissions = submissions_table.search(Submission.status == 'approved')
    return render_template('customer/browse.html', submissions=submissions)

@app.route('/customer/feedback', methods=['GET', 'POST'])
@role_required('customer')
def customer_feedback():
    if request.method == 'POST':
        submission_id = request.form.get('submission_id')
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        
        feedback_table.insert({
            'customer_id': session['user_id'],
            'customer_name': session['name'],
            'submission_id': int(submission_id) if submission_id else None,
            'rating': int(rating),
            'comment': comment,
            'created_at': datetime.now().isoformat()
        })
        
        log_action(session['user_id'], 'submit_feedback', f"Submitted feedback for submission {submission_id}")
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('customer_feedback'))
    
    Submission = Query()
    submissions = submissions_table.search(Submission.status == 'approved')
    Feedback = Query()
    my_feedback = feedback_table.search(Feedback.customer_id == session['user_id'])
    
    return render_template('customer/feedback.html', submissions=submissions, my_feedback=my_feedback)

@app.route('/customer/status')
@role_required('customer')
def customer_status():
    Feedback = Query()
    my_feedback = feedback_table.search(Feedback.customer_id == session['user_id'])
    
    Submission = Query()
    submissions = submissions_table.search(Submission.status == 'approved')
    
    return render_template('customer/status.html', submissions=submissions, my_feedback=my_feedback)

@app.route('/customer/files')
@role_required('customer')
def customer_files():
    File = Query()
    files = files_table.search(File.recipient_id == session['user_id'])
    
    return render_template('customer/files.html', files=files)

@app.route('/customer/download_encrypted/<int:file_id>')
@role_required('customer')
def customer_download_encrypted(file_id):
    file_record = files_table.get(doc_id=file_id)
    if file_record and file_record['recipient_id'] == session['user_id']:
        return send_file(file_record['encrypted_path'], 
                        as_attachment=True,
                        download_name=file_record['encrypted_filename'])
    flash('File not found or access denied!', 'danger')
    return redirect(url_for('customer_files'))

@app.route('/customer/download_decrypted/<int:file_id>')
@role_required('customer')
def customer_download_decrypted(file_id):
    file_record = files_table.get(doc_id=file_id)
    if file_record and file_record['recipient_id'] == session['user_id']:
        with open(file_record['encrypted_path'], 'rb') as f:
            encrypted_content = f.read()
        
        decrypted_content = decrypt_file_content(encrypted_content)
        
        buffer = io.BytesIO()
        buffer.write(decrypted_content)
        buffer.seek(0)
        
        log_action(session['user_id'], 'download_decrypted', f"Downloaded decrypted: {file_record['original_filename']}")
        
        return send_file(buffer, 
                        as_attachment=True,
                        download_name=file_record['original_filename'],
                        mimetype='application/octet-stream')
    flash('File not found or access denied!', 'danger')
    return redirect(url_for('customer_files'))

@app.route('/customer/profile', methods=['GET', 'POST'])
@role_required('customer')
def customer_profile():
    user = users_table.get(doc_id=session['user_id'])
    Image = Query()
    customer_images = images_table.search(Image.customer_id == session['user_id'])
    
    if request.method == 'POST':
        # Handle profile update
        if 'name' in request.form:
            name = request.form.get('name')
            phone = request.form.get('phone')
            address = request.form.get('address')
            
            users_table.update({
                'name': name,
                'phone': phone,
                'address': address
            }, doc_ids=[session['user_id']])
            
            session['name'] = name
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('customer_profile'))
        
        # Handle image upload
        if 'image' in request.files:
            image_file = request.files['image']
            image_description = request.form.get('image_description', '')
            
            if image_file.filename == '':
                flash('No image selected!', 'danger')
                return redirect(url_for('customer_profile'))
            
            if not allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                flash('Invalid file type. Allowed: png, jpg, jpeg, gif, webp', 'danger')
                return redirect(url_for('customer_profile'))
            
            filename = secure_filename(image_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_filename = f"{session['user_id']}_{timestamp}_{filename}"
            image_path = os.path.join(CUSTOMER_IMAGES_FOLDER, unique_filename)
            
            image_file.save(image_path)
            
            images_table.insert({
                'customer_id': session['user_id'],
                'customer_name': session['name'],
                'filename': unique_filename,
                'original_filename': filename,
                'image_path': image_path,
                'description': image_description,
                'uploaded_at': datetime.now().isoformat()
            })
            
            log_action(session['user_id'], 'upload_item_image', f"Uploaded item image: {filename}")
            flash('Item image uploaded successfully!', 'success')
            return redirect(url_for('customer_profile'))
    
    return render_template('customer/profile.html', user=user, customer_images=customer_images)

@app.route('/customer/image/delete/<int:image_id>', methods=['POST'])
@role_required('customer')
def customer_delete_image(image_id):
    image_record = images_table.get(doc_id=image_id)
    
    if image_record and image_record['customer_id'] == session['user_id']:
        # Delete file from disk
        if os.path.exists(image_record['image_path']):
            os.remove(image_record['image_path'])
        
        # Delete from database
        images_table.remove(doc_ids=[image_id])
        
        log_action(session['user_id'], 'delete_item_image', f"Deleted item image: {image_record['original_filename']}")
        flash('Item image deleted successfully!', 'success')
    else:
        flash('Image not found or access denied!', 'danger')
    
    return redirect(url_for('customer_profile'))

@app.route('/customer/communication')
@role_required('customer')
def customer_communication():
    Message = Query()
    messages = messages_table.search(
        (Message.sender_id == session['user_id']) | 
        (Message.receiver_id == session['user_id'])
    )
    
    User = Query()
    owners = users_table.search(User.role == 'jewellery_owner')
    admins = users_table.search(User.role == 'administrator')
    
    return render_template('customer/communication.html', 
                         messages=messages, 
                         owners=owners,
                         admins=admins)

@app.route('/customer/send_message', methods=['POST'])
@role_required('customer')
def customer_send_message():
    receiver_id = int(request.form.get('receiver_id'))
    content = request.form.get('content')
    is_encrypted = request.form.get('encrypt') == 'on'
    
    if is_encrypted:
        encrypted_content = hill_encrypt(content)
    else:
        encrypted_content = content
    
    messages_table.insert({
        'sender_id': session['user_id'],
        'sender_name': session['name'],
        'receiver_id': receiver_id,
        'content': encrypted_content,
        'original_content': content if is_encrypted else None,
        'is_encrypted': is_encrypted,
        'timestamp': datetime.now().isoformat()
    })
    
    log_action(session['user_id'], 'send_message', f"Sent message to user {receiver_id}")
    flash('Message sent successfully!', 'success')
    return redirect(url_for('customer_communication'))

@app.route('/decrypt_message/<int:msg_id>')
@login_required
def decrypt_message(msg_id):
    message = messages_table.get(doc_id=msg_id)
    if message and (message['sender_id'] == session['user_id'] or message['receiver_id'] == session['user_id']):
        if message['is_encrypted']:
            decrypted = hill_decrypt(message['content'])
            return {'decrypted': decrypted, 'original': message.get('original_content', decrypted)}
    return {'error': 'Access denied'}, 403

# ==================== GOLD PRICE ROUTES ====================

@app.route('/api/gold-price')
@login_required
def api_gold_price():
    """Get current gold price as JSON"""
    price_data = gold_service.get_gold_price()
    return jsonify(price_data)

@app.route('/api/gold-price/refresh')
@login_required
def api_gold_price_refresh():
    """Force refresh gold price from API"""
    price_data = gold_service.get_gold_price(force_refresh=True)
    return jsonify(price_data)

# ==================== WEBSOCKET ROUTES ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if 'user_id' in session:
        try:
            price_data = gold_service.get_gold_price()
            print(f"[WebSocket] New client connected - user_id: {session.get('user_id')}, price: {price_data.get('gold_price_usd', 'N/A')}/oz")
            emit('connection_response', {
                'data': 'Connected to gold price updates',
                'user_id': session.get('user_id'),
                'username': session.get('name')
            })
            # Send initial gold price to the newly connected client
            emit('gold_price_update', price_data)
        except Exception as e:
            print(f"Error during connection: {e}")
            emit('connection_response', {
                'data': 'Connected but error getting gold price',
                'error': str(e)
            })
    return False

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    pass

@socketio.on('request_gold_price')
def handle_gold_price_request():
    """Handle gold price update request from client"""
    try:
        price_data = gold_service.get_gold_price()
        print(f"[WebSocket] Client requested price: {price_data.get('gold_price_usd', 'N/A')}/oz")
        emit('gold_price_update', price_data)
    except Exception as e:
        print(f"Error handling gold price request: {e}")
        emit('gold_price_update', {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('request_gold_price_refresh')
def handle_gold_price_refresh():
    """Handle forced gold price refresh request"""
    try:
        price_data = gold_service.get_gold_price(force_refresh=True)
        print(f"[WebSocket] Client force-refreshed price: {price_data.get('gold_price_usd', 'N/A')}/oz")
        emit('gold_price_update', price_data, broadcast=True)
    except Exception as e:
        print(f"Error handling gold price refresh: {e}")
        emit('gold_price_update', {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        })

# ==================== BACKGROUND TASKS ====================

def emit_gold_price_updates():
    """Background task to emit gold price updates every 30 seconds"""
    while True:
        try:
            time.sleep(30)  # Update every 30 seconds for more frequent updates
            price_data = gold_service.get_gold_price()
            print(f"[Gold Price] Broadcasting update: {price_data.get('gold_price_usd', 'N/A')}/oz")
            # Use app context for background thread
            with app.app_context():
                socketio.emit('gold_price_update', price_data, broadcast=True, skip_sid=None)
        except Exception as e:
            print(f"Error emitting gold price update: {e}")
            continue

# Start background task in a separate thread
gold_price_thread = threading.Thread(target=emit_gold_price_updates, daemon=True)
gold_price_thread.start()
print("[Gold Price] Background update thread started")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
