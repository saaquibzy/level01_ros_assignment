import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    map_yaml_path = os.path.join(
        get_package_share_directory('testbed_bringup'),
        'maps',
        'testbed_world.yaml'
    )

    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'yaml_filename': map_yaml_path}]
    )

    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[{
            'autostart': True,
            'node_names': ['map_server']
        }]
    )

    return LaunchDescription([
        map_server_node,
        lifecycle_manager_node
    ])
