#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class CommandInput(Node):
    def __init__(self):
        super().__init__('command_input')
        self.publisher = self.create_publisher(String, '/tcp_commands', 10)

    def send_command(self, command):
        msg = String()
        msg.data = command
        self.publisher.publish(msg)
        self.get_logger().info(f"Sent command: {command}")

def main(args=None):
    rclpy.init(args=args)
    node = CommandInput()
    try:
        while True:
            command = input("Enter command (e.g., START_STREAM RGB_IMAGE): ")
            if command.lower() == "exit":
                break
            node.send_command(command)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

