# Ubiquity Core Utils (`ubiquity_core_utils`)

This package contains essential utility nodes and scripts that bridge the gap between low-level hardware firmware and the high-level ROS 2 navigation stack for Ubiquity Magni robots. It specifically handles architectural differences between Gen 5 and Gen 6 hardware.

## Core Nodes

### 1. `odom_tf_broadcaster` (Gen 6 Specific)

**Purpose:** Synchronizes and stamps raw odometry data from the Motor Controller Board (MCB) and broadcasts it to the ROS 2 system.

**Why it is needed:**
On Gen 6 robots, motor control and odometry calculations are handled directly by the low-level firmware on the MCB, bypassing the `ubiquity_motor_ros2` node used in older generations. 
*   **The Problem:** The firmware on the MCB does not have a Real-Time Clock (RTC) synchronized with the Ubuntu OS on the Raspberry Pi. Therefore, the raw odometry data it sends over serial (to `/mcb/odometry`) has no ROS 2 timestamps (`header.stamp`). Without timestamps, SLAM and navigation algorithms (like `iris_lama`) cannot function because they cannot synchronize laser scans with robot movement.
*   **The Solution:** The `odom_tf_broadcaster` subscribes to the raw, unstamped `/mcb/odometry` topic. The millisecond a message arrives, it grabs the highly accurate system time from the Ubuntu OS, applies it to the message, and republishes it as a fully compliant `nav_msgs/Odometry` message to `/odom`.
*   **TF Broadcasting:** Simultaneously, it calculates and broadcasts the official `odom` -> `base_link` coordinate transform to the `/tf` tree, establishing the robot's root position in the world.

### 2. `twist_bridge` (Gen 5 Specific)

**Purpose:** Bridges standard `geometry_msgs/Twist` commands to `geometry_msgs/TwistStamped` (or vice versa depending on legacy requirements).

**Why it is needed:**
Gen 5 robots rely heavily on the `ubiquity_motor_ros2` node for motor control. Depending on the exact configuration and legacy firmware versions, there is often a mismatch between the standard unstamped velocity commands (`/cmd_vel`) expected by standard ROS 2 navigation packages and the specific format required by the older motor controllers. This node acts as a transparent translation layer, ensuring velocity commands are properly formatted and routed to the hardware without requiring modifications to standard autonomy packages.

## Launch Architecture

The `ubiquity_core_utils.launch.py` file is conditionally driven by the robot's hardware generation (defined in `/etc/ubiquity/robot.yaml`).

*   **If `generation == 'gen6'`**: Launches `odom_tf_broadcaster` to handle raw firmware odometry.
*   **If `generation == 'gen5'`**: Launches `twist_bridge` to handle legacy velocity command translation.

This ensures that the robot's "brain" receives standardized, correctly formatted data regardless of which generation of "body" it is attached to.