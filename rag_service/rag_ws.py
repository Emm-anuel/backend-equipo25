# pip install pymssql flask flask-cors requests langchain chromadb
import pymssql
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import jwt
from functools import wraps

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}
SECRET_KEY = 'your_secret_key'  # Same as auth service

# Database configuration
SERVER = 'localhost'
DATABASE = 'master'
USERNAME = 'sa'
PASSWORD = 'YourPassword123!'

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    try:
        conn = pymssql.connect(
            server=SERVER, port=1433, database=DATABASE, user=USERNAME, password=PASSWORD)
        return conn
    except Exception as e:
        print(f"Error conectando a BD: {e}")
        return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'message': 'Token is missing'}), 401

        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        return f(*args, **kwargs)
    return decorated

@app.route('/upload-document', methods=['POST'])
@token_required
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Here you would typically process the document and store it in your vector DB
        # For now, we'll just store the file info in SQL
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO documents (filename, filepath, status) VALUES (%s, %s, %s)",
                    (filename, file_path, 'PENDING')
                )
                conn.commit()
                return jsonify({'message': 'File uploaded successfully'}), 200
            except Exception as e:
                return jsonify({'error': f'Database error: {e}'}), 500
            finally:
                conn.close()
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/rag-query', methods=['POST'])
@token_required
def rag_query():
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
        
    # Here you would:
    # 1. Use the query to search your vector DB
    # 2. Get relevant document chunks
    # 3. Use an LLM to generate a response
    # For now, we'll return a mock response
    
    mock_response = {
        'answer': f'This is a mock response to your query: {query}',
        'sources': [
            {
                'document': 'example.pdf',
                'relevance': 0.95
            }
        ]
    }
    
    return jsonify(mock_response), 200

@app.route('/documents', methods=['GET'])
@token_required
def list_documents():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute("SELECT id, filename, status FROM documents")
            documents = cursor.fetchall()
            return jsonify(documents), 200
        except Exception as e:
            return jsonify({'error': f'Database error: {e}'}), 500
        finally:
            conn.close()
    
    return jsonify({'error': 'Database connection failed'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)