
def generate_launch_description():
    from launch import LaunchDescription
    from launch_ros.actions import Node

    return LaunchDescription([
        Node(
            package='otagg_control',
            executable='connection.py',
            output='screen',
            parameters=[{
                'connection_type': 'uart_bridge',
            }]
        ),
        Node(
            package='otagg_control',
            executable='cmd_vel_listener.py',
            output='screen'
        ),
        Node(
            package='joy',
            executable='joy_node',
            output='screen'
        ),
    ])
