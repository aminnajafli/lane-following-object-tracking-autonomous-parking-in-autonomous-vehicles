#!/usr/bin/env python3

import queue
import rclpy
from rclpy.node import Node
from otagg_control.connections.arduino_connection import ArduinoConnection, CloneArduinoConnection
from otagg_control.connections.stm_connection import STMConnection
from can_msgs.msg import Frame

class ConnectionNode(Node):
    def __init__(self):
        super().__init__('connection_node')
        self.get_logger().info('Connection node has been started.')
        # Connection type: arduino, stm32, clone_arduino
        self.declare_parameter('connection_type', 'uart_bridge')
        self.declare_parameter('baudrate', '9600')

        connection_type = self.get_parameter('connection_type').get_parameter_value().string_value
        baudrate = int(self.get_parameter('baudrate').get_parameter_value().string_value)
        self.board = None

        if connection_type == 'arduino':
            self.board = ArduinoConnection(baudrate)
        elif connection_type == 'clone_arduino':
            self.board = CloneArduinoConnection(baudrate)
        elif connection_type == 'stm32':
            self.board = STMConnection(baudrate)
        elif connection_type == 'uart_bridge':
            from otagg_control.connections.uart_bridge_connection import UARTBridgeConnection
            self.board = UARTBridgeConnection(baudrate)
        else:
            self.get_logger().warn('No valid connection type specified. Running in disconnected mode.')
            return
        
        if not self.board.connect():
            self.get_logger().error(f'Failed to connect: {self.board.get_error()}')
            return
        
        # Initialize queue for sending CAN frames
        self.send_queue = queue.Queue()
        
        self.can_subscriber = self.create_subscription(
            Frame,
            '/otagg_can_tx',
            self.can_rx_callback,
            10
        )

        self.can_publisher = self.create_publisher(
            Frame,
            '/otagg_can_rx',
            10
        )
        self.timer = self.create_timer(0.2, self.timer_callback)

    def can_rx_callback(self, msg: Frame):
        # Add frame to send queue instead of sending immediately
        self.send_queue.put(msg)
    
    def timer_callback(self):
        # Process send queue
        while not self.send_queue.empty():
            try:
                msg = self.send_queue.get_nowait()
                if not self.board.send_can_frame(msg.id, msg.data):
                    self.get_logger().error(f'Failed to send CAN frame: {self.board.get_error()}')
            except queue.Empty:
                break

def main(args=None):
    rclpy.init(args=args)
    node = ConnectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
