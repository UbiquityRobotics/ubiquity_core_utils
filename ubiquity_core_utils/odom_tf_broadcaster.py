import rclpy, math
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class OdomTFBroadcaster(Node):
    def __init__(self):
        super().__init__('odom_tf_broadcaster')
        self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.subs, self.msgs = {}, {}
        
        self.create_timer(5.0, self.discover_topics)
        self.discover_topics()
        self.create_timer(0.05, self.publish_avg)

    def discover_topics(self):
        for n, ty in self.get_topic_names_and_types():
            if 'nav_msgs/msg/Odometry' in ty and 'mcb' in n:
                if n not in self.subs:
                    self.get_logger().info(f"Subscribing to {n}")
                    self.subs[n] = self.create_subscription(
                        Odometry, n, lambda m, t=n: self.msgs.update({t: m}), 10
                    )

    def publish_avg(self):
        if not self.msgs: return
        avg = Odometry()
        avg.header.stamp, avg.header.frame_id, avg.child_frame_id = self.get_clock().now().to_msg(), 'odom', 'base_link'
        
        for m in self.msgs.values():
            avg.pose.pose.position.x += m.pose.pose.position.x / len(self.msgs)
            avg.pose.pose.position.y += m.pose.pose.position.y / len(self.msgs)
            avg.pose.pose.orientation.x += m.pose.pose.orientation.x / len(self.msgs)
            avg.pose.pose.orientation.y += m.pose.pose.orientation.y / len(self.msgs)
            avg.pose.pose.orientation.z += m.pose.pose.orientation.z / len(self.msgs)
            avg.pose.pose.orientation.w += m.pose.pose.orientation.w / len(self.msgs)
            avg.twist.twist.linear.x += m.twist.twist.linear.x / len(self.msgs)
            avg.twist.twist.angular.z += m.twist.twist.angular.z / len(self.msgs)
            
        q = avg.pose.pose.orientation
        norm = math.sqrt(q.x**2 + q.y**2 + q.z**2 + q.w**2) or 1.0
        q.x, q.y, q.z, q.w = q.x/norm, q.y/norm, q.z/norm, q.w/norm
        
        self.odom_pub.publish(avg)
        t = TransformStamped(header=avg.header, child_frame_id=avg.child_frame_id)
        t.transform.translation.x, t.transform.translation.y = avg.pose.pose.position.x, avg.pose.pose.position.y
        t.transform.rotation = q
        self.tf_broadcaster.sendTransform(t)

def main():
    rclpy.init()
    rclpy.spin(OdomTFBroadcaster())
    rclpy.shutdown()

