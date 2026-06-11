# 机器人包验证清单

## 通用验证

- URDF / Xacro 文件是否存在。
- 所有 link 是否存在。
- 所有 joint 是否存在。
- parent-child 拓扑是否正确。
- 是否存在重复 child link、断链或拓扑循环。
- moving link 是否有 inertial。
- inertial 是否包含 mass、com_xyz、inertia，且 mass > 0。
- link 是否有 collision。
- joint origin_xyz / origin_rpy 是否存在且是 3 维。
- 非 fixed joint axis 是否存在、非零、近似归一化。
- revolute joint 是否有 lower / upper / effort / velocity。
- continuous joint 是否有 effort / velocity。
- fixed joint 是否没有多余 limit。
- joint axis 是否合理。
- actuator 是否引用已定义 joint。
- sensor 的 parent/link 是否引用已定义 link。
- ros2_control joint names 是否和 URDF 一致。
- ros2_control command/state interfaces 是否和 actuator/control 契约一致。
- controllers.yaml 中 joints 是否和 URDF 一致。
- 仿真模型输入输出是否符合接口契约。
- Plant 是否是动力学模型，而不是单纯位置动画。
- simulation / validation / forbidden 字段是否存在并覆盖关键质量门。
- 关键估计值是否带 `source: estimated`，待确认值是否带 `source: tbc`。

## 小车专项

- 左右轮轴是否对称。
- 轮子 axis 是否正确。
- wheel_separation / wheel_radius 是否存在。
- diff_drive 参数是否存在。
- cmd_vel 到 wheel velocity 的映射是否正确。

## 履带车专项

- 左右履带是否对称。
- 履带接触长度、track_width、sprocket_radius 是否存在。
- cmd_vel 到左右履带速度或 sprocket 命令的映射是否明确。
- 履带接触/摩擦参数是否存在。

## 机械臂专项

- revolute joint 数量是否等于自由度。
- tool0 是否存在。
- 每个 revolute joint limit 是否完整。
- 每个关节 axis 不应全部相同。
- 末端链路是否连续。

## 双足 / 四足专项

- 左右腿或四条腿结构是否对称。
- hip / knee / ankle joint 是否完整。
- foot_link 是否有 collision。
- contact sensor 是否存在。
- IMU 是否存在。
- 腿部 joint limit 是否合理。

## 轮腿机器人专项

- 轮子 joint axis 与腿部 joint axis 是否分别正确。
- wheel velocity 与 leg effort/position 控制接口是否分离。
- 站立高度、轮地接触、IMU、odom 是否存在。

## 无人机专项

- rotor 位置、旋向、thrust coefficient、torque coefficient 是否存在。
- motor speed/thrust/wrench 输入接口是否明确。
- 惯量矩阵、IMU、pose/velocity feedback 是否存在。

## 云台专项

- yaw/pitch/roll 轴顺序和 axis 是否明确。
- camera_link / optical frame 约定是否正确。
- payload mass、COM、inertia 是否存在。
