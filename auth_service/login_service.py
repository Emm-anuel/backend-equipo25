import os
import hashlib
from datetime import datetime, timedelta

import pymssql
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt

"""
Microservice responsible only for authenticating users.
Run with: python login_service.py
"""

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.environ.get('AUTH_SECRET_KEY', 'replace-me')

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


def verify_password(stored_hash, provided_password):
    hashed_provided = hashlib.sha1(provided_password.encode()).hexdigest()
    return stored_hash == hashed_provided


def generate_token(user_row):
    expiration = datetime.utcnow() + timedelta(hours=24)
    payload = {
        'sub': user_row['id'],
        'username': user_row['username'],
        'name': user_row.get('nombre_completo'),
        'exp': expiration
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token, int(expiration.timestamp())


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identity = data.get('username') or data.get('email')
    password = data.get('password')

    if not identity or not password:
        return jsonify({'error': 'username/email y password son requeridos'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            "SELECT id, username, email, nombre_completo, contrasena FROM usuarios WHERE username = %s OR email = %s",
            (identity, identity)
        )
        user = cursor.fetchone()

        if not user or not verify_password(user['contrasena'], password):
            return jsonify({'error': 'Credenciales inválidas'}), 401

        token, exp_ts = generate_token(user)
        response = {
            'accessToken': token,
            'tokenType': 'Bearer',
            'expiresIn': 24 * 60 * 60,
            'expiresAt': exp_ts,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'name': user.get('nombre_completo')
            }
        }
        return jsonify(response), 200
    except Exception as exc:
        app.logger.exception("Login error: %s", exc)
        return jsonify({'error': 'Error procesando la solicitud'}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
