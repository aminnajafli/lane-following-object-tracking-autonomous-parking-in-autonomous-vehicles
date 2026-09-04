#!/usr/bin/env python3

from geometry_msgs.msg import Twist
from rclpy.node import Node
import rclpy
from can_msgs.msg import Frame
from time import sleep


class CmdVelListener(Node):
    def __init__(self):
        super().__init__('cmd_vel_listener')
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.can_publisher = self.create_publisher(
            Frame,
            '/otagg_can_tx',
            10
        )

        self.old_linear_x = 0.0
        self.old_angular_z = 0.0

    def cmd_vel_callback(self, msg):
        self.get_logger().info(f'Received cmd_vel: linear={msg.linear.x:.2f}, angular={msg.angular.z:.2f}')

        linear_can_msg = Frame()
        linear_can_msg.id = 0x10
        linear_can_msg.dlc = 8

        bldc_direction = 1 if msg.linear.x > 0 else 0

        angular_can_msg = Frame()
        angular_can_msg.id = 0x11
        angular_can_msg.dlc = 8

        # BLDC Motor logic (Linear Velocity -> PWM 200 to 500)
        max_vel = 2.0
        if msg.linear.x > 0.01:
            bldc_pwm = int(200 + (msg.linear.x / max_vel) * (500 - 200))
            bldc_pwm = min(500, max(200, bldc_pwm))
        elif msg.linear.x < -0.01:
            bldc_pwm = int(200 + (-msg.linear.x / max_vel) * (500 - 200)) # Adjust as needed for reverse
            bldc_pwm = min(500, max(200, bldc_pwm))

        else:
            bldc_pwm = 0

        # Step Motor logic (Angular Velocity -> Direction (0/1) and Angle (0-50))
        # Assuming msg.angular.z max is ~1.0 rad/s for full 50 degree turn
        max_angular = 1.0 
        angle_ratio = min(1.0, abs(msg.angular.z) / max_angular)
        steering_angle = int(angle_ratio * 100)
        
        step_direction = 1 if msg.angular.z < 0 else 0

        linear_can_msg.data = [
            bldc_direction & 0xFF,
            (bldc_pwm >> 8) & 0xFF,
            bldc_pwm & 0xFF,
            0, 0, 0, 0, 0
        ]

        angular_can_msg.data = [
            step_direction & 0xFF,
            steering_angle & 0xFF,
            0, 0, 0, 0, 0, 0
        ]

        if (abs(msg.linear.x - self.old_linear_x) > 0.01):
            self.can_publisher.publish(linear_can_msg)
            self.old_linear_x = msg.linear.x

        sleep(0.01)  # Small delay to prevent flooding the CAN bus

        if (abs(msg.angular.z - self.old_angular_z) > 0.01):
            self.can_publisher.publish(angular_can_msg)
            self.old_angular_z = msg.angular.z

def main(args=None):
    rclpy.init(args=args)
    node = CmdVelListener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
