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

pi_address = "192.168.137.198"

def get_laptop_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Laptop IP Address: {ip_address}")  # Debug print
    return ip_address

def check_pi_server():
    try:
        ip_address = get_laptop_ip()
        print(f"Sending IP to server: {ip_address}")  # Debug print
        url = "http://" + pi_address + ":5001/set_ip"
        response = requests.post(url, json={'ip': ip_address})
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
        cursor.execute("SELECT name, designation FROM user WHERE card_id = %s", (card_id,))
        user = cursor.fetchone()

        if user:
            name = user['name']
            designation = user['designation']
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

            # Fetch the updated attendance list
            cursor.execute("""
            SELECT 
                attendance.id,
                attendance.card_id,
                attendance.name,
                attendance.EntryTime,
                attendance.ExitTime,
                user.designation
            FROM attendance
            LEFT JOIN user ON attendance.card_id = user.card_id
            """)
            attendance_records = cursor.fetchall()
            
            # Format EntryTime and ExitTime
            for record in attendance_records:
                record['Date'] = record['EntryTime'].strftime('%Y-%m-%d')  # Extract the Date part
                record['EntryTime'] = record['EntryTime'].strftime('%H:%M:%S')  # Format EntryTime
                record['ExitTime'] = record['ExitTime'].strftime('%H:%M:%S') if record['ExitTime'] else '--'  # Format ExitTime

            response_data = {
                "user": {
                    "name": name,
                    "designation": designation,
                    "card_id": card_id
                },
                "attendance_records": attendance_records
            }
            cursor.close()
            conn.close()
            return jsonify(response_data), 200

        else:
            print(f"Card ID: {card_id} not found in user table")
            response_message = {"error": "Card ID not found in user table"}

        cursor.close()
        conn.close()
        return jsonify(response_message), 404
    
    except mysql.connector.Error as err:
        print(f"Error inserting RFID data: {err}")
        return jsonify({"error": str(err)}), 500


@app.route('/test', methods=['POST'])
def test():
    data = request.get_json()
    return jsonify({"message": "Data received", "data": data}), 200

# WEB interface methods
@app.route('/')
def home():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Query to fetch attendance details and join with user details
        query = """
        SELECT 
            attendance.id,
            attendance.card_id,
            attendance.name,
            attendance.EntryTime,
            attendance.ExitTime,
            user.designation
        FROM attendance
        LEFT JOIN user ON attendance.card_id = user.card_id
        """
        cursor.execute(query)
        attendance_records = cursor.fetchall()
        
        # Format EntryTime and ExitTime
        for record in attendance_records:
            record['Date'] = record['EntryTime'].strftime('%Y-%m-%d')  # Extract the Date part
            record['EntryTime'] = record['EntryTime'].strftime('%H:%M:%S')  # Format EntryTime
            record['ExitTime'] = record['ExitTime'].strftime('%H:%M:%S') if record['ExitTime'] else '--'  # Format ExitTime

        cursor.close()
        conn.close()

        return render_template('Dashboard.html', attendance_records=attendance_records, pi_ip=pi_address)

    except mysql.connector.Error as err:
        print(f"Error fetching attendance data: {err}")
        return jsonify({"error": str(err)}), 500


@app.route('/login')
def login():
    return render_template('login.html', pi_ip=pi_address)

@app.route('/survilence')
def survilence():
    return render_template('survilence.html')

if __name__ == '__main__':
    create_tables()  # Ensure tables are created before checking PI server
    print("Checking PI server...")  # Debug print
    # if check_pi_server():
    if True :
        print("Server response OK, starting Flask app.")
        app.run(host='0.0.0.0', port=5001)
    else:
        print("Server not responding, Flask app will not start.", file=sys.stderr)
