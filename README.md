# Testbed-T1.0.0 — ROS 2 Navigation Assignment

## Overview

This repository contains the implementation of the Level 1 ROS 2 Navigation assignment for the ERIC Robotics Testbed-T1.0.0 robot.

The objective of this assignment is to develop a modular ROS 2 navigation package named `testbed_navigation` and manually configure the required Nav2 components instead of relying on the complete `nav2_bringup` launch system.

The final system allows the Testbed robot to:

* Load a predefined map.
* Localize itself on the map using AMCL.
* Build a collision-aware navigation path.
* Plan a path to a user-specified goal.
* Follow the planned path using a local controller.
* Navigate autonomously to the goal.
* Visualize the navigation process using RViz2.

**This has been implemented and verified end-to-end** — the robot successfully reached multiple navigation goals in simulation (see Section 20).

---

# 1. Environment

The original assignment targets ROS 2 Humble with Gazebo Classic.

Because ROS 2 Jazzy uses a newer Gazebo environment, the assignment is executed inside a Docker container using ROS 2 Humble.

### Environment

* Ubuntu host (ROS 2 Jazzy installed natively)
* Docker (container: `ros_humble_assignment`, image: `ros:humble-ros-base`)
* ROS 2 Humble
* Gazebo Classic
* RViz2
* Nav2
* CMake
* Python 3
* Git

The workspace is mounted/shared with the host so that source files remain accessible outside the Docker container — edits made in either the host filesystem or inside the container affect the same underlying files.

```text
Ubuntu host (Jazzy)
   |
   v
Docker container (ros_humble_assignment)
   |
   v
ROS 2 Humble -> Gazebo Classic -> Nav2
```

GUI passthrough (RViz2, Gazebo client) requires X11 forwarding:

```bash
xhost +local:docker
```

run once per host login session, with the `DISPLAY` environment variable matching between host and container.

---

# 2. Repository Structure

```text
level01_ros_assignment/
│
├── bugs_found.txt
├── help.md
├── README.md
│
├── testbed_bringup/
│   ├── CMakeLists.txt
│   ├── package.xml
│   ├── launch/
│   │   └── testbed_full_bringup.launch.py
│   └── maps/
│       ├── testbed_world.pgm
│       └── testbed_world.yaml
│
├── testbed_description/
│   ├── CMakeLists.txt
│   ├── package.xml
│   ├── launch/
│   │   ├── robot_description.launch.py
│   │   └── testbed_rviz_barebones.launch.py
│   ├── meshes/
│   ├── rviz/
│   └── urdf/
│       ├── materials.xacro
│       ├── testbed.gazebo
│       ├── testbed.trans
│       └── testbed.xacro
│
├── testbed_gazebo/
│   ├── CMakeLists.txt
│   ├── package.xml
│   ├── launch/
│   │   ├── spawn_playground.launch.py
│   │   └── spawn_testbed.launch.py
│   ├── models/
│   └── worlds/
│
└── testbed_navigation/
    ├── CMakeLists.txt
    ├── package.xml
    ├── README.md
    ├── config/
    │   ├── amcl_params.yaml
    │   └── nav2_params.yaml
    └── launch/
        ├── map_loader.launch.py
        ├── localization.launch.py
        └── navigation.launch.py
```

---

# 3. Robot and Simulation

The provided Testbed-T1.0.0 is a differential-drive mobile robot.

The robot description is provided through the `testbed_description` package. The Gazebo simulation is provided through the `testbed_gazebo` package. The main robot bringup is provided through:

```text
testbed_bringup/launch/testbed_full_bringup.launch.py
```

**Confirmed TF tree (via `ros2 run tf2_tools view_frames`):**

```text
map (published by amcl, once localized)
 └─ odom (published by diff_drive_control)
     └─ base_footprint
         └─ base_link
             ├─ left_wheel_1, right_wheel_1   (driven wheels)
             ├─ caster_1 .. caster_4          (passive casters)
             ├─ dummy_link_1
             ├─ imu_link_1
             └─ lidar_link_1                  (laser frame)
```

**Confirmed topics and types (via `ros2 topic info`):**

| Topic                 | Type                                        | Publisher                |
|------------------------|----------------------------------------------|-----------------------------|
| `/scan`                | `sensor_msgs/LaserScan`                      | `my_ray_sensor_plugin`      |
| `/odom`                | `nav_msgs/Odometry`                          | `diff_drive_control`        |
| `/cmd_vel`             | `geometry_msgs/Twist`                        | consumed by `diff_drive_control` |
| `/imu`                 | `sensor_msgs/Imu`                            | `my_imu_plugin`             |
| `/robot_description`   | `std_msgs/String`                            | `robot_state_publisher`     |
| `/map`                 | `nav_msgs/OccupancyGrid`                     | `map_server`                |
| `/amcl_pose`           | `geometry_msgs/PoseWithCovarianceStamped`    | `amcl`                       |

