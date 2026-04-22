from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import LaunchConfigurationEquals
from launch_ros.actions import Node

def generate_launch_description():
    # Declare the generation argument
    generation_arg = DeclareLaunchArgument(
        'generation',
        default_value='gen6',
        description='Robot generation (gen5 or gen6)'
    )
    
    # Launch odom_tf_broadcaster only for Gen6
    odom_node = Node(
        package='ubiquity_core_utils',
        executable='odom_tf_broadcaster',
        name='odom_tf_broadcaster',
        output='screen',
        condition=LaunchConfigurationEquals('generation', 'gen6')
    )
    
    # Launch twist_bridge only for Gen5
    twist_bridge_node = Node(
        package='ubiquity_core_utils',
        executable='twist_bridge',
        name='twist_bridge',
        output='screen',
        condition=LaunchConfigurationEquals('generation', 'gen5')
    )
    
    return LaunchDescription([
        generation_arg,
        odom_node,
        twist_bridge_node
    ])
