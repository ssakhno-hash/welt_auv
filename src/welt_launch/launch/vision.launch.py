import os
from datetime import datetime
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription, ExecuteProcess, TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
import yaml


def generate_launch_description():
    pkg = get_package_share_directory('welt_launch')
    cfg_path = os.path.join(pkg, 'config', 'cameras.yaml')
    qos_path = os.path.join(pkg, 'config', 'qos_overrides.yaml')

    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    topics = []
    for _, p in cfg['cameras'].items():
        topics.append(f"{p['namespace']}/{p['image_topic']}")
        topics.append(f"{p['namespace']}/{p['camera_info_topic']}")

    bag_root = '/tmp/bags'
    session = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    session_dir = os.path.join(bag_root, session)
    os.makedirs(bag_root, exist_ok=True)

    stat = os.statvfs(bag_root)
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
    if free_gb < 2:
        raise RuntimeError(
            f"Not enough space in {bag_root}: {free_gb:.2f} GB (need >= 2 GB)")

    cameras = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg, 'launch', 'camera.launch.py')),
        launch_arguments={'config_file': cfg_path}.items(),
    )

    record = ExecuteProcess(
        cmd=['ros2', 'bag', 'record', '-o', session_dir,
             '--max-bag-size', '1073741824',
             '--qos-profile-overrides-path', qos_path,
             *topics],
        output='screen',
    )

    return LaunchDescription([
        cameras,
        TimerAction(period=3.0, actions=[record]),
    ])
