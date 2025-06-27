import os
from flask import Flask, render_template, request, jsonify, send_file, session
# ... your existing imports

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Health check endpoint for Google Cloud
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': str(datetime.now())}), 200

# ... your existing routes

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)