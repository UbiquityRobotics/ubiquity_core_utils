import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'ubiquity_core_utils'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Michael Valand',
    maintainer_email='michael.valand@gmail.com',
    description='Hardware bridge and telemetry utilities for Ubiquity Robotics Magni robots',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'odom_tf_broadcaster = ubiquity_core_utils.odom_tf_broadcaster:main',
            'twist_bridge = ubiquity_core_utils.twist_bridge:main',
        ],
    },
)
