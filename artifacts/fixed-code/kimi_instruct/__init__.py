from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

# Dummy user data
users = {
    'admin': {'password': 'secretpassword'},
    'user1': {'password': 'user1password'}
}

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if username in users and users[username]['password'] == password:
        # Create a token
        token = generate_token(username)
        return jsonify({'token': token}), 200
    else:
        return make_response('Invalid credentials', 401)

def generate_token(username):
    # Implement token generation logic (e.g., using JWT)
    pass

if __name__ == '__main__':
    app.run(debug=True)