Robot footprint is approximated as a circle, `robot_radius: 0.25` m, based on the caster positions (~0.35 m x 0.36 m bounding box).

The exact topic and frame names were verified against the running simulation with `ros2 topic info`, `ros2 topic echo /tf --once`, and `ros2 run tf2_tools view_frames` before writing any Nav2 configuration.

---

# 4. Running the Simulation

Enter the assignment workspace and build:

```bash
cd ~/assignment_ws
source /opt/ros/humble/setup.bash
rm -rf build install log
colcon build --symlink-install
source install/setup.bash
```

Launch the complete Testbed simulation:

```bash
ros2 launch testbed_bringup testbed_full_bringup.launch.py
```

This starts the Gazebo simulation, robot, robot description components, and RViz.

---

# 5. Bugs Identified and Fixed

Five bugs were identified and fixed in the starter repository. Full details are documented in `bugs_found.txt`.

## Bug 1 — Missing parentheses in `ament_package`

File: `testbed_description/CMakeLists.txt`

**Problem:** `ament_package` was not called as a CMake function.

**Fix:**
```cmake
ament_package()
```

---

## Bug 2 — Incorrect map image filename

File: `testbed_bringup/maps/testbed_world.yaml`

**Problem:** The map YAML referenced an incorrect PGM filename that did not match the actual file present (`testbed_world.pgm`).

**Fix:** Updated the YAML's `image` field to reference `testbed_world.pgm`.

---

## Bug 3 — Malformed Gazebo XML

File: `testbed_description/urdf/testbed.gazebo`

**Problem:** A stray `>` character after the IMU sensor's closing tag produced malformed XML.

**Fix:** Removed the stray character to restore valid XML.

---

## Bug 4 — Insufficient LiDAR range

File: `testbed_description/urdf/testbed.gazebo`

**Problem:** LiDAR maximum range was configured to ~1.5 m, too short for practical navigation and obstacle detection.

**Fix:** Increased maximum LiDAR range to 10 m.

---

## Bug 5 — `maps/` directory not installed by `testbed_bringup`

File: `testbed_bringup/CMakeLists.txt`

**Problem:** The package's `install(DIRECTORY ...)` rule only installed the `launch/` directory. The `maps/` directory (containing `testbed_world.yaml` and `testbed_world.pgm`) was never copied to the package's `share/` folder on build. As a result, any node using `get_package_share_directory('testbed_bringup')` to locate the map — as `testbed_navigation`'s `map_loader.launch.py` does — would fail to find it at runtime, even though the files exist in the source tree.

This bug was discovered while building `map_loader.launch.py`, which needed to reference the map file via the package's installed share directory.

**Fix:** Added `maps` to the installed directories list:

```cmake
install(
  DIRECTORY
    launch
    maps
  DESTINATION
    share/${PROJECT_NAME}/
)
```

---

## Environment Dependency Issue — Xacro (not counted as a bug)

The Docker environment initially did not contain `ros-humble-xacro`, causing a launch failure. This was an environment/dependency issue rather than an intentional bug in the starter repository, and was resolved by installing the package.

---

# 6. Navigation Architecture

Instead of launching the complete navigation stack using `ros2 launch nav2_bringup bringup_launch.py`, the required components are launched and configured directly, as three modular stages:

```text
                         MAP
                          │
                          ▼
                    ┌───────────┐
                    │map_server │
                    └─────┬─────┘
                          │
                         /map
                          │
                          ▼
                    ┌───────────┐
                    │   AMCL    │
                    └─────┬─────┘
                          │
                    map → odom
                          │
                          ▼
                       ROBOT
                          │
             ┌────────────┴────────────┐
             │                         │
           /scan                     /odom
             │                         │
             └────────────┬────────────┘
                          │
                          ▼
                    Nav2 Costmaps
                          │
                          ▼
                    BT Navigator
                          │
                 ┌────────┴────────┐
                 │                 │
                 ▼                 ▼
             Planner           Controller
                 │                 │
                 │              /cmd_vel
                 │                 │
                 └────────┬────────┘
                          ▼
                       ROBOT
                          │
                          ▼
                         GOAL
```

---

# 7. `testbed_navigation` Package

