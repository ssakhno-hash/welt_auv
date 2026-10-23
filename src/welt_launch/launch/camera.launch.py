import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def make_cameras(context, *args, **kwargs):
    config_file = LaunchConfiguration('config_file').perform(context)
    with open(config_file, 'r') as f:
        cfg = yaml.safe_load(f)

    nodes = []
    for cam_name, p in cfg['cameras'].items():
        nodes.append(Node(
            package='usb_cam',
            executable='usb_cam_node_exe',
            name=f'{cam_name}_usb_cam',
            namespace=p['namespace'],
            parameters=[{
                'video_device': p['device'],
                'framing.frame_id': p['frame_id'],
                'pixel_format': p['pixel_format'],
                'image_width': p['image_width'],
                'image_height': p['image_height'],
                'framerate': p['framerate'],
                'publish_camera_info': True,
            }],
            remappings=[
                ('image_raw', p['image_topic']),
                ('camera_info', p['camera_info_topic']),
            ],
            output='screen',
        ))
    return nodes


def generate_launch_description():
    default_cfg = os.path.join(
        get_package_share_directory('welt_launch'), 'config', 'cameras.yaml')

    return LaunchDescription([
        DeclareLaunchArgument(
            'config_file', default_value=default_cfg,
            description='Путь к YAML с описанием камер'),
        OpaqueFunction(function=make_cameras),
    ])
