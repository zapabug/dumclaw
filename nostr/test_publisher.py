import time
import threading
from nostr.publisher import start_publisher, send_note


def test_publisher():
    print("Starting publisher test...")
    
    # Start the publisher
    start_publisher()
    
    # Give it a moment to connect
    time.sleep(2)
    
    # Send a test note
    print("Sending test note...")
    send_note("This is a test message from the new publisher")
    
    # Wait a bit to see if it sends successfully
    time.sleep(5)
    
    print("Test complete")


if __name__ == "__main__":
    test_publisher()