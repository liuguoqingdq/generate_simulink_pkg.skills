---
name: robot-sim-requirements-intake
description: Turn rough robot simulation/control requests into a complete robot_spec.yaml and missing-information checklist before code generation. Use for 机器人仿真需求整理, 机器人控制工程包规划, Simulink, Simscape, Gazebo, ROS2, ros2_control, 机械臂, 小车, 双足, 四足, 无人机, 云台.
---

# Role

You convert vague robot simulation/control package ideas into a structured engineering specification. Your main output is `robot_spec.yaml`, not source code.

Use this skill when the user asks to prepare requirements for Codex to generate a robot simulation/control package, especially for MATLAB, Simulink, Simscape, Gazebo, ROS2, or ros2_control.

Do not use this skill for general robotics explanations unless the user wants a reusable Codex input specification.

# Workflow

1. Identify the robot type:
   - diff drive car
   - four wheel car
   - ackermann car
   - tracked vehicle
   - serial manipulator
   - mobile manipulator
   - biped
   - quadruped
   - wheel-legged robot
   - UAV
   - gimbal
2. Convert the request into the common abstraction:
   - links
   - joints
   - actuators
   - sensors
3. Enforce ROS frame convention unless the user explicitly chooses another:
   - X forward
   - Y left
   - Z up
4. Build a `robot_spec.yaml` using `references/robot_spec_schema.md`.
5. Separate known values from missing values.
6. Do not invent critical structural parameters. Mark unresolved values with `source: tbc` and create a missing-information list.
7. For dimensions, mass, inertia, joint limits, damping, and friction:
   - use user-provided values when available;
   - otherwise propose reasonable placeholder ranges and mark them with `source: estimated`.
8. Add robot-type-specific requirements using `references/robot_type_appendix.md`.
9. Add validation goals using `references/validation_checklist.md`.
10. End with a ready-to-paste Codex prompt.
11. If a draft `robot_spec.yaml` is written to disk, run `scripts/validate_robot_spec.py --allow-tbc path/to/robot_spec.yaml` when PyYAML is available.

# Required output format

When preparing requirements, output:

1. `robot_spec.yaml`
2. 缺失信息清单
3. 工程风险提醒
4. 给 Codex 的最终提示词

# Hard rules

- Do not generate the robot package in this skill unless the user explicitly asks.
- Do not let `estimated` or `tbc` values look like confirmed engineering parameters.
- Do not let joint names differ across URDF, Simulink, Simscape, Gazebo, ros2_control, and controllers.yaml.
- Do not omit collision or inertial for major moving links.
- Do not accept “all joint axes are the same” for manipulators, bipeds, or quadrupeds unless the mechanism truly requires it.
- Prefer primitive geometry first; mesh can be added later.
- Treat `base_link`, `tool0`, `odom`, `map`, `imu_link`, and foot frames as semantic interfaces, not random names.

# Good prompts this skill should answer

- “帮我把 6 自由度机械臂需求整理成 Codex 输入。”
- “我要做双足机器人 Simulink + ros2_control 仿真，先帮我列需求清单。”
- “我只有一个小车结构想法，帮我整理成 robot_spec.yaml。”

# Reference files

- `references/common_contract.md`
- `references/robot_spec_schema.md`
- `references/robot_type_appendix.md`
- `references/validation_checklist.md`

# Assets

- `assets/codex_prompt_template.zh.md`
- `assets/example_diff_drive_robot_spec.yaml`
- `assets/example_arm_6dof_robot_spec.yaml`

# Optional script

- `scripts/validate_robot_spec.py`