The navigation package contains all navigation-specific configuration and launch files, divided into `config/` and `launch/`. This keeps the system modular and makes individual components easier to test and debug independently.

---

# 8. Map Loading

The provided map is `testbed_bringup/maps/testbed_world.yaml`, loaded using the Nav2 map server via `testbed_navigation/launch/map_loader.launch.py`.

```text
testbed_world.yaml
        │
        ▼
    map_server
        │
        ▼
       /map
        │
        ▼
       RViz
```

`map_server` is a lifecycle node and is configured/activated automatically by a dedicated `nav2_lifecycle_manager` (`autostart: True`).

**Run:**
```bash
ros2 launch testbed_navigation map_loader.launch.py
```

**Verified:** `/map` publishes as `nav_msgs/OccupancyGrid`, 405 x 400 cells @ 0.05 m/cell, `frame_id: map`, visible correctly in RViz2.

---

# 9. Localization

Localization is implemented using the Nav2 AMCL package.

Configuration: `testbed_navigation/config/amcl_params.yaml`
Launch file: `testbed_navigation/launch/localization.launch.py`

Key parameters:
* `base_frame_id: base_footprint`, `odom_frame_id: odom`, `global_frame_id: map`
* `scan_topic: scan`, `laser_max_range: 10.0`
* `set_initial_pose: false` — initial pose is supplied manually via RViz2's "2D Pose Estimate" tool rather than hardcoded, so particle cloud convergence can be observed and verified interactively.

```text
              /map
                │
                ▼
               AMCL
          ┌─────┴─────┐
          │           │
       /scan        /odom
          │           │
          └─────┬─────┘
                │
                ▼
           Robot Pose
```

AMCL publishes the `map → odom` transform once given a valid initial pose. The final TF chain:

```text
map
 │
 ▼
odom
 │
 ▼
base_footprint / base_link
 │
 ├── wheels
 ├── lidar
 └── imu
```

**Run:**
```bash
ros2 launch testbed_navigation localization.launch.py
```

**Important:** In RViz2, Fixed Frame must be set to `map` **before** clicking "2D Pose Estimate" — RViz publishes the pose estimate in whichever frame is currently set as Fixed Frame, and AMCL rejects any pose not published in the `map` frame (see Section 19).

**Verified:** `/amcl_pose` publishes a valid pose with reasonable covariance; `map → odom` transform confirmed stable via `ros2 run tf2_ros tf2_echo map odom`.

---

# 10. Navigation

Configuration: `testbed_navigation/config/nav2_params.yaml`
Launch file: `testbed_navigation/launch/navigation.launch.py`

The navigation stack is composed manually from the required Nav2 servers:

```text
controller_server
planner_server
bt_navigator
behavior_server
local_costmap   (instantiated inside controller_server)
global_costmap  (instantiated inside planner_server)
lifecycle_manager_navigation
```

`local_costmap` and `global_costmap` are configured as parameter blocks inside `nav2_params.yaml` and instantiated automatically by `controller_server` and `planner_server` respectively, per standard Nav2 architecture — they are not launched as separate standalone nodes.

**Run:**
```bash
ros2 launch testbed_navigation navigation.launch.py
```

**Verified:** All four lifecycle-managed servers (`controller_server`, `planner_server`, `behavior_server`, `bt_navigator`) configured and activated cleanly under `lifecycle_manager_navigation`.

---

# 11. Planner

The planner calculates a global path from the robot's current position to the requested goal, using the current pose, goal pose, and global costmap.

**Implementation used:** `nav2_navfn_planner/NavfnPlanner` (`GridBased` plugin), a basic and reliable choice appropriate for this Level 1 assignment.

```text
START
  │
  │
  ▼
🤖 ──────────────────── 🎯
       Global Path
```

---

# 12. Controller

The controller follows the generated global path, receiving the planned path and robot state and generating velocity commands published to `/cmd_vel`.

**Implementation used:** `dwb_core::DWBLocalPlanner` (`FollowPath` plugin), configured with 7 critics: `RotateToGoal`, `Oscillation`, `BaseObstacle`, `GoalAlign`, `PathAlign`, `PathDist`, `GoalDist`.

```text
Global Path
     │
     ▼
Controller (DWB)
     │
     ▼
 /cmd_vel
     │
     ▼
Robot
```

---

# 13. Costmaps

## Global Costmap

Used for global path planning. Configured with `static_layer` (from `/map`), `obstacle_layer` (from `/scan`), and `inflation_layer`. Frame: `map`.

