import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped
from builtin_interfaces.msg import Time

class TwistBridge(Node):
    def __init__(self):
        super().__init__('twist_to_stamped_bridge')
        self.sub = self.create_subscription(Twist, '/cmd_vel', self.cb, 10)
        self.pub = self.create_publisher(TwistStamped, '/ubiquity_velocity_controller/cmd_vel', 10)

    def cb(self, msg: Twist):
        stamped = TwistStamped()
        stamped.header.stamp = self.get_clock().now().to_msg()
        stamped.twist = msg
        self.pub.publish(stamped)


def main(args=None):
	rclpy.init(args=args)
	node = TwistBridge()

	try:
		rclpy.spin(node)  # Spin the node to handle callbacks (e.g., the Timer)
	except KeyboardInterrupt:
		node.get_logger().info("Script interrupted by user.")
	finally:
		node.destroy_node()  # Cleanup the node
		rclpy.shutdown()     # Shut	down rclpy

if __name__ == "__main__":
	main()

