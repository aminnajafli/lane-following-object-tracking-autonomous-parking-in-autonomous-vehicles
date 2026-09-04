#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from can_msgs.msg import Frame

class DistanceWarnNode(Node):
    def __init__(self):
        super().__init__('distance_warn_node')
        self.subscription = self.create_subscription(
            LaserScan,
            '/limited_scan',
            self.scan_callback,
            10
        )
        self.publisher = self.create_publisher(
            Frame,
            '/otagg_can_tx',
            10
        )
    
        self.declare_parameter('distance_threshold', 2)
        self.distance_threshold = self.get_parameter('distance_threshold').get_parameter_value().double_value

    def scan_callback(self, msg):
        if not msg.ranges:
            return
        
        min_distance = min(msg.ranges)
        self.get_logger().info(f'Minimum distance: {min_distance:.2f} m')

        if min_distance < self.distance_threshold:
            self.get_logger().warn('Obstacle detected within threshold! Sending CAN message.')

def main(args=None):
    rclpy.init(args=args)
    node = DistanceWarnNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

main()
