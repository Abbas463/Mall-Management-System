from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get statistics
    total_sales = db.execute_query(
        "SELECT SUM(total_amount) as total FROM sales WHERE user_id = %s",
        (user_id,),
        fetch_one=True
    )['total'] or 0
    
    active_warnings = db.execute_query(
        "SELECT COUNT(*) as count FROM warnings WHERE user_id = %s AND status = 'active'",
        (user_id,),
        fetch_one=True
    )['count']
    
    unread_messages = db.execute_query(
        "SELECT COUNT(*) as count FROM messages WHERE receiver_id = %s AND is_read = FALSE",
        (user_id,),
        fetch_one=True
    )['count']
    
    recent_sales = db.execute_query(
        "SELECT * FROM sales WHERE user_id = %s ORDER BY date DESC LIMIT 5",
        (user_id,)
    )
    
    payments = db.execute_query(
        "SELECT * FROM payments WHERE user_id = %s ORDER BY date DESC LIMIT 5",
        (user_id,)
    )
    
    return render_template('user/dashboard.html',
                         total_sales=total_sales,
                         active_warnings=active_warnings,
                         unread_messages=unread_messages,
                         recent_sales=recent_sales,
                         payments=payments)

@user_bp.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        name = request.form['name']
        
        # Check if category already exists for this user
        existing_category = db.execute_query(
            "SELECT * FROM categories WHERE name = %s AND user_id = %s",
            (name, user_id),
            fetch_one=True
        )
        
        if existing_category:
            flash('Category already exists', 'danger')
        else:
            db.execute_query(
                "INSERT INTO categories (name, user_id) VALUES (%s, %s)",
                (name, user_id)
            )
            flash('Category added successfully', 'success')
            return redirect(url_for('user.add_category'))
    
    categories = db.execute_query(
        "SELECT * FROM categories WHERE user_id = %s ORDER BY name",
        (user_id,)
    )
    
    return render_template('user/add_category.html', categories=categories)

