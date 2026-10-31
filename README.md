# Ubiquity Core Utils (`ubiquity_core_utils`)

Essential hardware utility nodes and launch logic bridging low-level MCB firmware to the high-level ROS 2 navigation and visualization stack for Ubiquity Magni robots.

## Architectural Purpose

This package bridges architectural differences across hardware generations (Gen 5 vs. Gen 6) and multi-MCB platforms (e.g. 4WD):

1. **Firmware Clock Decoupling (Gen 6):**
   The STM32 MCB firmware lacks an RTC synchronized with Ubuntu. Odometry and battery messages arriving over serial or micro-ROS/Pico-ROS lack system timestamps. `ubiquity_core_utils` injects accurate Ubuntu OS timestamps (`now()`), publishes compliant `/odom`, and broadcasts the `odom -> base_link` TF transform needed by SLAM (`iris_lama`, `cartographer`) and Nav2.
2. **Velocity Command Translation (Gen 5):**
   Translates standard unstamped velocity commands (`/cmd_vel`) into time-synchronized `geometry_msgs/TwistStamped` commands on `/ubiquity_velocity_controller/cmd_vel` required by the `ubiquity_motor_ros2` hardware controller.
3. **Battery Telemetry Standardization (Foxglove & Web Dashboard):**
   Translates raw MCB battery states (`/mcb/battery_state`) to the standard ROS 2 `/battery_state` topic, normalizing raw charge percentages to the standard `0.0..1.0` range and populating timestamps.
4. **Multi-MCB Odometry Aggregation:**
   Dynamically discovers and aggregates odometry streams across single or multi-controller configurations (e.g., dual-MCB 4WD platforms) with built-in staleness detection and single-node fast-path execution.

---

## Nodes

### 1. `odom_tf_broadcaster`

Subscribes to raw MCB telemetry, stamps it with ROS 2 system time, normalizes telemetry, and broadcasts transforms.

* **Subscribed Topics:**
  * `mcb/odometry` (`nav_msgs/msg/Odometry`) - discovered dynamically or by pattern.
  * `/mcb/battery_state` (`sensor_msgs/msg/BatteryState`) - raw MCB battery state.
* **Published Topics:**
  * `/odom` (`nav_msgs/msg/Odometry`) - stamped, standardized odometry.
  * `/battery_state` (`sensor_msgs/msg/BatteryState`) - normalized battery telemetry.
  * `/tf` (`tf2_msgs/msg/TFMessage`) - `odom -> base_link` dynamic transform.
* **Key Parameters:**
  * `odom_frame_id` (str, default: `'odom'`): Coordinate frame for odometry origin.
  * `base_frame_id` (str, default: `'base_link'`): Coordinate frame for robot chassis.
  * `publish_rate_hz` (double, default: `20.0`): Publishing frequency for odometry and TF.
  * `stale_timeout_sec` (double, default: `1.0`): Timeout after which unresponsive MCB streams are dropped.
  * `publish_tf` (bool, default: `True`): Whether to broadcast the `odom -> base_link` transform.

### 2. `twist_bridge`

Bridges unstamped `geometry_msgs/Twist` into `geometry_msgs/TwistStamped` with current timestamps and frame metadata.

* **Subscribed Topics:**
  * `/cmd_vel` (`geometry_msgs/msg/Twist`)
* **Published Topics:**
  * `/ubiquity_velocity_controller/cmd_vel` (`geometry_msgs/msg/TwistStamped`)
* **Key Parameters:**
  * `input_topic` (str, default: `'/cmd_vel'`): Unstamped velocity topic.
  * `output_topic` (str, default: `'/ubiquity_velocity_controller/cmd_vel'`): Target stamped velocity topic.
  * `frame_id` (str, default: `'base_link'`): Frame ID injected into TwistStamped header.

---

## Launch Architecture

Launch conditionally switches components based on the robot hardware generation:

```bash
ros2 launch ubiquity_core_utils ubiquity_core_utils.launch.py generation:=gen6
```

* **`generation == 'gen6'`**: Launches `odom_tf_broadcaster` (handles raw firmware odometry, TF tree, and battery telemetry).
* **`generation == 'gen5'`**: Launches `twist_bridge` (handles legacy command velocity translation to `ubiquity_motor_ros2`).

Legacy compatibility launch file `launch/ubiquity_core.launch.py` is preserved and forwards directly to `ubiquity_core_utils.launch.py`.
