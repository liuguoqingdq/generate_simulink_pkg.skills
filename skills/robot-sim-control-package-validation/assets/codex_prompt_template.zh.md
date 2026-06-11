# Codex 通用调用模板

请使用机器人仿真与控制工程化规范，生成一个可验证的工程包，不要玩具 demo。

机器人类型：
[差速小车 / 四轮小车 / 阿克曼小车 / 机械臂 / 双足机器人 / 四足机器人 / 移动机械臂 / 无人机 / 云台]

目标平台：
- ROS2 版本：[Humble / Jazzy / ...]
- Ubuntu 版本：[22.04 / 24.04 / ...]
- 仿真平台：[Simulink / Simscape / Gazebo / MuJoCo / Isaac Sim]
- 控制器平台：[Simulink / C++ ros2_control / Python 原型]

机器人结构：
- links：
  - [name, role, geometry, mass, inertial]
- joints：
  - [name, type, parent, child, origin_xyz, origin_rpy, axis, limit, dynamics]
- sensors：
  - [name, parent, origin, topic, update_rate, noise]

控制接口：
- command_interface：[position / velocity / effort]
- state_interface：[position / velocity / effort / imu / odom / contact]
- 控制器类型：[PD / PID / diff_drive / joint_trajectory / MPC / custom]
- 控制频率：[例如 500 Hz]
- 输入命令：[列出]
- 输出命令：[列出]

仿真要求：
- Plant 输入：[effort / velocity / position / motor speed]
- Plant 输出：[q/dq / odom / imu / contact / pose]
- 必须是动力学仿真，不是动画模型。
- 必须包含 collision 和 inertial。

ROS2 / ros2_control：
- 生成 ros2_control xacro。
- 生成 controllers.yaml。
- 生成 launch 文件。
- 生成 RViz 配置。
- joint names 必须与 URDF 完全一致。

验证要求：
- 生成 validate 脚本。
- 检查 link/joint 是否完整。
- 检查 inertial/collision/limit/dynamics 是否完整。
- 检查接口命名是否一致。
- 检查仿真模型是否为动力学模型。

禁止事项：
- 不要生成玩具 demo。
- 不要只生成 README。
- 不要把参数硬编码散落在多个文件。
- 不要漏 inertial/collision。
- 不要让 joint axis 全部一样，除非结构确实如此。
- 不要让控制器目标写死。
- 不要让仿真只做位置动画。
