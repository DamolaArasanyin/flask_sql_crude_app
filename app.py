from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
from config import db_config
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Context manager for database connections
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        yield conn
    except Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()

# Input validation helper
def validate_customer_data(data):
    """Validate customer form data"""
    errors = []
    
    if not data.get('First_name') or len(data['First_name'].strip()) < 2:
        errors.append("First name must be at least 2 characters")
    
    if not data.get('Last_name') or len(data['Last_name'].strip()) < 2:
        errors.append("Last name must be at least 2 characters")
    
    if not data.get('email') or '@' not in data['email']:
        errors.append("Valid email is required")
    
    if not data.get('Location'):
        errors.append("Location is required")
    
    if not data.get('Gender') or data['Gender'] not in ['Male', 'Female', 'Other']:
        errors.append("Valid gender selection is required")
    
    return errors

# Home page (list records)
@app.route("/")
def index():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Customer ORDER BY Customer_id DESC")
            customers = cursor.fetchall()
            cursor.close()
        return render_template("index.html", customers=customers)
    except Error as e:
        flash(f"Error loading customers: {str(e)}", "error")
        return render_template("index.html", customers=[])

# Add a new customer
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == "POST":
        # Validate input
        errors = validate_customer_data(request.form)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template('add.html')
        
        try:
            fname = request.form["First_name"].strip()
            lname = request.form["Last_name"].strip()
            email = request.form["email"].strip()
            location = request.form["Location"].strip()
            gender = request.form["Gender"]

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Customer (First_name, Last_name, email, Location, Gender) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (fname, lname, email, location, gender))
                conn.commit()
                cursor.close()
            
            flash("Customer added successfully!", "success")
            return redirect(url_for('index'))
        
        except Error as e:
            flash(f"Error adding customer: {str(e)}", "error")
            return render_template('add.html')
    
    return render_template('add.html')

# Update customer
@app.route('/update/<int:id>', methods=['GET', 'POST']) 
def update(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Customer WHERE Customer_id=%s", (id,))
            customer = cursor.fetchone()
            
            if not customer:
                flash("Customer not found", "error")
                return redirect(url_for('index'))

            if request.method == 'POST':
                # Validate input
                errors = validate_customer_data(request.form)
                if errors:
                    for error in errors:
                        flash(error, "error")
                    return render_template('update.html', customer=customer)
                
                fname = request.form["First_name"].strip()
                lname = request.form["Last_name"].strip()
                email = request.form["email"].strip()
                location = request.form["Location"].strip()
                gender = request.form["Gender"]

                cursor.execute("""
                    UPDATE Customer 
                    SET First_name=%s, Last_name=%s, email=%s, Location=%s, Gender=%s
                    WHERE Customer_id=%s
                """, (fname, lname, email, location, gender, id))
                conn.commit()
                cursor.close()
                
                flash("Customer updated successfully!", "success")
                return redirect(url_for('index'))
            
            cursor.close()
        
        return render_template('update.html', customer=customer)
    
    except Error as e:
        flash(f"Error updating customer: {str(e)}", "error")
        return redirect(url_for('index'))

# Delete customer
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Customer WHERE Customer_id=%s", (id,))
            
            if cursor.rowcount == 0:
                flash("Customer not found", "error")
            else:
                conn.commit()
                flash("Customer deleted successfully!", "success")
            
            cursor.close()
    
    except Error as e:
        flash(f"Error deleting customer: {str(e)}", "error")
    
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    # Only use debug mode in development
    app.run(debug=app.config.get('DEBUG', False))


