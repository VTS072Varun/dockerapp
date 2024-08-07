from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/post', methods=['POST'])
def handle_post():
    # Get data from the POST request
    data = request.get_json()  # Assumes JSON payload
    
    # Process the data (for demonstration, we'll just echo it back)
    response = {
        'message': 'Data received successfully!',
        'received_data': data
    }
    
    # Return a JSON response
    return jsonify(response)

# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    version = "1.0"  # Replace with your actual version
    hostname = os.getenv('HOSTNAME', 'localhost')
    port = os.getenv('PORT', '3000')
    print(f'[Version {version}]: New request => http://{hostname}:{port}/health')
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(port=3000)


    