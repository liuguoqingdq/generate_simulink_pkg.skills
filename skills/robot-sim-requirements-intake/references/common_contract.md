# 机器人仿真与控制工程包通用契约

## 总目标

生成机器人仿真与控制工程包时，不能只生成外观模型或 README，而要生成可验证的工程化包。

Codex 应当要求或使用以下输入：

1. 机器人类型
2. 机器人结构拓扑
3. link / joint / actuator / sensor 命名
4. 坐标系定义
5. 几何尺寸
6. 质量和惯量
7. 关节或轮子的约束
8. 驱动方式
9. 控制接口
10. 仿真接口
11. ROS2 / ros2_control 接口
12. 验证目标
13. 禁止事项

## 核心抽象

所有机器人先抽象成：

```text
link + joint + actuator + sensor
```

- link：刚体部件
- joint：部件之间的连接
- actuator：驱动器
- sensor：传感器

## 命名一致性规则

URDF、Xacro、Simulink、Simscape、Gazebo、ros2_control、controllers.yaml、launch、验证脚本中的 joint name 必须完全一致。

## 动力学规则

所有主要 link 必须包含：

- visual
- collision
- inertial

初期可以不用 mesh，优先使用 primitive。visual 可以更接近真实外观，collision 必须简洁稳定，inertial 必须合理估算。

## 单位规则

- 长度：m
- 角度：rad
- 质量：kg
- 力矩：N·m
- 速度：m/s 或 rad/s
- 频率：Hz

## 参数来源规则

关键几何、质量、惯量、关节限位、执行器和传感器参数必须区分来源：

- `source: user_provided`：来自用户、CAD、数据手册或真实设计文件。
- `source: estimated`：为建模推进而估算，必须在输出文档中标记。
- `source: tbc`：待确认，不能静默当作真实工程参数使用。

## 禁止事项

- 不要生成玩具 demo。
- 不要只生成 README。
- 不要把参数硬编码散落在多个文件。
- 不要把 `estimated` 或 `tbc` 参数伪装成真实参数。
- 不要漏 inertial / collision。
- 不要让 joint axis 全部一样，除非机器人结构确实如此。
- 不要让控制器目标写死。
- 不要忽略关节限位。
- 不要忽略 effort / velocity limit。
- 不要让仿真模型变成动画模型而不是动力学模型。
- 不要使用 position-driven Plant 伪装 torque control。
- 不要生成无法验证的工程。