```text
Static Map
    +
Obstacle Information
    ↓
Global Costmap
    ↓
Global Planner
```

## Local Costmap

Used by the controller for short-range obstacle avoidance. Rolling 3x3 m window, `obstacle_layer` (from `/scan`) + `inflation_layer`. Frame: `odom`.

```text
LiDAR
  ↓
Obstacle Layer
  ↓
Local Costmap
  ↓
Controller
  ↓
cmd_vel
```

---

# 14. Behavior Tree Navigator

The BT Navigator coordinates the navigation process using the default Nav2 behavior tree `navigate_to_pose_w_replanning_and_recovery.xml`.

```text
Navigation Goal
       │
       ▼
BT Navigator
       │
       ├── Compute Path
       │
       ├── Follow Path
       │
       ├── Check Conditions
       │
       └── Recover if necessary
```

Recovery behaviors configured in `behavior_server`: `spin`, `backup`, `wait`.

---

# 15. Lifecycle Management

Several Nav2 components are lifecycle nodes, transitioned through their states by dedicated `nav2_lifecycle_manager` instances (one per stage: map, localization, navigation), each with `autostart: True`.

```text
Unconfigured
     ↓
Inactive
     ↓
Active
```

All navigation components must reach the active state before navigation goals can be processed — confirmed via bond connections logged by each lifecycle manager.

---

# 16. Testing Procedure

Testing was performed incrementally, verifying each stage before proceeding to the next.

## Test 1 — Simulation
```bash
ros2 launch testbed_bringup testbed_full_bringup.launch.py
```
Verified: Gazebo starts, robot spawns, RViz starts, sensors available.

## Test 2 — Topics
```bash
ros2 topic list
ros2 topic info /scan
ros2 topic info /odom
ros2 topic info /cmd_vel
```
Verified all three topics present with correct types before any Nav2 configuration was written.

## Test 3 — TF
```bash
ros2 run tf2_tools view_frames
```
Verified full TF tree from `odom` down to `lidar_link_1` before AMCL; verified `map → odom` after AMCL activation.

## Test 4 — Map Server
```bash
ros2 launch testbed_navigation map_loader.launch.py
```
Verified `/map` topic present and correctly rendered in RViz2.

## Test 5 — Localization
```bash
ros2 launch testbed_navigation localization.launch.py
```
Used "2D Pose Estimate" in RViz2; verified AMCL converged via `/amcl_pose` and stable `map → odom` transform via `tf2_echo`.

## Test 6 — Navigation
```bash
ros2 launch testbed_navigation navigation.launch.py
```
Verified all Nav2 servers active via `ros2 node list` and lifecycle manager logs. Sent multiple "2D Goal Pose" goals in RViz2 and confirmed `"Goal succeeded"` logged by `bt_navigator` for each.

---

# 17. Useful Commands

```bash
# Build workspace
cd ~/assignment_ws
rm -rf build install log
colcon build --symlink-install

# Source workspace
source /opt/ros/humble/setup.bash
source ~/assignment_ws/install/setup.bash

# List nodes / topics
ros2 node list
ros2 topic list

# Check topic information
ros2 topic info /scan
ros2 topic info /odom
ros2 topic info /cmd_vel

# Inspect a topic
ros2 topic echo /scan --once
ros2 topic echo /odom --once

# Inspect TF
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo map odom

# Check AMCL pose
ros2 topic echo /amcl_pose --once
```

---

# 18. Design Philosophy

The implementation intentionally follows a modular architecture. Instead of a single launch file, separate launch files are provided for `map_loader.launch.py`, `localization.launch.py`, and `navigation.launch.py`. This makes it possible to test individual components, debug failures more easily, understand each Nav2 component's purpose, reuse components independently, and follow Nav2's plugin-based architecture.

---

# 19. Challenges Encountered

### ROS 2 Distribution Difference
The development host uses ROS 2 Jazzy, while the assignment targets ROS 2 Humble and Gazebo Classic. Resolved by running the assignment inside a Docker-based ROS 2 Humble environment, with the workspace bind-mounted for persistent file access.

### Docker Environment Setup
The Docker environment initially had a missing `ros-humble-xacro` dependency and Docker permission issues (`permission denied` on `/var/run/docker.sock`, resolved via `sudo` or adding the user to the `docker` group).

### Workspace Build Cache
The workspace initially contained CMake cache information associated with a different filesystem environment. Resolved by removing `build/`, `install/`, and `log/` before rebuilding.