@user_bp.route('/delete_category/<int:category_id>')
def delete_category(category_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Verify the category belongs to the user
    category = db.execute_query(
        "SELECT * FROM categories WHERE id = %s AND user_id = %s",
        (category_id, user_id),
        fetch_one=True
    )
    
    if not category:
        flash('Category not found or unauthorized', 'danger')
    else:
        db.execute_query(
            "DELETE FROM categories WHERE id = %s",
            (category_id,)
        )
        flash('Category deleted successfully', 'success')
    
    return redirect(url_for('user.add_category'))

@user_bp.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Handle product edit
    product_id = request.args.get('edit', type=int)
    product = None
    if product_id:
        product = db.execute_query(
            "SELECT * FROM products WHERE id = %s AND user_id = %s",
            (product_id, user_id),
            fetch_one=True
        )
        if not product:
            flash('Product not found or unauthorized', 'danger')
            return redirect(url_for('user.add_product'))
    
    if request.method == 'POST':
        name = request.form['name']
        category_id = request.form['category_id']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        
        # Verify category belongs to user
        category = db.execute_query(
            "SELECT * FROM categories WHERE id = %s AND user_id = %s",
            (category_id, user_id),
            fetch_one=True
        )
        
        if not category:
            flash('Invalid category selected', 'danger')
        else:
            if product_id:  # Update existing product
                db.execute_query(
                    "UPDATE products SET name = %s, category_id = %s, price = %s, stock = %s WHERE id = %s",
                    (name, category_id, price, stock, product_id)
                )
                flash('Product updated successfully', 'success')
            else:  # Add new product
                db.execute_query(
                    "INSERT INTO products (name, category_id, price, stock, user_id) VALUES (%s, %s, %s, %s, %s)",
                    (name, category_id, price, stock, user_id)
                )
                flash('Product added successfully', 'success')
            return redirect(url_for('user.add_product'))
    
    categories = db.execute_query(
        "SELECT * FROM categories WHERE user_id = %s ORDER BY name",
        (user_id,)
    )
    
    products = db.execute_query("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        JOIN categories c ON p.category_id = c.id 
        WHERE p.user_id = %s 
        ORDER BY p.name
    """, (user_id,))
    
    return render_template('user/add_product.html', 
                         categories=categories, 
                         products=products,
                         product=product)

@user_bp.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Verify product belongs to user
    product = db.execute_query(
        "SELECT * FROM products WHERE id = %s AND user_id = %s",
        (product_id, user_id),
        fetch_one=True
    )
    
    if not product:
        flash('Product not found or unauthorized', 'danger')
    else:
        db.execute_query(
            "DELETE FROM products WHERE id = %s",
            (product_id,)
        )
        flash('Product deleted successfully', 'success')
    
    return redirect(url_for('user.add_product'))

@user_bp.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Handle customer edit
    customer_id = request.args.get('edit', type=int)
    customer = None
    if customer_id:
        customer = db.execute_query(
            "SELECT * FROM customers WHERE id = %s AND user_id = %s",
            (customer_id, user_id),
            fetch_one=True
        )
        if not customer:
            flash('Customer not found or unauthorized', 'danger')
            return redirect(url_for('user.add_customer'))
    
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')
        
        if customer_id:  # Update existing customer
            db.execute_query(
                "UPDATE customers SET name = %s, phone = %s, email = %s WHERE id = %s",
                (name, phone, email, customer_id)
            )
            flash('Customer updated successfully', 'success')
        else:  # Add new customer
            db.execute_query(
                "INSERT INTO customers (name, phone, email, user_id) VALUES (%s, %s, %s, %s)",
                (name, phone, email, user_id)
            )
            flash('Customer added successfully', 'success')
        return redirect(url_for('user.add_customer'))
    
    customers = db.execute_query(
        "SELECT * FROM customers WHERE user_id = %s ORDER BY name",
        (user_id,)
    )
    
    return render_template('user/add_customer.html', 
                         customers=customers,
                         customer=customer)

@user_bp.route('/delete_customer/<int:customer_id>')
def delete_customer(customer_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Verify customer belongs to user
    customer = db.execute_query(
        "SELECT * FROM customers WHERE id = %s AND user_id = %s",
        (customer_id, user_id),
        fetch_one=True
    )
    
    if not customer:
        flash('Customer not found or unauthorized', 'danger')
    else:
        db.execute_query(
            "DELETE FROM customers WHERE id = %s",
            (customer_id,)
        )
        flash('Customer deleted successfully', 'success')
    
    return redirect(url_for('user.add_customer'))

@user_bp.route('/create_bill', methods=['GET', 'POST'])
def create_bill():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        customer_id = request.form.get('customer_id', None)
        if customer_id == 'new':
            name = request.form['new_customer_name']
            phone = request.form.get('new_customer_phone', '')
            email = request.form.get('new_customer_email', '')
            
            customer_id = db.execute_query(
                "INSERT INTO customers (name, phone, email, user_id) VALUES (%s, %s, %s, %s)",
                (name, phone, email, user_id)
            )
        
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        
        total_amount = 0
        sale_items = []
        
        for product_id, quantity in zip(product_ids, quantities):
            if not product_id or not quantity or int(quantity) <= 0:
                continue
                
            product = db.execute_query(
                "SELECT * FROM products WHERE id = %s AND user_id = %s",
                (product_id, user_id),
                fetch_one=True
            )
            
            if product:
                quantity = int(quantity)
                if quantity > product['stock']:
                    flash(f'Not enough stock for {product["name"]}', 'danger')
                    return redirect(url_for('user.create_bill'))
                
                item_total = product['price'] * quantity
                total_amount += item_total
                
                sale_items.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'price': product['price'],
                    'total': item_total,
                    'product_name': product['name']
                })
        
        if not sale_items:
            flash('No products selected', 'danger')
            return redirect(url_for('user.create_bill'))
        
        sale_id = db.execute_query(
            "INSERT INTO sales (customer_id, user_id, total_amount) VALUES (%s, %s, %s)",
            (customer_id if customer_id and customer_id != 'new' else None, user_id, total_amount)
        )
        
        for item in sale_items:
            db.execute_query(
                "INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (sale_id, item['product_id'], item['quantity'], item['price'])
            )
            
            db.execute_query(
                "UPDATE products SET stock = stock - %s WHERE id = %s",
                (item['quantity'], item['product_id'])
            )
        
        session['current_invoice'] = sale_id
        return redirect(url_for('user.view_invoice', invoice_id=sale_id))
    
    products = db.execute_query(
        "SELECT * FROM products WHERE user_id = %s AND stock > 0 ORDER BY name",
        (user_id,)
    )
    customers = db.execute_query(
        "SELECT * FROM customers WHERE user_id = %s ORDER BY name",
        (user_id,)
    )
    
    return render_template('user/create_bill.html', 
                         products=products, 
                         customers=customers)

@user_bp.route('/invoice/<int:invoice_id>')
def view_invoice(invoice_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    sale = db.execute_query("""
        SELECT s.*, u.full_name as seller_name, u.shop_number, 
               c.name as customer_name, c.phone as customer_phone, c.email as customer_email
        FROM sales s
        LEFT JOIN users u ON s.user_id = u.id
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE s.id = %s AND s.user_id = %s
    """, (invoice_id, user_id), fetch_one=True)
    
    if not sale:
        flash('Invoice not found', 'danger')
        return redirect(url_for('user.dashboard'))
    
    items = db.execute_query("""
        SELECT si.*, p.name as product_name
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = %s
    """, (invoice_id,))
    
    return render_template('bills/invoice.html', sale=sale, items=items)

@user_bp.route('/view_sales')
def view_sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    sales = db.execute_query("""
        SELECT s.*, c.name as customer_name
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE s.user_id = %s
        ORDER BY s.date DESC
    """, (user_id,))
    
    return render_template('user/view_sales.html', sales=sales)

@user_bp.route('/messages', methods=['GET', 'POST'])
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        message = request.form['message']
        db.execute_query(
            "INSERT INTO messages (sender_id, receiver_id, message, is_admin_message) VALUES (%s, (SELECT id FROM admins LIMIT 1), %s, FALSE)",
            (user_id, message)
        )
        flash('Message sent to admin', 'success')
        return redirect(url_for('user.messages'))
    
    # Mark messages as read
    db.execute_query(
        "UPDATE messages SET is_read = TRUE WHERE receiver_id = %s",
        (user_id,)
    )
    
    messages = db.execute_query("""
        SELECT m.*, a.username as sender_name, 
               CASE WHEN m.is_admin_message THEN 'Admin' ELSE 'You' END as sender_type
        FROM messages m
        LEFT JOIN admins a ON m.sender_id = a.id
        WHERE m.receiver_id = %s OR (m.sender_id = %s AND NOT m.is_admin_message)
        ORDER BY m.date DESC
    """, (user_id, user_id))
    
    return render_template('user/messages.html', messages=messages)

@user_bp.route('/view_balance')
def view_balance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.execute_query(
        "SELECT balance FROM users WHERE id = %s",
        (session['user_id'],),
        fetch_one=True
    )
    
    payments = db.execute_query(
        "SELECT * FROM payments WHERE user_id = %s ORDER BY date DESC",
        (session['user_id'],)
    )
    
    return render_template('user/view_balance.html', 
                         balance=user['balance'],
                         payments=payments)

@user_bp.route('/mark_payment_paid/<int:payment_id>')
def mark_payment_paid(payment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    payment = db.execute_query(
        "SELECT * FROM payments WHERE id = %s AND user_id = %s",
        (payment_id, user_id),
        fetch_one=True
    )
    
    if payment:
        db.execute_query(
            "UPDATE payments SET status = 'paid' WHERE id = %s",
            (payment_id,)
        )
        
        db.execute_query(
            "UPDATE warnings SET status = 'resolved' WHERE user_id = %s AND type = %s AND amount = %s",
            (user_id, payment['type'], payment['amount'])
        )
        
        flash('Payment marked as paid', 'success')
    
    return redirect(url_for('user.view_balance'))