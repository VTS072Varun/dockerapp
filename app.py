from flask import Flask, request, jsonify

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

if __name__ == '__main__':
    app.run(port=3000)