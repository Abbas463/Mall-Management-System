from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    # Get statistics
    total_users = db.execute_query("SELECT COUNT(*) as count FROM users", fetch_one=True)['count']
    total_sales = db.execute_query("SELECT SUM(total_amount) as total FROM sales", fetch_one=True)['total'] or 0
    pending_warnings = db.execute_query("SELECT COUNT(*) as count FROM warnings WHERE status = 'active'", fetch_one=True)['count']
    unread_messages = db.execute_query(
        "SELECT COUNT(*) as count FROM messages WHERE is_admin_message = FALSE AND is_read = FALSE",
        fetch_one=True
    )['count']
    
    recent_users = db.execute_query("SELECT * FROM users ORDER BY created_at DESC LIMIT 5")
    recent_sales = db.execute_query("""
        SELECT s.*, u.full_name as user_name, u.shop_number 
        FROM sales s 
        JOIN users u ON s.user_id = u.id 
        ORDER BY s.date DESC LIMIT 5
    """)
    recent_payments = db.execute_query("""
        SELECT p.*, u.full_name, u.shop_number
        FROM payments p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.date DESC LIMIT 5
    """)
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_sales=total_sales,
                         pending_warnings=pending_warnings,
                         unread_messages=unread_messages,
                         recent_users=recent_users,
                         recent_sales=recent_sales,
                         recent_payments=recent_payments)

@admin_bp.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        shop_number = request.form['shop_number']
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')
        
        existing_user = db.execute_query(
            "SELECT * FROM users WHERE username = %s OR shop_number = %s",
            (username, shop_number),
            fetch_one=True
        )
        
        if existing_user:
            flash('Username or shop number already exists', 'danger')
        else:
            db.execute_query(
                "INSERT INTO users (username, password, full_name, shop_number, phone, email) VALUES (%s, %s, %s, %s, %s, %s)",
                (username, password, full_name, shop_number, phone, email)
            )
            flash('User added successfully', 'success')
            return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/add_user.html')

@admin_bp.route('/manage_users')
def manage_users():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    users = db.execute_query("SELECT * FROM users ORDER BY created_at DESC")
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    user = db.execute_query("SELECT * FROM users WHERE id = %s", (user_id,), fetch_one=True)
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        shop_number = request.form['shop_number']
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')
        
        existing_user = db.execute_query(
            "SELECT * FROM users WHERE (username = %s OR shop_number = %s) AND id != %s",
            (username, shop_number, user_id),
            fetch_one=True
        )
        
        if existing_user:
            flash('Username or shop number already exists for another user', 'danger')
        else:
            db.execute_query(
                "UPDATE users SET username = %s, password = %s, full_name = %s, shop_number = %s, phone = %s, email = %s WHERE id = %s",
                (username, password, full_name, shop_number, phone, email, user_id)
            )
            flash('User updated successfully', 'success')
            return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    db.execute_query("DELETE FROM users WHERE id = %s", (user_id,))
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/view_sales')
def view_sales():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    shop_filter = request.args.get('shop_number', '')
    
    query = """
        SELECT s.*, u.full_name as user_name, u.shop_number 
        FROM sales s 
        JOIN users u ON s.user_id = u.id
    """
    params = ()
    
    if shop_filter:
        query += " WHERE u.shop_number = %s"
        params = (shop_filter,)
    
    query += " ORDER BY s.date DESC"
    
    sales = db.execute_query(query, params)
    shops = db.execute_query("SELECT shop_number FROM users ORDER BY shop_number")
    
    return render_template('admin/view_sales.html', sales=sales, shops=shops, selected_shop=shop_filter)

@admin_bp.route('/send_warning', methods=['GET', 'POST'])
def send_warning():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        warning_type = request.form['type']
        amount = float(request.form['amount'])
        message = request.form['message']
        
        db.execute_query(
            "INSERT INTO warnings (user_id, type, amount, message) VALUES (%s, %s, %s, %s)",
            (user_id, warning_type, amount, message)
        )
        
        db.execute_query(
            "INSERT INTO payments (user_id, type, amount) VALUES (%s, %s, %s)",
            (user_id, warning_type, amount)
        )
        
        flash('Warning sent successfully', 'success')
        return redirect(url_for('admin.dashboard'))
    
    users = db.execute_query("SELECT id, full_name, shop_number FROM users ORDER BY full_name")
    return render_template('admin/send_warning.html', users=users)

@admin_bp.route('/send_message_to_user', methods=['GET', 'POST'])
def send_message_to_user():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        message = request.form['message']
        
        db.execute_query(
            "INSERT INTO messages (sender_id, receiver_id, message, is_admin_message) VALUES (%s, %s, %s, TRUE)",
            (session['admin_id'], user_id, message)
        )
        flash('Message sent successfully', 'success')
        return redirect(url_for('admin.view_messages'))
    
    users = db.execute_query("SELECT id, full_name, shop_number FROM users ORDER BY full_name")
    return render_template('admin/send_message_to_user.html', users=users)

@admin_bp.route('/view_messages')
def view_messages():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    # Mark messages as read
    db.execute_query(
        "UPDATE messages SET is_read = TRUE WHERE is_admin_message = FALSE"
    )
    
    messages = db.execute_query("""
        SELECT m.*, u.full_name as user_name, u.shop_number 
        FROM messages m
        JOIN users u ON m.receiver_id = u.id
        WHERE m.is_admin_message = FALSE
        ORDER BY m.date DESC
    """)
    return render_template('admin/view_messages.html', messages=messages)

@admin_bp.route('/mark_payment_paid/<int:payment_id>')
def mark_payment_paid(payment_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    payment = db.execute_query("SELECT * FROM payments WHERE id = %s", (payment_id,), fetch_one=True)
    if payment:
        db.execute_query(
            "UPDATE payments SET status = 'paid', date = %s WHERE id = %s",
            (datetime.now(), payment_id)
        )
        
        db.execute_query(
            "UPDATE users SET balance = balance - %s WHERE id = %s",
            (payment['amount'], payment['user_id'])
        )
        
        db.execute_query(
            "UPDATE warnings SET status = 'resolved' WHERE user_id = %s AND type = %s AND amount = %s AND status = 'active'",
            (payment['user_id'], payment['type'], payment['amount'])
        )
        
        flash('Payment marked as paid', 'success')
    
    return redirect(url_for('admin.view_payments'))

@admin_bp.route('/view_payments')
def view_payments():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    payments = db.execute_query("""
        SELECT p.*, u.full_name, u.shop_number 
        FROM payments p 
        JOIN users u ON p.user_id = u.id 
        ORDER BY p.date DESC
    """)
    
    return render_template('admin/view_payments.html', payments=payments)