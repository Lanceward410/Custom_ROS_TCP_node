#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import socket
import threading
from sensor_msgs.msg import Image, PointCloud2, LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped
from rtabmap_msgs.msg import MapData
import pickle

class ClientNode(Node):
    def __init__(self):
        super().__init__('client_node')
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.subscribers = {}

    def handle_server_communication(self):
        try:
            while rclpy.ok():
                response = self.client_socket.recv(1024)
                if not response:
                    break
                self.get_logger().info(f"Received from server: {response.decode()}")
                self.handle_server_command(response.decode())
        except socket.error as e:
            self.get_logger().error(f"Socket error: {e}")
        finally:
            self.client_socket.close()
            self.get_logger().info("Socket closed.")

    def handle_server_command(self, command):
        if command.startswith("START_STREAM"):
            data_type = command.split()[1]
            self.start_stream(data_type)
        elif command.startswith("STOP_STREAM"):
            data_type = command.split()[1]
            self.stop_stream(data_type)

    def start_stream(self, data_type):
        if data_type == "RGB_IMAGE":
            self.subscribers["RGB_IMAGE"] = self.create_subscription(
                Image, "/camera/color/image_raw", self.send_rgb_image_stream, 5)
        elif data_type == "DEPTH_IMAGE":
            self.subscribers["DEPTH_IMAGE"] = self.create_subscription(
                Image, "/camera/depth/image_rect_raw", self.send_depth_image_stream, 5)
        elif data_type == "POINT_CLOUD":
            self.subscribers["POINT_CLOUD"] = self.create_subscription(
                PointCloud2, "/camera/depth/color/points", self.send_point_cloud_stream, 5)
        elif data_type == "LIDAR":
            self.subscribers["LIDAR"] = self.create_subscription(
                LaserScan, "/scan", self.send_lidar_stream, 10)
        elif data_type == "POSE":
            self.subscribers["POSE"] = self.create_subscription(
                PoseStamped, "/pose", self.send_pose_stream, 10)
        elif data_type == "ODOMETRY":
            self.subscribers["ODOMETRY"] = self.create_subscription(
                Odometry, "/odom", self.send_odometry_stream, 10)
        elif data_type == "MAP_DATA":
            self.subscribers["MAP_DATA"] = self.create_subscription(
                MapData, "/mapData", self.send_map_data_stream, 10)
        self.get_logger().info(f"Started streaming {data_type}")

    def stop_stream(self, data_type):
        if data_type in self.subscribers:
            self.destroy_subscription(self.subscribers[data_type])
            del self.subscribers[data_type]
            self.get_logger().info(f"Stopped streaming {data_type}")

    def send_rgb_image_stream(self, data):
        serialized_data = pickle.dumps(data)
        self.client_socket.sendall(serialized_data)
        self.get_logger().info("Streaming RGB image")

    def send_depth_image_stream(self, data):
        serialized_data = pickle.dumps(data)
        self.client_socket.sendall(serialized_data)
        self.get_logger().info("Streaming depth image")

    def send_point_cloud_stream(self, data):
        serialized_data = pickle.dumps(data)
        self.client_socket.sendall(serialized_data)
        self.get_logger().info("Streaming point cloud")

    def send_lidar_stream(self, data):
        serialized_data = pickle.dumps(data)
        self.client_socket.sendall(serialized_data)
        self.get_logger().info("Streaming Lidar scan")

    def send_pose_stream(self, data):
        serialized_data = pickle.dumps(data)
        self.client_socket.sendall(serialized_data)
        self.get_logger().info("Streaming pose data")

    def send_odometry_stream(self, data):
        serialized_data = pickle.dumps(data)
        self.client_socket.sendall(serialized_data)
        self.get_logger().info("Streaming odometry data")

    def send_map_data_stream(self, data):
        serialized_data = pickle.dumps(data)
        self.client_socket.sendall(serialized_data)
        self.get_logger().info("Streaming map data")

    def connect_to_server(self):
        server_ip = '192.168.8.222'
        server_port = 11312

        try:
            self.client_socket.connect((server_ip, server_port))
            self.get_logger().info(f"Connected to server at {server_ip}:{server_port}")

            thread = threading.Thread(target=self.handle_server_communication)
            thread.start()

            input_thread = threading.Thread(target=self.capture_user_input)
            input_thread.start()

        except socket.error as e:
            self.get_logger().error(f"Socket error: {e}")
            self.client_socket.close()

    def capture_user_input(self):
        while rclpy.ok():
            command = input("Enter command (e.g., START_STREAM RGB_IMAGE): ")
            self.send_command(command)

    def send_command(self, command):
        try:
            self.client_socket.sendall(command.encode())
            self.get_logger().info(f"Sent command: {command}")
        except socket.error as e:
            self.get_logger().error(f"Failed to send command: {e}")

def main(args=None):
    rclpy.init(args=args)
    client_node = ClientNode()
    client_node.connect_to_server()
    try:
        rclpy.spin(client_node)
    except KeyboardInterrupt:
        client_node.get_logger().info("Node terminated")
    finally:
        client_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

