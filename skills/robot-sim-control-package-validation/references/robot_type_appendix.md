# 不同机器人类型的额外输入

## 差速小车

必须补充：

- wheel_radius
- wheel_width
- wheel_separation
- chassis_length / chassis_width / chassis_height
- left_wheel_joint / right_wheel_joint
- wheel axis
- cmd_vel 接口
- odom 输出
- 是否需要 LiDAR / Camera
- 是否使用 diff_drive_controller

关键约束：左右轮对称，轮子 axis 正确，base_link 到 wheel 的 origin 正确。

## 四轮小车 / 阿克曼车

必须补充：

- front_left_wheel / front_right_wheel / rear_left_wheel / rear_right_wheel
- wheelbase
- track_width
- wheel_radius
- 驱动方式：四驱 / 后驱 / 前驱
- 转向方式：差速 / 阿克曼 / 全向

阿克曼还要提供：

- front_left_steering_joint
- front_right_steering_joint
- rear wheel drive joints
- steering limit
- steering geometry

## 履带车

必须补充：

- left_track_link / right_track_link
- track_width
- track_contact_length
- sprocket_radius
- 驱动方式：左右履带速度 / 左右 sprocket velocity / effort
- cmd_vel 到左右履带速度的映射
- 地面接触和摩擦参数
- odom 输出

关键约束：左右履带对称，接触模型不要只用视觉 mesh，履带速度方向和 base_link 坐标系一致。

## 机械臂

必须补充：

- 自由度
- 关节轴序列
- link 长度
- tool0 位置
- 关节限位
- effort limit
- velocity limit
- 是否使用 joint_trajectory_controller
- 是否使用 MoveIt2

关键约束：joint axis 不要全部相同，tool0 必须存在，每个 revolute joint 必须有 limit。

## 双足机器人

必须补充：

- pelvis_link / torso_link
- left_leg links / right_leg links
- hip yaw / roll / pitch joints
- knee pitch joint
- ankle pitch / roll joints
- foot_link
- 左右腿对称关系
- 腿长
- 脚底尺寸
- 质心高度
- IMU 安装位置
- foot contact sensor
- stand posture
- walking gait primitive

关键约束：左右腿对称，foot_link 有 collision，必须有 IMU，最好有 contact sensor，腿部 joint limit 合理。

## 四足机器人

必须补充：

- body_link
- front_left_leg / front_right_leg / rear_left_leg / rear_right_leg
- hip joints
- thigh links
- shank links
- foot links
- 每条腿的安装位置
- 步态：walk / trot / bound
- foot contact sensor
- IMU
- body velocity command

关键约束：四条腿结构镜像对称，foot collision 必须存在，每条腿 joint axis 正确。

## 轮腿机器人

必须补充：

- body_link
- left_leg / right_leg 或四条腿结构
- wheel_link 与 wheel_joint
- hip / knee / ankle 或等效腿部 joints
- 轮子半径、轮距、腿长、足端或轮端接触模型
- body velocity command
- wheel velocity / leg effort 的混合控制接口
- IMU 和 wheel odom
- 站立高度、蹲起范围、轮地接触约束

关键约束：轮子 joint axis 与左右镜像关系必须明确，腿部 effort/position 控制和轮速控制不能混成同一个未定义接口。

## 移动机械臂

必须补充：

- mobile_base 部分
- arm 部分
- base_link 到 arm_base_link 的 fixed transform
- 底盘控制接口
- 机械臂控制接口
- 是否同时生成 Nav2 和 MoveIt2 配置

关键约束：移动底盘和机械臂必须通过 fixed joint 连接，base_link / arm_base_link / tool0 命名清楚。

## 无人机

必须补充：

- base_link / body_link
- motor links 和 propeller links
- 机臂长度、机身尺寸、质量分布、惯量矩阵
- rotor 安装位置、旋向、thrust coefficient、torque coefficient
- motor speed 或 thrust command 接口
- IMU、pose、velocity、angular velocity feedback
- 控制器：姿态 PID / 位置 PID / cascaded controller
- 是否需要 Gazebo / Simscape / PX4 接口

关键约束：惯量矩阵和电机旋向不能省略，Plant 输入必须明确是 motor speed、thrust 还是 wrench。

## 云台

必须补充：

- base_link
- yaw_link / pitch_link / roll_link
- camera_link 或 payload_link
- yaw / pitch / roll joint axis
- 每个轴的 limit、velocity limit、effort limit
- command_interface：position 或 velocity
- state_interface：position、velocity，可选 effort
- 控制器：position PID / velocity PID
- 负载质量、质心和惯量

关键约束：轴向顺序必须明确，camera optical frame 与 ROS optical frame 约定不能混淆。