### Container SIGHUP / GUI Passthrough
The Docker container exited unexpectedly (exit code 129 / SIGHUP) after a terminal session closed, killing all running ROS processes (workspace files were unaffected, being on a bind mount). After restarting the container, RViz2 and `gzclient` failed to start with Qt `xcb` platform plugin errors, caused by the host's X11 access control list resetting. Resolved by running `xhost +local:docker` on the host and ensuring `DISPLAY` matched between host and container.

### Missing `maps/` Install Rule
Discovered while building `map_loader.launch.py` — see Bug 5 above.

### AMCL Initial Pose Frame Mismatch
The first several "2D Pose Estimate" clicks in RViz2 were silently rejected by AMCL with `"Ignoring initial pose in frame 'odom'; initial poses must be in the global frame, 'map'"`. Root cause: RViz2 publishes pose estimates in whichever frame is currently set as Fixed Frame, and Fixed Frame was still `odom` (since `map` did not yet exist in the TF tree — a chicken-and-egg situation, as `map` only appears once AMCL successfully publishes a pose). Resolved by manually typing `map` into the Fixed Frame field before sending the pose estimate.

### First Navigation Goal Aborted Before Succeeding
Immediately after Nav2 bring-up, the first goal sent caused `DWBLocalPlanner: No valid trajectories out of 419!`, because the local costmap's rolling window had not yet accumulated enough scan data along the global path. Nav2's built-in recovery (automatic local costmap clearing) resolved this within ~1 second, and the goal succeeded on the third attempt. All subsequent goals succeeded on the first attempt — this demonstrated Nav2's recovery behavior working as intended, rather than indicating a configuration defect.

---

# 20. Current Status

The following has been completed and verified:

* Repository fork and clone.
* Feature branch created.
* Docker environment configured (ROS 2 Humble, Gazebo Classic, Nav2 dependencies).
* Workspace successfully rebuilt.
* Testbed Gazebo simulation, RViz2, and robot spawn verified working.
* Five starter-code bugs identified and fixed (see Section 5 / `bugs_found.txt`).
* `testbed_navigation` package created with `map_loader.launch.py`, `localization.launch.py`, and `navigation.launch.py`.
* Map server verified: `/map` publishing correctly, visible in RViz2.
* AMCL verified: `/amcl_pose` publishing valid pose, `map → odom` transform stable.
* Full navigation stack verified: `controller_server`, `planner_server`, `behavior_server`, `bt_navigator` all active under `lifecycle_manager_navigation`.
* **Multiple autonomous navigation goals successfully reached**, confirmed via `"Goal succeeded"` in `bt_navigator` logs, including recovery from an initial trajectory-planning failure.

**All Level 1 assignment requirements have been implemented and verified end-to-end.**

---

# 21. Final Result Achieved

The completed system provides the following verified workflow:

```text
                  TESTBED NAVIGATION
                         │
                         ▼
                    ┌─────────┐
                    │   MAP   │
                    └────┬────┘
                         │
                         ▼
                    map_server
                         │
                         ▼
                        AMCL
                         │
                    Robot Pose
                         │
                         ▼
                  Global Costmap
                         │
                         ▼
                     Planner (NavFn)
                         │
                    Global Path
                         │
                         ▼
                   Local Costmap
                         │
                         ▼
                    Controller (DWB)
                         │
                      /cmd_vel
                         │
                         ▼
                        🤖
                         │
                         ▼
                        🎯
                    "Goal succeeded"
```

The Testbed-T1.0.0 robot autonomously navigated from its initial position to multiple goals selected in RViz2, with the full manually-assembled Nav2 pipeline — map server, AMCL, planner, controller, and BT navigator — working correctly end to end.

---

# 22. Conclusion

This project demonstrates a modular ROS 2 navigation architecture using Nav2 components individually, rather than relying on the complete `nav2_bringup` workflow. The assignment provided practical experience with:

* ROS 2 package development.
* Launch files and modular architecture.
* YAML parameter configuration.
* TF and coordinate frames.
* Map Server.
* AMCL localization.
* Costmaps (global and local).
* Global planning (NavFn).
* Local control (DWB).
* Behavior Trees.
* Lifecycle nodes and lifecycle management.
* Autonomous robot navigation, verified end-to-end with multiple successful goal completions.
* Gazebo simulation and Docker-based ROS 2 development, including GUI passthrough and container lifecycle management.
* RViz2 visualization.

The implementation avoids relying on the complete `nav2_bringup` workflow and instead builds the required navigation pipeline from individual Nav2 components, providing a clearer understanding of how the ROS 2 navigation stack operates internally — and demonstrating that understanding through successful autonomous navigation in simulation.
