from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ubiquity_core_utils',
            executable='odom_tf_broadcaster',
            name='odom_tf_broadcaster',
            output='screen'
        ),
        Node(
            package='ubiquity_core_utils',
            executable='twist_bridge',
            name='twist_bridge',
            output='screen'
        )
    ])