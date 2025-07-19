from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import time

def produce_messages():
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    message = b'Hello, Kafka!'
    producer.send('test_topic', value=message)
    producer.flush()
    print("Message sent successfully: " + message.decode('utf-8'))
    
def consume_messages():
    consumer = KafkaConsumer(
        'test_topic', 
        bootstrap_servers='localhost:9092', 
        auto_offset_reset='earliest', 
        consumer_timeout_ms=5000)
    for message in consumer:
        print(f"Received message: {message.value.decode('utf-8')}")
        time.sleep(1)  # Simulate processing time

if __name__ == "__main__":
    try:
        produce_messages()
        time.sleep(2)  # Ensure the message is sent before consuming
        consume_messages()
    except KafkaError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")    