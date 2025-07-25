#!/usr/bin/env python3
"""
Simple UDP client to test the UDP server
"""
import socket
import sys

def test_udp_server(host='127.0.0.1', port=9000, message='Hello UDP Server!'):
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Send message
        print(f"Sending message to {host}:{port}")
        print(f"Message: {message}")
        
        sock.sendto(message.encode('utf-8'), (host, port))
        print("✅ Message sent successfully!")
        
        # Close socket
        sock.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending UDP message: {e}")
        return False

if __name__ == "__main__":
    # Get message from command line argument if provided
    message = sys.argv[1] if len(sys.argv) > 1 else "Test message from UDP client"
    
    success = test_udp_server(message=message)
    
    if success:
        print("\n🎉 UDP test completed successfully!")
        print("Check the main application console for received message.")
    else:
        print("\n❌ UDP test failed!")
