import signal

from geometry_msgs.msg import Twist, TwistStamped
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class TwistBridge(Node):
    """Bridge unstamped Twist to stamped TwistStamped messages for Gen5 hardware."""

    def __init__(self):
        super().__init__('twist_to_stamped_bridge')
        self.declare_parameter('input_topic', '/cmd_vel')
        self.declare_parameter('output_topic', '/ubiquity_velocity_controller/cmd_vel')
        self.declare_parameter('frame_id', 'base_link')

        in_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        out_topic = self.get_parameter('output_topic').get_parameter_value().string_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value

        self.sub = self.create_subscription(Twist, in_topic, self.cmd_vel_callback, 10)
        self.pub = self.create_publisher(TwistStamped, out_topic, 10)

    def cmd_vel_callback(self, msg: Twist):
        """Timestamp and republish incoming Twist command."""
        stamped = TwistStamped()
        stamped.header.stamp = self.get_clock().now().to_msg()
        stamped.header.frame_id = self.frame_id
        stamped.twist = msg
        self.pub.publish(stamped)


def main(args=None):
    """Execute the TwistBridge node."""
    rclpy.init(args=args)
    node = TwistBridge()
    stop_requested = False

    def _on_signal(_signum, _frame):
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    try:
        while rclpy.ok() and not stop_requested:
            rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
