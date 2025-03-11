#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import socket
import threading
from sensor_msgs.msg import Image, PointCloud2, LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped
from rtabmap_msgs.msg import MapData

class ServerNode(Node):
    def __init__(self):
        super().__init__('server_node')
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_publishers = {}

    def handle_client_connection(self, client_socket, address):
        client_id = f"{address[0].replace('.', '_')}_{address[1]}"
        self.get_logger().info(f"Connected to client {client_id} at {address}")
        client_socket.settimeout(120)  # Set timeout to 120 seconds
        
        try:
            while rclpy.ok():
                data = client_socket.recv(1024)
                if not data:
                    self.get_logger().info("No data received. Client may have closed the connection.")
                    break
                self.get_logger().info(f"Received data from client {client_id} at {address}")
                self.process_received_data(client_id, data)
        except socket.error as e:
            self.get_logger().error(f"Socket error with {client_id} at {address}: {e}")
        finally:
            client_socket.close()
            self.get_logger().info(f"Connection with {client_id} at {address} closed")
            self.cleanup_publishers(client_id)

    def process_received_data(self, client_id, data):
        # Process the received data and publish to appropriate topics
        try:
            # Assume data comes as "DATA_TYPE|payload"
            data_type, payload = data.decode().split("|", 1)
            topic_name = f"/received/{data_type.lower()}/{client_id}"
            if topic_name not in self.publishers:
                self.publishers[topic_name] = self.create_publisher_for_type(data_type, topic_name)
            msg = self.create_message(data_type, payload)
            if msg:
                self.publishers[topic_name].publish(msg)
        except Exception as e:
            self.get_logger().error(f"Failed to process data: {e}")

    def create_publisher_for_type(self, data_type, topic_name):
        if data_type == "RGB_IMAGE":
            return self.create_publisher(Image, topic_name, 10)
        elif data_type == "DEPTH_IMAGE":
            return self.create_publisher(Image, topic_name, 10)
        elif data_type == "POINT_CLOUD":
            return self.create_publisher(PointCloud2, topic_name, 10)
        elif data_type == "LIDAR":
            return self.create_publisher(LaserScan, topic_name, 10)
        elif data_type == "POSE":
            return self.create_publisher(PoseStamped, topic_name, 10)
        elif data_type == "ODOMETRY":
            return self.create_publisher(Odometry, topic_name, 10)
        elif data_type == "MAP_DATA":
            return self.create_publisher(MapData, topic_name, 10)
        else:
            self.get_logger().error(f"Unsupported data type: {data_type}")
            return None

    def create_message(self, data_type, payload):
        # Create the appropriate message type based on the data_type and payload
        msg = None
        if data_type == "RGB_IMAGE":
            msg = Image()  # Populate with the actual data from payload
        elif data_type == "DEPTH_IMAGE":
            msg = Image()  # Populate with the actual data from payload
        elif data_type == "POINT_CLOUD":
            msg = PointCloud2()  # Populate with the actual data from payload
        elif data_type == "LIDAR":
            msg = LaserScan()  # Populate with the actual data from payload
        elif data_type == "POSE":
            msg = PoseStamped()  # Populate with the actual data from payload
        elif data_type == "ODOMETRY":
            msg = Odometry()  # Populate with the actual data from payload
        elif data_type == "MAP_DATA":
            msg = MapData()  # Populate with the actual data from payload
        else:
            self.get_logger().error(f"Unsupported data type: {data_type}")
        return msg

    def cleanup_publishers(self, client_id):
        topics_to_remove = [topic for topic in self.publishers if client_id in topic]
        for topic in topics_to_remove:
            self.publishers.pop(topic, None)
            self.get_logger().info(f"Cleaned up publisher for topic: {topic}")

    def start_server(self):
        server_ip = ''  # Listen on all available interfaces
        server_port = 11312  # The port on which to listen for incoming data
        self.server_socket.bind((server_ip, server_port))
        self.server_socket.listen(5)  # Maximum of 5 queued connections
        self.get_logger().info(f"Server is listening on port {server_port}")

        try:
            while rclpy.ok():
                self.get_logger().info("Waiting for a connection...")
                client_socket, addr = self.server_socket.accept()
                # Start a new thread for each client connection
                thread = threading.Thread(target=self.handle_client_connection, args=(client_socket, addr))
                thread.start()
        except KeyboardInterrupt:
            self.get_logger().info("Server is shutting down...")
        finally:
            self.server_socket.close()
            self.get_logger().info("Server socket closed.")

def main(args=None):
    rclpy.init(args=args)
    server_node = ServerNode()
    server_node.start_server()
    try:
        rclpy.spin(server_node)
    except KeyboardInterrupt:
        server_node.get_logger().info("ROS node terminated")
    finally:
        server_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
