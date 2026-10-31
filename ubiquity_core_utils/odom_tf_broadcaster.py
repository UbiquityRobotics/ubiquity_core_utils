import math
import time

from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from tf2_ros import TransformBroadcaster


class OdomTFBroadcaster(Node):
    """Bridges raw MCB odometry and battery telemetry to standard stamped ROS 2 topics."""

    def __init__(self):
        super().__init__('odom_tf_broadcaster')
        self.declare_parameter('odom_frame_id', 'odom')
        self.declare_parameter('base_frame_id', 'base_link')
        self.declare_parameter('publish_rate_hz', 20.0)
        self.declare_parameter('stale_timeout_sec', 1.0)
        self.declare_parameter('publish_tf', True)

        self.odom_frame_id = self.get_parameter(
            'odom_frame_id').get_parameter_value().string_value
        self.base_frame_id = self.get_parameter(
            'base_frame_id').get_parameter_value().string_value
        self.stale_timeout = self.get_parameter(
            'stale_timeout_sec').get_parameter_value().double_value
        self.publish_tf = self.get_parameter(
            'publish_tf').get_parameter_value().bool_value
        rate = max(1.0, self.get_parameter('publish_rate_hz').get_parameter_value().double_value)

        self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        # Relay /mcb/battery_state to /battery_state with normalization
        self.battery_pub = self.create_publisher(BatteryState, '/battery_state', 10)
        self.battery_sub = self.create_subscription(
            BatteryState, '/mcb/battery_state', self.battery_callback, 10
        )

        self.subs = {}
        self.msgs = {}

        self.create_timer(5.0, self.discover_topics)
        self.discover_topics()
        self.create_timer(1.0 / rate, self.publish_odometry)

    def battery_callback(self, msg: BatteryState):
        """Relay and normalize battery telemetry for standard ROS 2 monitoring."""
        if msg.header.stamp.sec == 0 and msg.header.stamp.nanosec == 0:
            msg.header.stamp = self.get_clock().now().to_msg()
        if 0.0 < msg.charge <= 100.0 and (math.isnan(msg.percentage) or msg.percentage <= 0.0):
            msg.percentage = float(msg.charge) / 100.0
        elif msg.percentage > 1.0:
            msg.percentage = float(msg.percentage) / 100.0
        self.battery_pub.publish(msg)

    def discover_topics(self):
        """Discover active MCB odometry topics and register subscriptions."""
        for name, types in self.get_topic_names_and_types():
            if 'nav_msgs/msg/Odometry' in types and 'mcb' in name and name not in self.subs:
                self.get_logger().info(f"Subscribing to MCB odometry topic: '{name}'")
                self.subs[name] = self.create_subscription(
                    Odometry, name, lambda m, t=name: self._record_odom(t, m), 10
                )

    def _record_odom(self, topic: str, msg: Odometry):
        self.msgs[topic] = (msg, time.monotonic())

    def publish_odometry(self):
        """Aggregate odometry sources, stamp with current ROS time, and broadcast TF."""
        if not self.msgs:
            return

        now_mono = time.monotonic()
        active = [m for m, t in self.msgs.values() if (now_mono - t) <= self.stale_timeout]
        if not active:
            return

        now_ros = self.get_clock().now().to_msg()
        n_msgs = len(active)

        if n_msgs == 1:
            m = active[0]
            odom = Odometry()
            odom.header.stamp = now_ros
            odom.header.frame_id = self.odom_frame_id
            odom.child_frame_id = self.base_frame_id
            odom.pose = m.pose
            odom.twist = m.twist
            q = m.pose.pose.orientation
            pos = m.pose.pose.position
        else:
            odom = Odometry()
            odom.header.stamp = now_ros
            odom.header.frame_id = self.odom_frame_id
            odom.child_frame_id = self.base_frame_id
            odom.pose.pose.orientation.w = 0.0
            inv_n = 1.0 / n_msgs

            for m in active:
                p = m.pose.pose.position
                o = m.pose.pose.orientation
                tw = m.twist.twist
                odom.pose.pose.position.x += p.x * inv_n
                odom.pose.pose.position.y += p.y * inv_n
                odom.pose.pose.position.z += p.z * inv_n
                odom.pose.pose.orientation.x += o.x * inv_n
                odom.pose.pose.orientation.y += o.y * inv_n
                odom.pose.pose.orientation.z += o.z * inv_n
                odom.pose.pose.orientation.w += o.w * inv_n
                odom.twist.twist.linear.x += tw.linear.x * inv_n
                odom.twist.twist.angular.z += tw.angular.z * inv_n

            q = odom.pose.pose.orientation
            norm = math.sqrt(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w) or 1.0
            q.x /= norm
            q.y /= norm
            q.z /= norm
            q.w /= norm
            pos = odom.pose.pose.position

        self.odom_pub.publish(odom)

        if self.publish_tf:
            t = TransformStamped(header=odom.header, child_frame_id=odom.child_frame_id)
            t.transform.translation.x = pos.x
            t.transform.translation.y = pos.y
            t.transform.translation.z = pos.z
            t.transform.rotation = q
            self.tf_broadcaster.sendTransform(t)


def main(args=None):
    """Execute the OdomTFBroadcaster node."""
    rclpy.init(args=args)
    node = OdomTFBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
