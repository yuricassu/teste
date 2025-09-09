from flask import Flask, request, jsonify, send_file, send_from_directory, redirect
from flask_cors import CORS
from pathlib import Path
from datetime import datetime
import os
from main import process_pbit  # Your existing function

# -----------------------------
# Flask app
# -----------------------------
app = Flask(__name__, static_folder=None)
CORS(app)  # Enable CORS for frontend integration

# -----------------------------
# Config
# -----------------------------
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'pbit'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

HTML_PATH = Path(__file__).parent / "power-bi-documentador/index.html"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------------
# Frontend routes
# -----------------------------
@app.get("/")
def root():
    return redirect("/home", code=302)

@app.get("/home")
def home():
    return app.response_class(HTML_PATH.read_text(encoding="utf-8"), mimetype="text/html")

@app.get("/assets/<path:filename>")
def assets(filename):
    assets_dir = HTML_PATH.parent
    return send_from_directory(assets_dir, filename)

# -----------------------------
# API routes
# -----------------------------
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Power BI Documentador API',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/process-file', methods=['POST'])
def process_file():
    """Process uploaded .pbit file and return PDF"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only .pbit files are allowed'}), 400

        file_bytes = file.read()
        pdf_buffer = process_pbit(file_bytes, file.filename)
        if pdf_buffer is None:
            return jsonify({'error': 'Failed to process .pbit file'}), 500

        download_filename = file.filename.replace('.pbit', '_erd_final.pdf')
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=download_filename
        )

    except Exception as e:
        print(f"Error processing .pbit file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({
        'message': 'API is working!',
        'service': 'Power BI Documentador API',
        'endpoints': {
            'health': '/api/health',
            'process_file': '/api/process-file (POST)',
            'test': '/api/test',
            'frontend': '/home'
        },
        'timestamp': datetime.now().isoformat()
    })

# -----------------------------
# Run
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
