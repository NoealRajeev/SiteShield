import sys
import socket
import requests
from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import errorcode

app = Flask(__name__)

# MySQL configuration
db_config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'projects'
}

def get_laptop_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Laptop IP Address: {ip_address}")  # Debug print
    return ip_address

def check_pi_server():
    try:
        ip_address = get_laptop_ip()
        print(f"Sending IP to server: {ip_address}")  # Debug print
        response = requests.post('http://192.168.137.198:5001/set_ip', json={'ip': ip_address})
        print(f"Server response status code: {response.status_code}")  # Debug print
        if response.status_code == 200:
            response_data = response.json()
            print(f"Server response data: {response_data}")  # Debug print
            if (response_data.get("ip_address") == ip_address and
                    response_data.get("message") == "IP address received"):
                return True
            else:
                print("Response data does not match expected values.")  # Debug print
        else:
            print("Response status code is not 200.")  # Debug print
        return False
    except requests.RequestException as e:
        print(f"Error checking server: {e}", file=sys.stderr)
        return False
    
def create_tables():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        create_user_table_query = """
        CREATE TABLE IF NOT EXISTS user (
            id INT NOT NULL AUTO_INCREMENT,
            card_id VARCHAR(255) DEFAULT NULL,
            name VARCHAR(255) DEFAULT NULL,
            designation VARCHAR(255) DEFAULT NULL,
            PRIMARY KEY (id)
        )
        """
        cursor.execute(create_user_table_query)
        
        create_attendance_table_query = """
        CREATE TABLE IF NOT EXISTS attendance (
            id INT NOT NULL AUTO_INCREMENT,
            card_id VARCHAR(255) DEFAULT NULL,
            name VARCHAR(255) DEFAULT NULL,
            EntryTime DATETIME DEFAULT NULL,
            ExitTime DATETIME DEFAULT NULL,
            ErrorReport VARCHAR(60) DEFAULT NULL,
            PRIMARY KEY (id)
        )
        """
        cursor.execute(create_attendance_table_query)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Tables checked/created successfully.")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

@app.route('/rfid', methods=['POST'])
def receive_rfid():
    data = request.get_json()
    if not data or 'id' not in data or 'timestamp' not in data:
        return jsonify({"error": "Invalid payload"}), 400

    card_id = data['id']
    timestamp = data['timestamp']

    print(f"Received RFID data - ID: {card_id}, Timestamp: {timestamp}")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Check user table for card owner details
        cursor.execute("SELECT name FROM user WHERE card_id = %s", (card_id,))
        user = cursor.fetchone()

        if user:
            name = user['name']
            # Check if there's an existing record in attendance table with EntryTime present and ExitTime is NULL
            cursor.execute("""
                SELECT id FROM attendance
                WHERE card_id = %s AND EntryTime IS NOT NULL AND ExitTime IS NULL
                ORDER BY EntryTime DESC LIMIT 1
            """, (card_id,))
            attendance_record = cursor.fetchone()

            if attendance_record:
                # Update the existing record with the new ExitTime
                update_query = """
                UPDATE attendance SET ExitTime = %s WHERE id = %s
                """
                cursor.execute(update_query, (timestamp, attendance_record['id']))
                response_message = {"message": "Exit time updated successfully"}
            else:
                # Insert a new record with EntryTime
                insert_query = """
                INSERT INTO attendance (card_id, name, EntryTime)
                VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (card_id, name, timestamp))
                response_message = {"message": "Data received successfully"}

            conn.commit()
        else:
            print(f"Card ID: {card_id} not found in user table")
            response_message = {"error": "Card ID not found in user table"}

        cursor.close()
        conn.close()
        return jsonify(response_message), 200 if user else 404
    
    except mysql.connector.Error as err:
        print(f"Error inserting RFID data: {err}")
        return jsonify({"error": str(err)}), 500

@app.route('/test', methods=['POST'])
def test():
    data = request.get_json()
    return jsonify({"message": "Data received", "data": data}), 200

# WEB interface methods
@app.route('/')
def index():
    return render_template('index.html', rfid_data=123)

if __name__ == '__main__':
    create_tables()  # Ensure tables are created before checking PI server
    print("Checking PI server...")  # Debug print
    if check_pi_server():
        print("Server response OK, starting Flask app.")
        app.run(host='0.0.0.0', port=5001)
    else:
        print("Server not responding, Flask app will not start.", file=sys.stderr)
