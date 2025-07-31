from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/test_post', methods=['POST'])
def test_post():
    return jsonify({"message": "POST request successful!"})

if __name__ == '__main__':
    app.run(debug=True)
