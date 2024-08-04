from flask import Flask, render_template, redirect, url_for, request, Response
import time
from kafka import KafkaProducer
from kafka import KafkaConsumer
from statistics import mean, median
import json
import uuid
import threading

app = Flask(__name__)

class Orchestrator:
    def __init__(self, kafka_bootstrap_servers):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.orchestrator_id = str(uuid.uuid4())
        self.orchestrator_ip = "127.0.0.1"
        self.means = []
        self.medians = []
        self.mins = []
        self.maxs = []
        self.consumer_thread = threading.Thread(target=self._consume_metrics)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
        self.metrics_stream_data = []
        
    def _consume_metrics(self):
        consumer = KafkaConsumer("metrics", bootstrap_servers=self.kafka_bootstrap_servers,
                                 group_id=self.orchestrator_id,
                                 value_deserializer=lambda v: json.loads(v.decode('utf-8')))
        for message in consumer:
            test_metric = message.value
            print(test_metric)
            i_mean_latency = test_metric["mean_latency"]
            i_median_latency = test_metric["median_latency"]
            i_min_latency = test_metric["min_latency"]
            i_max_latency = test_metric["max_latency"]

            self.means.append(i_mean_latency)
            self.medians.append(i_median_latency)
            self.mins.append(i_min_latency)
            self.maxs.append(i_max_latency)

            consumer.commit()

            met1 = {
                "mean_latency": mean(self.means),
                "median_latency": median(self.medians),
                "min_latency": min(self.mins),
                "max_latency": max(self.maxs)
            }
            print("met1 = ", met1)
            self.metrics_stream_data.append(met1)

    def publish_test_config(self, test_type, test_message_delay,  message_count_per_driver):
        test_id = str(uuid.uuid4())
        test_config_message = {
            "test_id":test_id, 
            "test_type":test_type,
            "test_message_delay":test_message_delay,
            "message_count_per_driver": message_count_per_driver
        }
        producer = KafkaProducer(bootstrap_servers=self.kafka_bootstrap_servers)

        try:
            producer.send("testconfig", json.dumps(test_config_message).encode("utf-8"))
            producer.flush()
            print(test_config_message)
            return test_id
        except Exception as e:
            print(f"Error publishing test configuration: {e}")
            return None
        
    # Not Used
    def publish_trigger_message(self, test_id):
        trigger_message = {
            "test_id": test_id,
            "trigger": "YES",
            "last_message": True
        }
        producer = KafkaProducer(bootstrap_servers=self.kafka_bootstrap_servers)
        producer.send("trigger", json.dumps(trigger_message).encode("utf-8"))
        producer.flush()
        print(trigger_message)
        return f"Trigger message published for Test ID: {test_id}"

    def start_load_test(self):
        delay_interval = 5
        message_count_per_driver = 3
        #test_id = self.publish_test_config("AVALANCHE", delay_interval, message_count_per_driver)
        test_id = self.publish_test_config("TSUNAMI", delay_interval, message_count_per_driver)
        self.publish_trigger_message(test_id)

        return test_id
    
    def summary_metric_stream(self):
        while True:
            if self.metrics_stream_data:
                data = self.metrics_stream_data.pop(0)
                yield f'data: {json.dumps(data)}\n\n'
            time.sleep(1)
        
            


orchestrator = Orchestrator("localhost:9092")

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/test_config')
def config():
    test_id = orchestrator.publist_test_config("AVALANCHE", 3, 3)
    # orchestrator.publish_trigger_message(test_id)
    return test_id

@app.route('/publish_testconfig', methods=['POST'])
def publish_testconfig():
    test_type = request.form['test_type']
    test_message_delay = int(request.form['test_message_delay'])
    message_count_per_driver = int(request.form['message_count_per_driver'])
    test_id  = orchestrator.publish_test_config(test_type, test_message_delay, message_count_per_driver)
    # test_id = orchestrator.publist_test_config("AVALANCHE", 3, 3)
    # orchestrator.publish_trigger_message(test_id)
    print(test_id)
    return redirect(url_for('home'))

@app.route('/metricsum', methods=["POST"])
def summary():
    sum_met = orchestrator.summary_metric()
    return sum_met

@app.route('/metrics_stream')
def metrics_stream():
    return Response(orchestrator.summary_metric_stream(), content_type='text/event-stream')
    
if __name__ == "__main__":
    app.run(port=5006,threaded=True, debug=True)