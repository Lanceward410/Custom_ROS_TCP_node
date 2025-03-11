#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import socket
import pickle
import threading
import time
from sensor_msgs.msg import Image, LaserScan, PointCloud2
from std_msgs.msg import String

BUFFER_SIZE = 1024
HEADER_SIZE = 1

class ClientNode(Node):
    def __init__(self):
        super().__init__('client_node')
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.subscribers = {}
        self.connect_to_server()
        self.create_subscriptions()

    def create_subscriptions(self):
        self.subscribers["/tcp_command"] = self.create_subscription(String, "/tcp_command", self.handle_command, 10)

    def handle_command(self, msg):
        command = msg.data
        self.get_logger().info(f"Received command: {command}")
        if command.startswith("START_STREAM"):
            _, data_type = command.split()
            self.start_stream(data_type)
        elif command.startswith("STOP_STREAM"):
            _, data_type = command.split()
            self.stop_stream(data_type)

    def serialize_message(self, header_byte, msg):
        try:
            serialized_data = pickle.dumps(msg, protocol=2)
            message_chunks = [header_byte + serialized_data[i:i + BUFFER_SIZE - HEADER_SIZE] for i in range(0, len(serialized_data), BUFFER_SIZE - HEADER_SIZE)]
            return message_chunks
        except Exception as e:
            self.get_logger().error(f"Error serializing message: {e}")
            return None

    def send_data(self, data_chunks):
        try:
            for chunk in data_chunks:
                self.client_socket.sendall(chunk.ljust(BUFFER_SIZE, b'\x00'))
            self.get_logger().info("Data sent successfully")
        except socket.error as e:
            self.get_logger().error(f"Failed to send data: {e}")
            self.reconnect_to_server()

    def handle_image(self, msg):
        data_chunks = self.serialize_message(b'\x01', msg)
        if data_chunks:
            self.send_data(data_chunks)

    def handle_laserscan(self, msg):
        data_chunks = self.serialize_message(b'\x02', msg)
        if data_chunks:
            self.send_data(data_chunks)

    def handle_pointcloud2(self, msg):
        data_chunks = self.serialize_message(b'\x03', msg)
        if data_chunks:
            self.send_data(data_chunks)

    def start_stream(self, data_type):
        if data_type == "RGB_IMAGE":
            self.subscribers["RGB_IMAGE"] = self.create_subscription(Image, "/camera/color/image_raw", self.handle_image, 10)
        elif data_type == "LASER":
            self.subscribers["LASER"] = self.create_subscription(LaserScan, "/scan", self.handle_laserscan, 10)
        elif data_type == "POINT_CLOUD":
            self.subscribers["POINT_CLOUD"] = self.create_subscription(PointCloud2, "/camera/depth/color/points", self.handle_pointcloud2, 10)
        self.get_logger().info(f"Started streaming {data_type}")

    def stop_stream(self, data_type):
        if data_type in self.subscribers:
            self.destroy_subscription(self.subscribers[data_type])
            del self.subscribers[data_type]
            self.get_logger().info(f"Stopped streaming {data_type}")

    def handle_server_communication(self):
        try:
            while rclpy.ok():
                response = self.client_socket.recv(1024)
                if not response:
                    break
                command = response.decode().strip()
                self.get_logger().info(f"Received command: {command}")
                if command.startswith("START_STREAM"):
                    _, data_type = command.split()
                    self.start_stream(data_type)
                elif command.startswith("STOP_STREAM"):
                    _, data_type = command.split()
                    self.stop_stream(data_type)
        except socket.error as e:
            self.get_logger().error(f"Socket error: {e}")
        finally:
            self.client_socket.close()
            self.get_logger().info("Socket closed.")

    def connect_to_server(self):
        server_ip = '192.168.8.125'
        server_port = 42069
        while True:
            try:
                self.client_socket.connect((server_ip, server_port))
                self.get_logger().info(f"Connected to server at {server_ip}:{server_port}")
                communication_thread = threading.Thread(target=self.handle_server_communication)
                communication_thread.start()
                break
            except socket.error as e:
                self.get_logger().error(f"Socket error: {e}. Retrying in 5 seconds...")
                self.client_socket.close()
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                time.sleep(5.0)

    def reconnect_to_server(self):
        self.get_logger().info("Attempting to reconnect to server...")
        self.client_socket.close()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server()

def main(args=None):
    rclpy.init(args=args)
    client_node = ClientNode()
    try:
        rclpy.spin(client_node)
    except KeyboardInterrupt:
        client_node.get_logger().info("Node terminated")
    finally:
        client_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

