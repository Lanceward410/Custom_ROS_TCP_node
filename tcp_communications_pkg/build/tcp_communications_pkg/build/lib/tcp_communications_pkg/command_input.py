#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class CommandInputNode(Node):
    def __init__(self):
        super().__init__('command_input_node')
        self.publisher = self.create_publisher(String, '/tcp_commands', 10)
        self.prompt_for_commands()

    def prompt_for_commands(self):
        while rclpy.ok():
            command = input("Enter command (e.g., START_STREAM RGB_IMAGE): ")
            msg = String()
            msg.data = command
            self.publisher.publish(msg)
            self.get_logger().info(f"Sent command: {command}")

def main(args=None):
    rclpy.init(args=args)
    command_input_node = CommandInputNode()
    try:
        rclpy.spin(command_input_node)
    except KeyboardInterrupt:
        command_input_node.get_logger().info("Node terminated")
    finally:
        command_input_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

