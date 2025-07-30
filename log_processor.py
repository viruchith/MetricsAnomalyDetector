import os

import google.generativeai as genai

import pika



def read_api_key_from_file(file_path: str) -> str:
    """Reads the Gemini API key from a file."""
    with open(file_path, 'r') as file:
        return file.read().strip()


# Set your Gemini API key
genai.configure(api_key=read_api_key_from_file("apikey.txt"))

negative_keywords = set([
    "exceeded",
    "failed",
    "fail",
    "failure",
    "error",
    "exception",
    "fatal",
    "critical",
    "panic",
    "abort",
    "denied",
    "rejected",
    "timeout",
    "unavailable",
    "unreachable",
    "invalid",
    "corrupt",
    "overflow",
    "underflow",
    "missing",
    "not found",
    "cannot",
    "unable",
    "disconnect",
    "down",
    "crash",
    "bug",
    "broken",
    "halt",
    "stopped",
    "stop",
    "off",
    "refused",
    "lost",
    "terminated",
    "deprecated",
    "blocked",
    "conflict",
    "unauthorized",
    "forbidden",
    "expired",
    "malformed",
    "incomplete",
    "limit",
    "overflow",
    "retry",
    "shutdown",
    "warning",
    "assert",
    "traceback",
    "stacktrace"
])

negative_log_messages = list()
batch_size = 10

def is_log_critical(log_message: str) -> str:
    """
    Uses Gemini API to determine whether a log message is critical.
    Returns True if critical, False otherwise.
    """
    prompt = (
        "You are a helpful assistant. Determine if the following log message is critical.\n"
        "Return only whether log message is 'CRITICAL' true or false along with the log message itself as 'message' attribute and the reason for its criticality as 'reason' attribute, as a JSON response only.\n"
        f"Log message: {log_message}"
    )

    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)

    output = response.text.strip().upper()
    return output

# Example usage
log_msg = "Database connection failed: timeout after 30s"
# is_critical = is_log_critical(log_msg)
# print(f"Is the log message critical? {is_critical}")



def is_log_message_negative(log_message: str) -> bool:
    """
    Checks if the log message contains any negative keywords.
    Returns True if it contains a negative keyword, False otherwise.
    """
    log_message_lower = log_message.lower()
    for keyword in negative_keywords:
        if keyword in log_message_lower:
            return True
    return False

def process_log_message(log_message: str) -> None:
    """
    Processes a log message to determine if it is critical or contains negative keywords.
    Returns True if the log message is critical or contains negative keywords, False otherwise.
    """
    if is_log_message_negative(log_message) and len(negative_log_messages) < batch_size:
        negative_log_messages.append(log_message)
    else:
        combined_message = "\n".join(negative_log_messages)
        # Send the combined message to the Gemini API for further analysis
        is_critical = is_log_critical(combined_message)
        print(f"Is the combined log message critical? {is_critical}")
        negative_log_messages.clear()   

def consume_messages_from_queue():
    """
    Consumes messages from the RabbitMQ queue and processes them.
    This function connects to the RabbitMQ server, consumes messages from the 'q.logs' queue,
    and checks if each log message is critical using the Gemini API.
    """

    # Establish a connection to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # Declare the queue to ensure it exists
    channel.queue_declare(queue='q.logs', durable=True)

    def callback(ch, method, properties, body):
        print("Received a message from the queue.")
        log_message = body.decode('utf-8')
        process_log_message(log_message)
        print(f"Log message: {log_message}")

    # Start consuming messages
    channel.basic_consume(queue='q.logs', on_message_callback=callback, auto_ack=True)

    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()   
    
if __name__ == '__main__':
    # Example usage:
    consume_messages_from_queue()