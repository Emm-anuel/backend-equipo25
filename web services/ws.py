# pip install pymssql flask flask-cors requests
import pymssql
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import hashlib

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


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Se requiere usuario y contraseña'}), 400

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(
                "SELECT username, contrasena FROM usuarios WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and verify_password(user['contrasena'], password):
                session['username'] = username
                return jsonify({'mensaje': 'Autenticacion exitosa'}), 200
            else:
                return jsonify({'error': 'Usuario o password incorrectas'}), 401
        except Exception as e:
            return jsonify({'error': f'Error en BD {e}'}), 500
        finally:
            conn.close()
    else:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

# --- Servicios CRUD para la tabla 'personajes' ---

# Obtener todos los personajes


@app.route('/personajes', methods=['GET'])
def get_personajes():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute("SELECT id, name, email FROM personajes")
            personajes = cursor.fetchall()
            return jsonify(personajes), 200
        except Exception as e:
            return jsonify({'error': f'Error al obtener personajes: {e}'}), 500
        finally:
            conn.close()
    else:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

# Obtener un personaje por ID


@app.route('/personajes/<int:id>', methods=['GET'])
def get_personaje(id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(
                "SELECT id, name, email FROM personajes WHERE id = %d", (id,))
            personaje = cursor.fetchone()
            if personaje:
                return jsonify(personaje), 200
            else:
                return jsonify({'mensaje': 'Personaje no encontrado'}), 404
        except Exception as e:
            return jsonify({'error': f'Error al obtener personaje: {e}'}), 500
        finally:
            conn.close()
    else:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

# Crear un nuevo personaje


@app.route('/personajes', methods=['POST'])
def create_personaje():
    data = request.get_json()
    id = data.get('id')
    name = data.get('name')
    email = data.get('email')

    if not id or not name or not email:
        return jsonify({'error': 'Se requiere id, nombre y correo electrónico'}), 400

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO personajes (id, name, email) VALUES (%d, %s, %s)", (id, name, email))
            conn.commit()
            return jsonify({'mensaje': 'Personaje creado exitosamente'}), 201
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Error al crear personaje: {e}'}), 500
        finally:
            conn.close()
    else:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

# Actualizar un personaje existente


@app.route('/personajes/<int:id>', methods=['PUT'])
def update_personaje(id):
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({'error': 'Se requiere nombre y correo electrónico'}), 400

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE personajes SET name = %s, email = %s WHERE id = %d", (name, email, id))
            conn.commit()
            if cursor.rowcount > 0:
                return jsonify({'mensaje': 'Personaje actualizado exitosamente'}), 200
            else:
                return jsonify({'mensaje': 'Personaje no encontrado'}), 404
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Error al actualizar personaje: {e}'}), 500
        finally:
            conn.close()
    else:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

# Eliminar un personaje por ID


@app.route('/personajes/<int:id>', methods=['DELETE'])
def delete_personaje(id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM personajes WHERE id = %d", (id,))
            conn.commit()
            if cursor.rowcount > 0:
                return jsonify({'mensaje': 'Personaje eliminado exitosamente'}), 200
            else:
                return jsonify({'mensaje': 'Personaje no encontrado'}), 404
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Error al eliminar personaje: {e}'}), 500
        finally:
            conn.close()
    else:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500


@app.route('/rag/query', methods=['POST'])
def rag_query():
    data = request.get_json()
    question = data.get('question', '')
    
    # Obtener documentos reales de la base de datos
    conn = get_db_connection()
    available_docs = []
    if conn:
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute("SELECT nombre_archivo FROM documentos WHERE estatus IN ('Activo', 'Archivado')")
            docs = cursor.fetchall()
            available_docs = [doc['nombre_archivo'] for doc in docs]
        except:
            available_docs = ['Contrato-Proveedor.pdf', 'Estado-Financiero.xlsx', 'Manual-Empleado.docx']
        finally:
            conn.close()
    else:
        available_docs = ['Contrato-Proveedor.pdf', 'Estado-Financiero.xlsx', 'Manual-Empleado.docx']
    
    # Mock responses basadas en palabras clave de documentos internos
    mock_responses = {
        'contrato': 'Según el análisis de Contrato-Proveedor.pdf, se identificó una cláusula de incumplimiento en la sección 4.2 que establece penalizaciones del 5% por retrasos superiores a 15 días hábiles. El contrato tiene vigencia hasta diciembre de 2025.',
        'proveedor': 'De acuerdo con Contrato-Proveedor.pdf, el proveedor actual es TechSupply Inc. con NIF B-12345678. Las condiciones de pago son NET 30 y el contacto principal es el Ing. Roberto Sánchez.',
        'financiero': 'Basado en Estado-Financiero.xlsx, los resultados del Q3 2025 muestran un incremento del 12% en ingresos respecto al trimestre anterior. El EBITDA se situó en $2.4M con un margen operativo del 18%.',
        'presupuesto': 'Según Estado-Financiero.xlsx, el presupuesto anual aprobado es de $8.5M distribuido en: 45% operaciones, 30% recursos humanos, 15% tecnología y 10% marketing.',
        'empleado': 'De acuerdo con Manual-Empleado.docx, el programa de capacitación incluye 40 horas anuales obligatorias. Los nuevos empleados tienen un periodo de prueba de 90 días y acceso a beneficios después de 6 meses.',
        'vacaciones': 'Según Manual-Empleado.docx, los empleados tienen derecho a 15 días hábiles de vacaciones anuales después del primer año. Se pueden acumular hasta 30 días máximo.',
        'capacitación': 'El Manual-Empleado.docx especifica que el programa de capacitación cubre: onboarding (primera semana), seguridad y compliance (mensual), y desarrollo profesional (trimestral).',
        'cumplimiento': 'Basado en los documentos de compliance, la empresa sigue los estándares ISO 27001 para seguridad de información y realiza auditorías trimestrales de cumplimiento normativo.',
    }
    
    # Buscar respuesta basada en palabras clave
    response_text = None
    question_lower = question.lower()
    selected_sources = []
    
    for keyword, response in mock_responses.items():
        if keyword in question_lower:
            response_text = response
            # Extraer documentos mencionados en la respuesta
            for doc in available_docs:
                if doc in response:
                    selected_sources.append(doc)
            break
    
    # Respuesta genérica si no se encuentra palabra clave
    if not response_text:
        response_text = f'Según los documentos corporativos disponibles, he encontrado información relacionada con su consulta: "{question}". Los archivos indican que este tema requiere análisis de la documentación interna. Se recomienda revisar los archivos de políticas y procedimientos para información detallada.'
        selected_sources = available_docs[:2] if len(available_docs) >= 2 else available_docs
    
    # Si no se seleccionaron fuentes, usar algunas aleatorias
    if not selected_sources and available_docs:
        selected_sources = available_docs[:3] if len(available_docs) >= 3 else available_docs
    
    return jsonify({
        'answer': response_text,
        'sources': selected_sources,
        'confidence': 0.87
    }), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
