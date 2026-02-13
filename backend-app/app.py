from flask import Flask, jsonify
import mysql.connector
import os
import time

app = Flask(__name__)

def get_db_connection():
    # Tentative de connexion (retry simple)
    retries = 5
    while retries > 0:
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('MYSQL_HOST'),
                user=os.environ.get('MYSQL_USER'),
                password=os.environ.get('MYSQL_PASSWORD'),
                database=os.environ.get('MYSQL_DATABASE')
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Erreur connexion DB: {err}")
            retries -= 1
            time.sleep(2)
    return None

@app.route('/')
def health():
    return "Backend is running!"

@app.route('/api')
def api():
    conn = get_db_connection()
    if conn:
        status = "Succès : Connecté à MySQL !"
        conn.close()
    else:
        status = "Erreur : Impossible de joindre MySQL."

    return jsonify({
        "message": "CloudShop API v1",
        "db_status": status,
        "node": os.environ.get('MY_NODE_NAME')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)