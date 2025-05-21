from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db
from admin import admin_bp
from user import user_bp
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Register blueprints
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/user')

# Common routes
@app.route('/')
def home():
    if 'admin_id' in session:
        return redirect(url_for('admin.dashboard'))
    elif 'user_id' in session:
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        
        if user_type == 'admin':
            admin = db.execute_query(
                "SELECT * FROM admins WHERE username = %s AND password = %s",
                (username, password),
                fetch_one=True
            )
            if admin:
                session['admin_id'] = admin['id']
                session['username'] = admin['username']
                session['user_type'] = 'admin'
                return redirect(url_for('admin.dashboard'))
        else:
            user = db.execute_query(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                (username, password),
                fetch_one=True
            )
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_type'] = 'user'
                session['shop_number'] = user['shop_number']
                return redirect(url_for('user.dashboard'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)