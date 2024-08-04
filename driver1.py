import time
import json
import uuid
from statistics import mean, median
import requests
from kafka import KafkaProducer
from kafka import KafkaConsumer
from flask import Flask, render_template, redirect

app = Flask(__name__)

class DriverNode:
    def __init__(self, kafka_bootstrap_servers, target_server_url):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.target_server_url = target_server_url
        self.driver_id = str(uuid.uuid4())
        self.response_times = []

    def send_request(self):
        print("sending")
        start_time = time.time()
        url = "http://localhost:8080/test"
        
        # A GET request to the API
        response = requests.get(url)

        print("response= ", response)
        end_time = time.time()
        response_time = (end_time - start_time)
        return response_time
    
    def record_statistics(self, response_time):
        self.response_times.append(response_time)
    
    def publish_metrics(self):
        if not self.response_times:
            return {
                "mean_latency": 0,
                "meadian_lantency": None,
                "min_latancy": None,
                "max_latency": None
            }
        
        mean_lentency = mean(self.response_times)
        median_latency = median(self.response_times)
        min_latency = min(self.response_times)
        max_latency = max(self.response_times)
        self.response_times = []

        metrics = {
            "mean_latency":mean_lentency,
            "median_latency":median_latency,
            "min_latency": min_latency,
            "max_latency": max_latency
        }
        producer = KafkaProducer(bootstrap_servers=self.kafka_bootstrap_servers)
        producer.send("metrics", json.dumps(metrics).encode("utf-8"))
        producer.flush()

        return metrics
    
    def start(self):

        print("hi")
        consumer = KafkaConsumer("testconfig", bootstrap_servers= self.kafka_bootstrap_servers,
                                group_id = self.driver_id,
                                value_deserializer = lambda v: json.loads(v.decode('utf-8')))
        print("Hello")

        print("response time before ", self.response_times)

        for message in consumer:
            test_config = message.value
            print(test_config)
            test_type = test_config["test_type"]
            test_message_delay = test_config["test_message_delay"]
            num_requests = test_config["message_count_per_driver"]

            consumer.commit()
            
            if test_type == "AVALANCHE":
                self.avalanche_test(num_requests)
            elif test_type == "TSUNAMI":
                self.tsunami_test(test_message_delay, num_requests)
            
            metric1 = self.publish_metrics()
            print(f"metric for {test_type} ", metric1)
            

        

        # self.avalanche_test(3)

        # metric1 = self.publish_metrics()
        # print("metric for Ava ", metric1)
        
        # self.tsunami_test(5, 3)

        # metric2 = self.publish_metrics()
        # print("metric for Tsu ", metric2)

        # print("response time after ", self.response_times)
        
        

        

    def avalanche_test(self, num_requests):
            for _ in range(num_requests):
                print("Ava")
                response_time = self.send_request()
                self.record_statistics(response_time)
                print(response_time)
            return 

    def tsunami_test(self, delay_interval, num_requests):
        request_interval = delay_interval # Convert delay_interval to seconds

        for _ in range(num_requests):
            print("tsu")
            response_time = self.send_request()
            self.record_statistics(response_time)
            print(response_time)
            time.sleep(request_interval)

        return 

# Instantiate the DriverNode
kafka_ip = "localhost:9092"  # Replace with the Kafka broker address
target_server_url = "https://www.yahoo.com/"  # Replace with the target server URL
# num_requests = 100  # Specify the number of requests for testing
driver_node = DriverNode(kafka_bootstrap_servers=kafka_ip, target_server_url=target_server_url)

@app.route('/metric')
def view_statistics():
    statistics = driver_node.publish_metrics()
    return statistics

@app.route('/start')
def start():
    driver_node.start()
    return "Test has started"

@app.route('/')
def home():
    return "This is driver node."

if __name__ == "__main__":
    # Start the Flask web server
    app.run(port=5001,threaded=True, debug=True)