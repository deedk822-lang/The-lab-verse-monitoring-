from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/research', methods=['POST'])
def research():
    data = request.get_json()
    query = data.get('q')
    return jsonify({
        'provider': 'test-provider',
        'text': f'Response to "{query}"',
        'model': 'test-model'
    })

if __name__ == '__main__':
    app.run(port=8000)
