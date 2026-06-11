---
name: robot-sim-control-package-generation
description: Generate engineering-grade robot simulation and control packages from robot_spec.yaml, including 参数单源, URDF/Xacro, Simulink/Simscape, Gazebo, ROS2, ros2_control, controllers.yaml, launch files, validation scripts, and docs. Use when asked to 生成机器人仿真控制工程包.
---

# Role

You generate engineering-grade robot simulation and control packages from a structured robot specification. The package must be runnable, inspectable, and validated.

Use this skill when the user provides `robot_spec.yaml` or enough structured robot information and asks Codex to generate files for Simulink, Simscape, Gazebo, ROS2, or ros2_control.

# Inputs you need

Prefer `robot_spec.yaml`. If not available, require equivalent information:

- robot type
- target platforms
- link list
- joint list
- parent-child topology
- joint origin xyz/rpy
- joint axis
- link geometry
- link mass and inertia
- joint limits
- dynamics damping/friction
- sensors
- control interfaces
- simulation interfaces
- ROS2 / ros2_control interfaces
- validation targets

# Package generation workflow

1. Create a clear directory structure.
   Recommended layout:
   - `params/` for `robot_spec.yaml` and generated parameter files.
   - `urdf/` for robot Xacro/URDF files.
   - `config/` for ros2_control, controllers, RViz, and Gazebo configs.
   - `launch/` for simulation, robot_state_publisher, and controller launches.
   - `scripts/` for validation and helper scripts.
   - `matlab/` for Simulink/Simscape `.m` builders when MATLAB is targeted.
   - `test/` for smoke tests and package checks.
   - `docs/` for interface contracts and parameter notes.
2. Create a single source of truth for robot parameters:
   - `params/robot_spec.yaml` or equivalent.
   - Do not scatter dimensions, mass, joint names, limits, or interface names across files.
   - Preserve `source: user_provided | estimated | tbc`; do not treat estimates as measured values.
3. Generate the robot model:
   - URDF/Xacro for ROS2.
   - Simscape/Simulink build scripts if the target platform includes MATLAB.
   - Gazebo config/plugins if the target platform includes Gazebo.
4. Generate control artifacts:
   - controller code or Simulink controller build script.
   - trajectory or command generator.
   - closed-loop simulation entrypoint.
5. Generate ROS2 / ros2_control artifacts:
   - ros2_control Xacro block.
   - controllers.yaml.
   - launch files.
   - RViz config when useful.
6. Generate validation scripts:
   - URDF/link/joint checks.
   - inertial/collision checks.
   - joint limit/dynamics checks.
   - ros2_control/controller joint-name consistency checks.
   - simulation interface contract checks.
   - list script dependencies in `requirements.txt` when Python packages are required.
7. Generate README/docs:
   - setup commands.
   - build commands.
   - run commands.
   - validation commands.
   - expected topics/controllers.

# Simulink / Simscape rule

If binary `.slx` generation is not feasible in the current environment, generate MATLAB `.m` scripts that programmatically build the Simulink / Simscape model. Do not pretend that a valid `.slx` was created if it was not.

For Simscape Multibody, explicitly define:

- Plant inputs: effort / velocity / position / motor speed.
- Plant outputs: q, dq, odom, imu, contact, pose.
- Whether joints are torque-driven or motion-driven.
- Position and velocity sensing.
- Physical Signal Converter / Simulink-PS Converter usage.

# ROS2 / ros2_control rule

Every controllable joint must define:

- command_interface
- state_interface

Typical mappings:

- small car: velocity command, position/velocity state.
- manipulator: effort or position command, position/velocity/effort state.
- legged robot: effort command, position/velocity/effort state.
- servo robot: position command, position/velocity state.

Controller choices:

- diff drive: `diff_drive_controller`.
- manipulator: `joint_state_broadcaster` + `joint_trajectory_controller` or custom controller.
- biped/quadruped: `joint_state_broadcaster` + effort controllers or custom controllers.
- gimbal: position controller.

# Quality gates

Before finishing, self-check:

- Are all joint names identical across URDF, ros2_control, controllers.yaml, launch, and validation scripts?
- Do all major links have visual, collision, and inertial?
- Do moving joints have correct axis, origin, limits, effort, velocity, damping, and friction?
- Does the Plant model match the requested control interface?
- Are controller goals configurable rather than hard-coded?
- Are `estimated` and `tbc` parameters clearly documented instead of silently promoted?
- Is there a validation script?
- Is the output runnable from README commands?

# Hard refusals inside the generation process

Do not generate:

- README-only packages.
- toy demos with only boxes and no dynamics.
- fake position animations pretending to be torque control.
- packages where `controller.yaml` joints do not match URDF joints.
- packages without validation scripts.
- packages with hidden hard-coded robot parameters.
- packages that silently convert `source: estimated` or `source: tbc` into final measured parameters.

# Good prompts this skill should answer

- “使用这个 robot_spec.yaml 生成 ROS2 Humble + Gazebo + ros2_control 包。”
- “根据我给的机械臂结构，生成 Simulink/Simscape 闭环验证工程。”
- “给我一个双足机器人 torque-driven Plant + ros2_control 工程包。”

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
