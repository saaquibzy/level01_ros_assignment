import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    nav_share = get_package_share_directory('testbed_navigation')

    map_loader = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav_share, 'launch', 'map_loader.launch.py')
        )
    )

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav_share, 'launch', 'localization.launch.py')
        )
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav_share, 'launch', 'navigation.launch.py')
        )
    )

    return LaunchDescription([
        map_loader,
        localization,
        navigation
    ])
