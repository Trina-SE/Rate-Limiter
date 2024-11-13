from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify({"data": "This is some data from the backend"}), 200

if __name__ == "__main__":
    app.run(port=5002)
