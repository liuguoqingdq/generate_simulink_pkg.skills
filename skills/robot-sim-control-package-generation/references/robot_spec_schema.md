# robot_spec.yaml 参考结构

```yaml
project:
  name: my_robot
  robot_type: arm_6dof        # diff_drive | four_wheel | ackermann | tracked | arm_6dof | biped | quadruped | wheel_legged | mobile_manipulator | uav | gimbal
  goal:
    - control_algorithm_validation
    - ros2_control_deployment
  target_platforms:
    ros2:
      distro: humble
      ubuntu: "22.04"
    simulation:
      - simulink
      - simscape
      - gazebo
    control_runtime:
      - simulink
      - cpp_ros2_control

frames:
  convention: ros
  base_link: base_link
  axes:
    x: forward
    y: left
    z: up
  world_frames:
    odom: odom
    map: map
  end_effector_frame: tool0

links:
  - name: base_link
    role: base_frame
    moving: false
    source: estimated          # user_provided | estimated | tbc
    geometry:
      visual: {type: box, size: [0.20, 0.20, 0.08]}
      collision: {type: box, size: [0.20, 0.20, 0.08]}
    inertial:
      mass: 2.0
      com_xyz: [0.0, 0.0, 0.0]
      inertia: {ixx: auto, ixy: 0.0, ixz: 0.0, iyy: auto, iyz: 0.0, izz: auto}

joints:
  - name: joint1
    type: revolute
    source: user_provided      # user_provided | estimated | tbc
    parent: base_link
    child: link1
    origin_xyz: [0.0, 0.0, 0.08]
    origin_rpy: [0.0, 0.0, 0.0]
    axis: [0.0, 0.0, 1.0]
    limit: {lower: -3.14, upper: 3.14, effort: 80.0, velocity: 2.5}
    dynamics: {damping: 0.5, friction: 0.03}

actuators:
  - name: joint1_motor
    joint: joint1
    source: estimated
    command_interface: effort
    state_interfaces: [position, velocity, effort]
    effort_limit: 80.0
    velocity_limit: 2.5

sensors:
  - name: imu
    link: imu_link
    parent: base_link
    source: estimated
    origin_xyz: [0.0, 0.0, 0.10]
    origin_rpy: [0.0, 0.0, 0.0]
    topic: /imu/data
    update_rate_hz: 200
    noise: simple

control:
  controller_type: joint_space_pd
  control_space: joint_space
  sample_time_s: 0.002
  command_input: joint_trajectory
  feedback: [joint_position, joint_velocity]
  output: effort
  limits:
    enforce_effort: true
    enforce_velocity: true
    enforce_acceleration: true

simulation:
  plant_input: effort
  plant_output: [q, dq, pose]
  dynamic_simulation_required: true
  collision_required: true
  inertial_required: true
  simscape:
    torque_driven: true
    enable_position_sensing: true
    enable_velocity_sensing: true
  gazebo:
    use_gazebo_ros2_control: true
    use_sensor_plugins: true

ros2_control:
  hardware_plugin: gazebo_ros2_control/GazeboSystem
  joints:
    - name: joint1
      command_interfaces: [effort]
      state_interfaces: [position, velocity, effort]
  controllers:
    joint_state_broadcaster: true
    joint_trajectory_controller: true

outputs:
  recommended_layout:
    - params/                 # robot_spec.yaml and generated parameter files
    - urdf/                   # robot.urdf.xacro and included xacro fragments
    - config/                 # ros2_control.xacro, controllers.yaml, RViz, Gazebo config
    - launch/                 # launch files for sim, rsp, controllers
    - scripts/                # validation and helper scripts
    - matlab/                 # Simulink/Simscape .m builders when MATLAB is targeted
    - test/                   # smoke tests and package checks
    - docs/                   # engineering notes and interface contract
  required_files:
    - params/robot_spec.yaml
    - urdf/robot.urdf.xacro
    - config/ros2_control.xacro
    - config/controllers.yaml
    - launch/sim.launch.py
    - scripts/validate_robot_package.py
    - README.md

validation:
  generate_validate_script: true
  check_urdf: true
  check_joint_name_consistency: true
  check_inertial_collision: true
  check_limits_dynamics: true
  check_interface_contract: true

forbidden:
  - toy_demo
  - readme_only
  - hardcoded_scattered_params
  - missing_inertial
  - missing_collision
  - fake_position_animation
```

## Source 标记规则

关键结构、几何、质量、惯量、关节限位、执行器和传感器参数应带 `source`：

- `user_provided`：用户或真实设计文件提供，可以作为工程输入。
- `estimated`：为推进建模给出的估计值，生成包时必须在 README 或 docs 中标记。
- `tbc`：待确认；不应直接进入最终工程生成，除非用户明确接受占位。

如果某个对象内只有部分字段是估计值，可以在对象级用 `source: estimated`，并在 `notes` 中说明哪些字段需要后续替换。
