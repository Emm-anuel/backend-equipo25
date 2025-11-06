# pip install pymssql flask flask-cors requests pyjwt
import pymssql
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import hashlib
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

app.secret_key = 'your_secret_key'  # Replace with a strong, random secret key

SERVER = 'localhost'
DATABASE = 'master'
USERNAME = 'sa'
PASSWORD = 'YourPassword123!'

def get_db_connection():
    try:
        conn = pymssql.connect(
            server=SERVER, port=1433, database=DATABASE, user=USERNAME, password=PASSWORD)
        return conn
    except Exception as e:
        print(f"Error conectando a BD: {e}")
        return None

def verify_password(stored_password_hash, provided_password):
    hashed_provided_password = hashlib.sha1(
        provided_password.encode()).hexdigest()
    return stored_password_hash == hashed_provided_password

def generate_token(user_data):
    expiration = datetime.utcnow() + timedelta(hours=24)
    token = jwt.encode({
        'user_id': user_data['id'],
        'username': user_data['username'],
        'exp': expiration
    }, app.secret_key, algorithm='HS256')
    return token

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('email')  # Frontend sends email as username
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Se requiere usuario y contraseña'}), 400

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(
                "SELECT id, username, contrasena FROM usuarios WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and verify_password(user['contrasena'], password):
                token = generate_token(user)
                return jsonify({
                    'mensaje': 'Autenticacion exitosa',
                    'token': token
                }), 200
            else:
                return jsonify({'error': 'Usuario o password incorrectas'}), 401
        except Exception as e:
            return jsonify({'error': f'Error en BD {e}'}), 500
        finally:
            conn.close()
    else:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)