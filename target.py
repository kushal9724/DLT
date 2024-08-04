# target_server.py

from flask import Flask, jsonify, request
import random
import time

app = Flask(__name__)

class TargetServer:
    def __init__(self):
        self.requests_sent = 0
        self.responses_sent = 0

    def test_endpoint(self):
        self.requests_sent += 1
        response_delay = random.uniform(1, 5)  # Simulating response delay
        time.sleep(2)
        self.responses_sent += 1
        return jsonify({"message": "Test endpoint response"})

    def metrics_endpoint(self):
        return jsonify({
            "requests_sent": self.requests_sent,
            "responses_sent": self.responses_sent
        })

target_server = TargetServer()

@app.route("/", methods=["GET"])
def home():
	return "Hello this is Target server, load me with your requests."

@app.route("/test", methods=["GET"])
def test_endpoint():
    return target_server.test_endpoint()

@app.route("/metrics", methods=["GET"])
def metrics_endpoint():
    return target_server.metrics_endpoint()

if __name__ == "__main__":
    app.run(port=8080)
