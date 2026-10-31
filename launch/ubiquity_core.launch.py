import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    """Forward legacy ubiquity_core.launch.py to ubiquity_core_utils.launch.py."""
    pkg_dir = get_package_share_directory('ubiquity_core_utils')
    target_launch = os.path.join(pkg_dir, 'launch', 'ubiquity_core_utils.launch.py')
    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(target_launch))
    ])
