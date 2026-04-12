# src/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from diagnostic_engine import analyze_company
import traceback

app = Flask(__name__)
CORS(app)

@app.route('/api/analyze', methods=['POST'])
def analyze_company_endpoint():
    try:
        data = request.json
        company_name = data.get('company_name')

        if not company_name:
            return jsonify({'error': 'company_name required'}), 400

        result = analyze_company(company_name)
        return jsonify(result), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'version': '1.0'}), 200

@app.route('/api/status', methods=['GET'])
def status_check():
    return jsonify({'status': 'ok', 'version': '1.0'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)