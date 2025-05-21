import mysql.connector
from mysql.connector import Error
from datetime import datetime

class Database:
    def __init__(self):
        self.connection = self.create_connection()
        if self.connection:
            self.create_tables()
            self.create_admin_user()

    def create_connection(self):
        try:
            # First try to connect without specifying database
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password=''
            )
            
            # Create database if it doesn't exist
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS market_management")
            cursor.close()
            connection.close()
            
            # Now connect with database specified
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='market_management'
            )
            print("Connection to MySQL DB successful")
            return connection
            
        except Error as e:
            print(f"The error '{e}' occurred")
            return None

    def create_tables(self):
        cursor = self.connection.cursor()
        
        try:
            # Admins table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                shop_number VARCHAR(20) NOT NULL UNIQUE,
                phone VARCHAR(20),
                email VARCHAR(100),
                balance DECIMAL(10, 2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Categories table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """)
            
            # Products table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                category_id INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                stock INT DEFAULT 0,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """)
            
            # Customers table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                email VARCHAR(100),
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """)
            
            # Sales table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT,
                user_id INT NOT NULL,
                total_amount DECIMAL(10, 2) NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """)
            
            # Sale items table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sale_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
            """)
            
            # Payments table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                type ENUM('rent', 'electricity') NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('pending', 'paid') DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """)
            
            # Warnings table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                type ENUM('rent', 'electricity') NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                message TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('active', 'resolved') DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """)
            
            # Messages table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                message TEXT NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                is_admin_message BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (sender_id) REFERENCES admins(id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """)
            
            self.connection.commit()
            print("Tables created successfully")
            
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            cursor.close()

    def create_admin_user(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM admins WHERE username = 'admin'")
            admin = cursor.fetchone()
            
            if not admin:
                cursor.execute("""
                INSERT INTO admins (username, password, full_name)
                VALUES (%s, %s, %s)
                """, ('admin', 'admin123', 'Abbas Hilal'))
                self.connection.commit()
                print("Default admin user created")
                
        except Error as e:
            print(f"Error creating admin user: {e}")
        finally:
            cursor.close()

    # Message-related methods
    def send_message_to_admin(self, user_id, message):
        query = """
        INSERT INTO messages (sender_id, receiver_id, message, is_admin_message)
        VALUES (%s, (SELECT id FROM admins LIMIT 1), %s, FALSE)
        """
        return self.execute_query(query, (user_id, message))

    def send_message_to_user(self, admin_id, user_id, message):
        query = """
        INSERT INTO messages (sender_id, receiver_id, message, is_admin_message)
        VALUES (%s, %s, %s, TRUE)
        """
        return self.execute_query(query, (admin_id, user_id, message))

    def get_user_messages(self, user_id):
        query = """
        SELECT m.*, a.username as sender_name, 
               CASE WHEN m.is_admin_message THEN 'Admin' ELSE 'You' END as sender_type
        FROM messages m
        LEFT JOIN admins a ON m.sender_id = a.id
        WHERE m.receiver_id = %s OR (m.sender_id = %s AND NOT m.is_admin_message)
        ORDER BY m.date DESC
        """
        return self.execute_query(query, (user_id, user_id))

    def get_admin_messages(self):
        query = """
        SELECT m.*, u.full_name as user_name, u.shop_number 
        FROM messages m
        JOIN users u ON m.receiver_id = u.id
        WHERE m.is_admin_message = FALSE
        ORDER BY m.date DESC
        """
        return self.execute_query(query)

    # General query execution method
    def execute_query(self, query, params=None, fetch_one=False):
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            if query.strip().lower().startswith(('insert', 'update', 'delete')):
                self.connection.commit()
                return cursor.lastrowid
            else:
                return cursor.fetchone() if fetch_one else cursor.fetchall()
        except Error as e:
            print(f"The error '{e}' occurred")
            return None
        finally:
            cursor.close()

db = Database()