from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os

app = Flask(__name__)

# RDS MySQL Configuration (Get from environment variables)
db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')

def get_db_connection():
    try:
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            db=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route('/')
def index():
    products = [
        {"name": "Life Insurance", "description": "Protects your family's future.", "banner": "banner1.jpg"},
        {"name": "Health Insurance", "description": "Covers medical expenses.", "banner": "banner2.jpg"},
        # Add more products...
    ]
    return render_template('index.html', products=products)

@app.route('/claim', methods=['GET', 'POST'])
def claim():
    if request.method == 'POST':
        policy_id = request.form['policy_id']
        name = request.form['name']
        dob = request.form['dob']
        mobile = request.form['mobile']

        connection = get_db_connection()
        if connection:
            try:
                with connection.cursor() as cursor:
                    sql = "INSERT INTO claims (policy_id, name, dob, mobile) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (policy_id, name, dob, mobile))
                connection.commit()
                return "Claim submitted successfully. Our executives will call you shortly! "
            except pymysql.MySQLError as e:
                return f"Error submitting claim: {e}"
            finally:
                connection.close()
        else:
            return "Database connection failed."

    return render_template('claim.html')

if __name__ == '__main__':
    app.run(debug=True)