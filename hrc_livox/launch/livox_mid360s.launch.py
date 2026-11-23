"""Launch the official livox_ros_driver2 node for HRC Mid-360S lidars.

Examples:
  ros2 launch hrc_livox livox_mid360s.launch.py               # unit 1 + RViz
  ros2 launch hrc_livox livox_mid360s.launch.py lidar:=2      # unit 2
  ros2 launch hrc_livox livox_mid360s.launch.py lidar:=all    # both (via a switch)
  ros2 launch hrc_livox livox_mid360s.launch.py rviz:=false xfer_format:=1   # CustomMsg for FAST-LIO
"""
import os
import sys
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from livox_config_utils import write_config  # noqa: E402


def _launch_driver(context):
    lidar = LaunchConfiguration('lidar').perform(context)
    lidars_file = LaunchConfiguration('lidars_file').perform(context)
    xfer_format = int(LaunchConfiguration('xfer_format').perform(context))
    frame_id = LaunchConfiguration('frame_id').perform(context)
    publish_freq = float(LaunchConfiguration('publish_freq').perform(context))

    driver_share = get_package_share_directory('livox_ros_driver2')
    template = os.path.join(driver_share, 'config', 'MID360s_config.json')

    safe_name = lidar.replace(',', '_')
    out_path = os.path.join(tempfile.gettempdir(), f'hrc_livox_mid360s_{safe_name}.json')
    ips = write_config(template, lidars_file, lidar, out_path)

    # Several lidars -> one topic per lidar (topic names include the lidar IP)
    multi_topic = 1 if len(ips) > 1 else 0

    driver = Node(
        package='livox_ros_driver2',
        executable='livox_ros_driver2_node',
        name='livox_lidar_publisher',
        output='screen',
        parameters=[{
            'xfer_format': xfer_format,      # 0: PointCloud2, 1: Livox CustomMsg
            'multi_topic': multi_topic,
            'data_src': 0,                   # 0: real lidar
            'publish_freq': publish_freq,
            'output_data_type': 0,
            'frame_id': frame_id,
            'lvx_file_path': '',
            'user_config_path': out_path,
            'cmdline_input_bd_code': 'livox0000000001',
        }],
    )
    return [
        LogInfo(msg=f'[hrc_livox] lidar={lidar} ips={ips} config={out_path}'),
        driver,
    ]


def generate_launch_description():
    hrc_share = get_package_share_directory('hrc_livox')
    driver_share = get_package_share_directory('livox_ros_driver2')
    rviz_cfg = os.path.join(driver_share, 'config', 'display_point_cloud_ROS2.rviz')

    return LaunchDescription([
        DeclareLaunchArgument('lidar', default_value='1',
                              description="Which unit: '1', '2', 'all' or '1,2'"),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('xfer_format', default_value='0',
                              description='0: PointCloud2 (RViz), 1: CustomMsg (FAST-LIO)'),
        DeclareLaunchArgument('frame_id', default_value='livox_frame'),
        DeclareLaunchArgument('publish_freq', default_value='10.0'),
        DeclareLaunchArgument('lidars_file',
                              default_value=os.path.join(hrc_share, 'config', 'lidars.yaml')),
        OpaqueFunction(function=_launch_driver),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_cfg],
            output='screen',
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
