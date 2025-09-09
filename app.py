from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from datetime import datetime
from main import process_pbit  # Import your existing processing function

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'pbit'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    """
    Process uploaded .pbit file using your existing main.py logic
    Returns: PDF file for download
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only .pbit files are allowed'}), 400
        
        # Read file bytes
        file_bytes = file.read()
        
        try:
            # Use your existing process_pbit function from main.py
            pdf_buffer = process_pbit(file_bytes, file.filename)
            
            if pdf_buffer is None:
                return jsonify({'error': 'Failed to process .pbit file'}), 500
            
            # Generate filename for download
            download_filename = file.filename.replace('.pbit', '_erd_final.pdf')
            
            # Return the PDF file
            pdf_buffer.seek(0)
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=download_filename
            )
                
        except Exception as e:
            print(f"Error processing .pbit file: {e}")
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Error in API endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify API is working"""
    return jsonify({
        'message': 'API is working!',
        'service': 'Power BI Documentador API',
        'endpoints': {
            'health': '/api/health',
            'process_file': '/api/process-file (POST)',
            'test': '/api/test'
        },
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
