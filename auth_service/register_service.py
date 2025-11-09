import os
import hashlib
from datetime import datetime

import pymssql
from flask import Flask, request, jsonify
from flask_cors import CORS

"""
Microservice focused on registering users into SQL Server.
Run with: python register_service.py
"""

app = Flask(__name__)
CORS(app)

SERVER = os.environ.get('DB_SERVER', 'localhost')
DATABASE = os.environ.get('DB_NAME', 'master')
USERNAME = os.environ.get('DB_USER', 'sa')
PASSWORD = os.environ.get('DB_PASSWORD', 'YourPassword123!')


def get_db_connection():
    try:
        return pymssql.connect(
            server=SERVER,
            port=1433,
            database=DATABASE,
            user=USERNAME,
            password=PASSWORD
        )
    except Exception as exc:
        app.logger.error("Error connecting to DB: %s", exc)
        return None


def hash_password(password):
    return hashlib.sha1(password.encode()).hexdigest()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username') or data.get('email')
    email = data.get('email')
    full_name = data.get('name') or data.get('fullName')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'username, email y password son requeridos'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            "SELECT id FROM usuarios WHERE username = %s OR email = %s",
            (username, email)
        )
        existing = cursor.fetchone()
        if existing:
            return jsonify({'error': 'Usuario o correo ya registrados'}), 409

        hashed_password = hash_password(password)
        created_at = datetime.utcnow()
        cursor.execute(
            """
            INSERT INTO usuarios (username, email, nombre_completo, contrasena, created_at)
            OUTPUT INSERTED.id
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, email, full_name, hashed_password, created_at)
        )
        new_user_id = cursor.fetchone()['id']
        conn.commit()

        return jsonify({
            'id': new_user_id,
            'username': username,
            'email': email,
            'name': full_name
        }), 201
    except Exception as exc:
        conn.rollback()
        app.logger.exception("Register error: %s", exc)
        return jsonify({'error': 'Error registrando usuario'}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
