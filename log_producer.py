import csv
import pika
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
    

# RabbitMQ configuration
rabbitmq_host = 'localhost'  # Change this to your RabbitMQ host if needed
queue_name = 'q.logs'  # Name of the RabbitMQ queue to create and use

delay = 0 # Delay in seconds between processing each log message

def create_rabbitmq_queue():
    """
    Creates a RabbitMQ queue named 'q.logs' with durable settings, only if it doesn't already exist.
    This function establishes a connection to RabbitMQ and declares the queue.
    """

    # Establish a connection to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    # Declare a durable queue
    channel.queue_declare(queue=queue_name, durable=True)

    # Close the connection
    connection.close()


def add_log_to_queue(log_message: str):
    """
    Adds a log message to the RabbitMQ queue 'q.logs'.

    Args:
        log_message (str): The log message to be added to the queue.
    """

    # Establish a connection to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    # Publish the log message to the queue
    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body=log_message,
                          properties=pika.BasicProperties(delivery_mode=2))  # Make message persistent
    logger.info(f"Log message added to queue: {log_message}")
    # Close the connection
    connection.close()  


def read_csv_row_by_row(filename):
    """
    Reads a CSV file row by row and prints each row.

    Args:
        filename (str): The path to the CSV file.
    """
    with open(filename, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            log_message = ' '.join(row)
            add_log_to_queue(log_message)
            time.sleep(delay)

if __name__ == '__main__':
    # Example usage:
    csv_file_path = 'Linux_2k.log_structured.csv'  # Replace with your CSV file path
    create_rabbitmq_queue()
    read_csv_row_by_row(csv_file_path)