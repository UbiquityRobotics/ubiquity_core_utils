import math
import time

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import rclpy
from sensor_msgs.msg import BatteryState
from ubiquity_core_utils.odom_tf_broadcaster import OdomTFBroadcaster
from ubiquity_core_utils.twist_bridge import TwistBridge


def setup_module():
    rclpy.init()


def teardown_module():
    rclpy.shutdown()


def test_twist_bridge():
    node = TwistBridge()
    received = []
    node.pub = type('MockPub', (), {'publish': lambda self, msg: received.append(msg)})()

    twist = Twist()
    twist.linear.x = 0.5
    twist.angular.z = 1.2
    node.cmd_vel_callback(twist)

    assert len(received) == 1
    stamped = received[0]
    assert stamped.twist.linear.x == 0.5
    assert stamped.twist.angular.z == 1.2
    assert stamped.header.frame_id == 'base_link'
    assert stamped.header.stamp.sec > 0 or stamped.header.stamp.nanosec > 0
    node.destroy_node()


def test_battery_relay_normalization():
    node = OdomTFBroadcaster()
    received = []
    node.battery_pub = type('MockPub', (), {'publish': lambda self, msg: received.append(msg)})()

    # Case 1: msg.charge in 0..100 range
    b1 = BatteryState()
    b1.charge = 85.0
    b1.percentage = float('nan')
    node.battery_callback(b1)
    assert math.isclose(received[-1].percentage, 0.85, rel_tol=1e-3)
    assert received[-1].header.stamp.sec > 0 or received[-1].header.stamp.nanosec > 0

    # Case 2: msg.percentage > 1.0 (e.g. 74.0%)
    b2 = BatteryState()
    b2.percentage = 74.0
    node.battery_callback(b2)
    assert math.isclose(received[-1].percentage, 0.74, rel_tol=1e-3)

    # Case 3: already normalized 0.0..1.0
    b3 = BatteryState()
    b3.percentage = 0.62
    node.battery_callback(b3)
    assert math.isclose(received[-1].percentage, 0.62, rel_tol=1e-3)
    node.destroy_node()


def test_odometry_fast_path():
    node = OdomTFBroadcaster()
    odom_received = []
    node.odom_pub = type('MockPub', (), {'publish': lambda self, msg: odom_received.append(msg)})()

    # Single MCB
    m = Odometry()
    m.pose.pose.position.x = 2.0
    m.pose.pose.position.y = 1.0
    m.pose.pose.orientation.w = 1.0
    m.twist.twist.linear.x = 0.4
    node.msgs['/mcb/odometry'] = (m, time.monotonic())

    node.publish_odometry()
    assert len(odom_received) == 1
    res = odom_received[0]
    assert res.pose.pose.position.x == 2.0
    assert res.pose.pose.position.y == 1.0
    assert res.pose.pose.orientation.w == 1.0
    assert res.twist.twist.linear.x == 0.4
    assert res.header.frame_id == 'odom'
    assert res.child_frame_id == 'base_link'
    node.destroy_node()


def test_odometry_stale_filter():
    node = OdomTFBroadcaster()
    odom_received = []
    node.odom_pub = type('MockPub', (), {'publish': lambda self, msg: odom_received.append(msg)})()

    # Message older than stale timeout (1.0s)
    m = Odometry()
    m.pose.pose.position.x = 5.0
    node.msgs['/mcb/odometry'] = (m, time.monotonic() - 2.5)

    node.publish_odometry()
    assert len(odom_received) == 0
    node.destroy_node()


def test_odometry_multi_mcb_averaging():
    node = OdomTFBroadcaster()
    odom_received = []
    node.odom_pub = type('MockPub', (), {'publish': lambda self, msg: odom_received.append(msg)})()

    # Two MCBs (e.g. front and rear controllers)
    m1 = Odometry()
    m1.pose.pose.position.x = 1.0
    m1.pose.pose.orientation.w = 1.0

    m2 = Odometry()
    m2.pose.pose.position.x = 3.0
    m2.pose.pose.orientation.w = 1.0

    now = time.monotonic()
    node.msgs['/mcb1/odometry'] = (m1, now)
    node.msgs['/mcb2/odometry'] = (m2, now)

    node.publish_odometry()
    assert len(odom_received) == 1
    res = odom_received[0]
    assert math.isclose(res.pose.pose.position.x, 2.0, rel_tol=1e-3)
    assert math.isclose(res.pose.pose.orientation.w, 1.0, rel_tol=1e-3)
    node.destroy_node()
