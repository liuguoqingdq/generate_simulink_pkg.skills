# generate_simulink_pkg.skills

面向 **机器人仿真、控制器验证、Simulink / Simscape、Gazebo、ROS2、ros2_control** 的 Codex Skills 集合。

这个仓库不是一个机器人运行时工程包，也不是一个单独的 ROS2 package。它是一组给 Codex 使用的 **Skills**，用于约束 Codex 在生成机器人仿真 / 控制工程时的行为，让 Codex 先整理需求，再生成工程，最后检查工程质量。

它的核心目标是：

> 不让 Codex 直接生成一个“看起来像机器人、实际不可验证、joint name 到处不一致、没有惯量、没有 collision、controller 配不起来”的玩具 demo，而是生成一个有规格、有接口、有验证脚本、有文档、有工程质量门的机器人仿真控制包。

推荐使用流程如下：

```text
粗略机器人想法
    ↓
robot-sim-requirements-intake
    ↓
robot_spec.yaml + 缺失信息清单 + 风险提醒 + 给 Codex 的最终提示词
    ↓
robot-sim-control-package-generation
    ↓
ROS2 / Gazebo / Simulink / Simscape / ros2_control 工程包
    ↓
robot-sim-control-package-validation
    ↓
接口一致性检查 + 动力学质量检查 + 修复方案 + 验证命令
```

---

## 目录

- [1. 这个仓库解决什么问题](#1-这个仓库解决什么问题)
- [2. 仓库里有什么](#2-仓库里有什么)
- [3. 三个 Skill 的分工](#3-三个-skill-的分工)
- [4. 适用场景与不适用场景](#4-适用场景与不适用场景)
- [5. 安装方式](#5-安装方式)
- [6. 安装后如何确认生效](#6-安装后如何确认生效)
- [7. 最推荐的使用流程](#7-最推荐的使用流程)
- [8. 使用前需要提供哪些信息](#8-使用前需要提供哪些信息)
- [9. 不同机器人类型需要补充的信息](#9-不同机器人类型需要补充的信息)
- [10. robot_spec.yaml 说明](#10-robot_specyaml-说明)
- [11. robot_spec.yaml 完整模板](#11-robot_specyaml-完整模板)
- [12. 6 自由度机械臂示例](#12-6-自由度机械臂示例)
- [13. 差速小车示例](#13-差速小车示例)
- [14. 工程生成后会有哪些文件](#14-工程生成后会有哪些文件)
- [15. 生成包里的关键文件分别干什么](#15-生成包里的关键文件分别干什么)
- [16. Simulink / Simscape 生成规则](#16-simulink--simscape-生成规则)
- [17. ROS2 / ros2_control 生成规则](#17-ros2--ros2_control-生成规则)
- [18. Gazebo 生成规则](#18-gazebo-生成规则)
- [19. MoveIt2、Nav2 与本仓库的关系](#19-moveit2nav2-与本仓库的关系)
- [20. 验证方式](#20-验证方式)
- [21. 常用提示词模板](#21-常用提示词模板)
- [22. 典型工作流示例](#22-典型工作流示例)
- [23. 常见问题](#23-常见问题)
- [24. 排错指南](#24-排错指南)
- [25. 维护与扩展建议](#25-维护与扩展建议)

---

## 1. 这个仓库解决什么问题

机器人仿真与控制工程生成最容易出现的问题不是“文件不够多”，而是 **接口和工程语义不一致**。

比如你让 Codex 生成一个机械臂工程，它很可能会犯这些错误：

- URDF 里叫 `joint1`，`controllers.yaml` 里叫 `shoulder_joint`；
- ros2_control 里定义了 `position` command interface，但 Simulink 控制器输出的是 effort；
- Simscape 模型看起来在动，但其实是 position-driven 动画，不是动力学仿真；
- 机器人 link 只有 visual，没有 collision；
- 有 collision 但没有 inertial；
- 所有关节轴都写成 `[0, 0, 1]`，机械结构完全不可信；
- controller goal 写死在代码里，换一个目标就要改源码；
- 参数散落在 URDF、Python launch、YAML、MATLAB 脚本里，后续无法维护；
- 生成了 README，但没有验证脚本；
- `estimated` 参数被当成真实参数写进工程，后续没人知道哪些是估算的。

这个仓库通过三个 skill 把生成过程拆成三步：

1. **需求规格化**：先把机器人抽象成 link / joint / actuator / sensor，并生成 `robot_spec.yaml`。
2. **工程生成**：只根据 `robot_spec.yaml` 这个单一事实源生成工程。
3. **工程验证**：检查 joint name、动力学、collision、ros2_control、controller、仿真接口是否一致。

最终希望形成这样的心智模型：

```text
robot_spec.yaml 是唯一事实源
URDF / Xacro / Simscape / Gazebo / ros2_control / controllers.yaml / launch 都从它派生
验证脚本再反向检查这些派生文件有没有偏离规格
```

---

## 2. 仓库里有什么

当前仓库包含三个可安装 skill：

```text
generate_simulink_pkg.skills/
├── README.md
└── skills/
    ├── robot-sim-requirements-intake/
    ├── robot-sim-control-package-generation/
    └── robot-sim-control-package-validation/
```

每个 skill 内部通常包含：

```text
SKILL.md                       # skill 的核心行为说明
requirements.txt               # 可选 Python 脚本依赖
assets/                        # 示例 robot_spec、提示词模板
references/                    # 通用工程契约、schema、机器人类型附录、验证清单
scripts/                       # robot_spec 校验脚本
```

三个 skill 共享一套机器人仿真控制工程规则：

- 通用工程契约：`references/common_contract.md`
- robot_spec 结构：`references/robot_spec_schema.md`
- 机器人类型附录：`references/robot_type_appendix.md`
- 验证清单：`references/validation_checklist.md`
- 示例机械臂规格：`assets/example_arm_6dof_robot_spec.yaml`
- 示例差速小车规格：`assets/example_diff_drive_robot_spec.yaml`
- 静态校验脚本：`scripts/validate_robot_spec.py`

---

## 3. 三个 Skill 的分工

### 3.1 `robot-sim-requirements-intake`

用途：把粗略需求整理成可执行的工程规格。

它不负责直接生成工程包，主要输出：

1. `robot_spec.yaml`
2. 缺失信息清单
3. 工程风险提醒
4. 给 Codex 的最终提示词

适合在这些场景使用：

```text
帮我把 6 自由度机械臂需求整理成 Codex 输入
我要做双足机器人 Simulink + ros2_control 仿真，先帮我列需求清单
我只有一个小车结构想法，帮我整理成 robot_spec.yaml
```

这个 skill 会重点做这些事情：

- 判断机器人类型；
- 抽象 link、joint、actuator、sensor；
- 统一 ROS 坐标系约定；
- 生成 `robot_spec.yaml`；
- 标记哪些参数来自用户、哪些是估算、哪些待确认；
- 不随便编造关键结构参数；
- 输出最终可复制给 Codex 的生成提示词。

---

### 3.2 `robot-sim-control-package-generation`

用途：根据 `robot_spec.yaml` 生成机器人仿真控制工程包。

主要输入：

- `robot_spec.yaml`
- 或者等价的结构化信息

主要输出可能包括：

- ROS2 package 结构；
- URDF / Xacro；
- `ros2_control` 配置；
- `controllers.yaml`；
- Gazebo 插件与仿真配置；
- Simulink / Simscape 生成脚本；
- MATLAB `.m` builder 脚本；
- launch 文件；
- RViz 配置；
- Python / shell 验证脚本；
- README 和 docs。

适合在这些场景使用：

```text
使用这个 robot_spec.yaml 生成 ROS2 Humble + Gazebo + ros2_control 包
根据我给的机械臂结构，生成 Simulink/Simscape 闭环验证工程
给我一个双足机器人 torque-driven Plant + ros2_control 工程包
```

这个 skill 的重点不是“能生成文件”，而是：

- 生成的文件要能跑；
- joint name 要一致；
- 控制接口和仿真接口要一致；
- 不生成伪动力学动画；
- 不把参数写散；
- 生成验证脚本；
- README 命令要能复现构建、启动、验证流程。

---

### 3.3 `robot-sim-control-package-validation`

用途：检查一个已经生成的机器人仿真控制包是否合格。

它会重点检查：

- `params/robot_spec.yaml` 是否存在；
- URDF / Xacro 是否存在；
- ros2_control 配置是否存在；
- `controllers.yaml` 是否存在；
- launch 文件是否正确加载 robot description 和 controllers；
- link 是否有 visual / collision / inertial；
- joint 是否有 parent / child / origin / axis / limit / dynamics；
- joint name 是否在 URDF、ros2_control、controllers.yaml、launch、脚本之间一致；
- actuator 是否引用真实存在的 joint；
- sensor 是否引用真实存在的 link；
- Plant 输入输出是否和 controller 对得上；
- 是否用 position animation 假装 torque control；
- 是否保留 `source: estimated` 和 `source: tbc` 标记；
- 是否存在验证脚本。

输出结构通常是：

1. 总体结论：可运行 / 基本可运行但有风险 / 不合格
2. 必修问题：会导致不能运行或接口错乱的问题
3. 工程质量问题：会导致 demo 化、后续难维护的问题
4. 机器人类型专项问题
5. 建议修复顺序
6. 具体补丁或修改后的文件
7. 验证命令

适合在这些场景使用：

```text
检查这个包是不是玩具 demo
帮我看 controller.yaml 和 URDF joint name 是否一致
这个 Simscape Plant 是不是伪装的动画模型
帮我补 validate 脚本
```

---

## 4. 适用场景与不适用场景

### 4.1 适用场景

适合生成或规范这些类型的工程：

- ROS2 Humble / Jazzy 机器人仿真包；
- Gazebo + `gazebo_ros2_control` 工程；
- Simulink / Simscape 控制验证工程；
- ros2_control 的硬件接口、controller 配置、launch 文件；
- 机械臂动力学仿真和关节控制；
- 差速小车 / 四轮小车 / 阿克曼车仿真；
- 移动机械臂建模；
- 双足、四足、轮腿机器人的 link / joint / actuator / sensor 结构整理；
- 无人机或云台控制接口整理；
- 需要 Codex 生成完整工程包，而不是只生成解释文本；
- 需要检查一个工程包是否存在命名、接口和动力学错误。

### 4.2 不适用场景

不适合：

- 只是想问 ROS2、MoveIt2、Simulink 的概念；
- 只是想生成一段单独代码；
- 只是想生成 CAD 模型或工业级 mesh；
- 没有任何结构信息，却希望生成真实可用的机械系统；
- 想跳过规格阶段，直接让 Codex 猜所有参数；
- 希望生成没有 collision、没有 inertial、没有验证脚本的展示 demo；
- 希望把估算参数伪装成真实参数。

---

## 5. 安装方式

### 5.1 通过 Codex 从 GitHub 安装

在 Codex 中输入：

```text
Install the skills from liuguoqingdq/generate_simulink_pkg.skills:
- skills/robot-sim-requirements-intake
- skills/robot-sim-control-package-generation
- skills/robot-sim-control-package-validation
```

安装完成后，重启 Codex，让新安装的 skills 被重新发现。

---

### 5.2 使用 installer 脚本安装

如果你的 Codex 环境里有官方 skill installer，可以执行：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo liuguoqingdq/generate_simulink_pkg.skills \
  --path skills/robot-sim-requirements-intake \
  --path skills/robot-sim-control-package-generation \
  --path skills/robot-sim-control-package-validation
```

然后重启 Codex。

---

### 5.3 手动本地安装

克隆仓库：

```bash
git clone https://github.com/liuguoqingdq/generate_simulink_pkg.skills.git
cd generate_simulink_pkg.skills
```

复制三个 skill 到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R skills/robot-sim-requirements-intake ~/.codex/skills/
cp -R skills/robot-sim-control-package-generation ~/.codex/skills/
cp -R skills/robot-sim-control-package-validation ~/.codex/skills/
```

重启 Codex。

---

### 5.4 本地开发安装

如果你想修改这些 skill，并希望 Codex 使用你本地修改后的版本，可以用软链接方式：

```bash
mkdir -p ~/.codex/skills
ln -s "$PWD/skills/robot-sim-requirements-intake" ~/.codex/skills/robot-sim-requirements-intake
ln -s "$PWD/skills/robot-sim-control-package-generation" ~/.codex/skills/robot-sim-control-package-generation
ln -s "$PWD/skills/robot-sim-control-package-validation" ~/.codex/skills/robot-sim-control-package-validation
```

这样你修改仓库文件后，不需要重复复制。但通常仍然需要重启 Codex 才能让 skill 说明重新加载。

---

### 5.5 安装 Python 校验脚本依赖

每个 skill 中都有 `scripts/validate_robot_spec.py`，用于静态检查 `robot_spec.yaml`。

依赖安装：

```bash
python3 -m pip install -r skills/robot-sim-requirements-intake/requirements.txt
```

当前主要依赖：

```text
pyyaml>=6.0
```

也可以直接安装：

```bash
python3 -m pip install pyyaml
```

---

### 5.6 更新 skill

如果你通过 GitHub 克隆安装：

```bash
cd generate_simulink_pkg.skills
git pull
cp -R skills/robot-sim-requirements-intake ~/.codex/skills/
cp -R skills/robot-sim-control-package-generation ~/.codex/skills/
cp -R skills/robot-sim-control-package-validation ~/.codex/skills/
```

然后重启 Codex。

如果你用软链接安装，只需要：

```bash
cd generate_simulink_pkg.skills
git pull
```

然后重启 Codex。

---

### 5.7 卸载 skill

```bash
rm -rf ~/.codex/skills/robot-sim-requirements-intake
rm -rf ~/.codex/skills/robot-sim-control-package-generation
rm -rf ~/.codex/skills/robot-sim-control-package-validation
```

然后重启 Codex。

---

## 6. 安装后如何确认生效

安装后可以在 Codex 中测试：

```text
请列出当前可用的 robot-sim 相关 skills。
```

或者直接给一个触发任务：

```text
请使用 robot-sim-requirements-intake skill，帮我把一个差速小车整理成 robot_spec.yaml。
要求 ROS2 Humble + Gazebo + ros2_control，使用 diff_drive_controller。
```

如果 skill 生效，Codex 应该会：

- 先询问或整理机器人类型、link、joint、actuator、sensor；
- 输出 `robot_spec.yaml`；
- 标记缺失信息；
- 不直接生成工程代码；
- 给出下一步可复制给工程生成 skill 的提示词。

如果 Codex 直接开始写 URDF、launch、controller，而没有先整理 `robot_spec.yaml`，说明你可能没有明确要求使用 `robot-sim-requirements-intake`，或者 skill 没有被正确加载。

---

## 7. 最推荐的使用流程

### 7.1 总体流程

```text
Step 1：需求整理
    输入：粗略机器人想法
    输出：robot_spec.yaml + 缺失信息清单 + 风险提醒 + 生成提示词

Step 2：工程生成
    输入：robot_spec.yaml
    输出：ROS2 / Gazebo / Simulink / Simscape / ros2_control 工程包

Step 3：工程验证
    输入：生成后的工程包
    输出：问题清单 + 修复方案 + 验证命令
```

### 7.2 为什么不要一上来就生成工程

因为机器人仿真控制包不是普通脚手架，它至少需要这些信息统一：

- 结构拓扑；
- 坐标系；
- link 名称；
- joint 名称；
- joint origin；
- joint axis；
- joint limit；
- 动力学参数；
- actuator 接口；
- sensor 接口；
- controller 输入输出；
- Plant 输入输出；
- ROS2 topic / controller / launch 约定。

如果这些信息没整理好，Codex 越早写代码，后面错得越多。这个仓库的路线是：

```text
先把规格写对，再让 Codex 写代码。
```

---

## 8. 使用前需要提供哪些信息

你不一定一开始就要提供所有信息。`robot-sim-requirements-intake` 可以帮你整理缺失项。

但如果你想让 Codex 生成一个更接近可运行的工程，最好尽量提供下面这些信息。

---

### 8.1 项目信息

| 信息 | 是否必须 | 示例 | 说明 |
|---|---:|---|---|
| 项目名 | 推荐 | `arm_6dof_robot` | 用于 package 名、README、launch 命名 |
| 机器人类型 | 必须 | `arm_6dof` / `diff_drive` | 决定专项检查规则 |
| 目标平台 | 必须 | ROS2 Humble、Gazebo、Simulink | 决定生成哪些文件 |
| Ubuntu 版本 | 推荐 | `22.04` | ROS2 Humble 常用 Ubuntu 22.04 |
| ROS2 发行版 | 推荐 | `humble` | 影响依赖和命令 |
| 目标用途 | 必须 | 控制验证、ros2_control 部署 | 决定工程重点 |

示例：

```yaml
project:
  name: arm_6dof_robot
  robot_type: arm_6dof
  goal:
    - simscape_control_validation
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
```

---

### 8.2 坐标系信息

至少需要明确：

| 信息 | 是否必须 | 示例 |
|---|---:|---|
| 坐标系约定 | 必须 | ROS 约定 |
| X 轴方向 | 必须 | forward |
| Y 轴方向 | 必须 | left |
| Z 轴方向 | 必须 | up |
| base frame | 必须 | `base_link` |
| odom frame | 移动机器人推荐 | `odom` |
| map frame | 导航机器人推荐 | `map` |
| end effector frame | 机械臂必须 | `tool0` |
| imu frame | 移动 / 腿式 / 无人机推荐 | `imu_link` |

推荐默认使用 ROS 约定：

```text
X forward
Y left
Z up
```

示例：

```yaml
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
```

---

### 8.3 link 信息

每个 link 建议提供：

| 字段 | 是否必须 | 示例 | 说明 |
|---|---:|---|---|
| `name` | 必须 | `upper_arm_link` | link 名称 |
| `role` | 推荐 | `upper_arm` | 语义角色 |
| `moving` | 推荐 | `true` | 是否运动 link |
| `source` | 必须 | `user_provided` / `estimated` / `tbc` | 参数来源 |
| visual geometry | 必须 | box / cylinder / sphere / mesh | 可视化几何 |
| collision geometry | 必须 | box / cylinder / sphere | 碰撞几何，建议简单稳定 |
| mass | 必须 | `1.2` | kg |
| COM | 推荐 | `[0, 0, 0.16]` | 质心位置 |
| inertia | 必须 | `auto_box` 或矩阵 | 惯量 |

示例：

```yaml
links:
  - name: upper_arm_link
    role: upper_arm
    moving: true
    source: estimated
    geometry:
      visual:
        type: box
        size: [0.08, 0.06, 0.32]
      collision:
        type: box
        size: [0.08, 0.06, 0.32]
    inertial:
      mass: 1.2
      com_xyz: [0.0, 0.0, 0.16]
      inertia: auto_box
```

注意：

- 主要 link 不应该只有 visual；
- moving link 必须有 inertial；
- collision 不一定要和 visual 一样复杂，优先稳定；
- mesh 可以后续加，早期推荐 primitive；
- 真实参数不知道时要标 `estimated` 或 `tbc`。

---

### 8.4 joint 信息

每个 joint 建议提供：

| 字段 | 是否必须 | 示例 | 说明 |
|---|---:|---|---|
| `name` | 必须 | `shoulder_lift_joint` | joint 名称 |
| `type` | 必须 | `revolute` / `continuous` / `fixed` | joint 类型 |
| `parent` | 必须 | `shoulder_link` | 父 link |
| `child` | 必须 | `upper_arm_link` | 子 link |
| `origin_xyz` | 必须 | `[0, 0, 0.1]` | joint 相对 parent 的位置 |
| `origin_rpy` | 必须 | `[0, 0, 0]` | joint 相对 parent 的姿态 |
| `axis` | 非 fixed 必须 | `[0, 1, 0]` | 关节轴 |
| `limit.lower` | revolute 必须 | `-1.8` | 下限 rad |
| `limit.upper` | revolute 必须 | `1.8` | 上限 rad |
| `limit.effort` | 非 fixed 推荐 | `80` | 力矩限制 |
| `limit.velocity` | 非 fixed 推荐 | `2.5` | 速度限制 |
| `dynamics.damping` | 推荐 | `0.6` | 阻尼 |
| `dynamics.friction` | 推荐 | `0.04` | 摩擦 |

示例：

```yaml
joints:
  - name: shoulder_lift_joint
    type: revolute
    source: estimated
    parent: shoulder_link
    child: upper_arm_link
    origin_xyz: [0.0, 0.0, 0.10]
    origin_rpy: [0.0, 0.0, 0.0]
    axis: [0.0, 1.0, 0.0]
    limit:
      lower: -1.8
      upper: 1.8
      effort: 80.0
      velocity: 2.5
    dynamics:
      damping: 0.6
      friction: 0.04
```

注意：

- 机械臂、双足、四足的 joint axis 不能全部一样；
- fixed joint 不需要 limit；
- continuous joint 不需要 lower / upper，但需要 effort / velocity；
- revolute joint 必须有 lower / upper / effort / velocity；
- parent-child 拓扑不能断链，不能出现重复 child link。

---

### 8.5 actuator 信息

每个 actuator 建议提供：

| 字段 | 是否必须 | 示例 | 说明 |
|---|---:|---|---|
| `name` | 必须 | `shoulder_lift_motor` | 执行器名称 |
| `joint` | 必须 | `shoulder_lift_joint` | 对应 joint |
| `command_interface` | 必须 | `effort` / `position` / `velocity` | 命令接口 |
| `state_interfaces` | 必须 | `[position, velocity, effort]` | 状态接口 |
| `effort_limit` | 推荐 | `80` | effort 限制 |
| `velocity_limit` | 推荐 | `2.5` | 速度限制 |
| `source` | 必须 | `estimated` | 参数来源 |

示例：

```yaml
actuators:
  - name: shoulder_lift_motor
    joint: shoulder_lift_joint
    source: estimated
    command_interface: effort
    state_interfaces: [position, velocity, effort]
    effort_limit: 80.0
    velocity_limit: 2.5
```

注意：

- actuator 引用的 joint 必须存在；
- actuator 的 command interface 要和 control 输出一致；
- actuator 的接口要和 ros2_control 中的 command/state interfaces 一致。

---

### 8.6 sensor 信息

传感器不是所有机器人都必须有，但很多场景强烈建议提供。

| 机器人类型 | 推荐传感器 |
|---|---|
| 差速小车 | wheel odom、LiDAR、camera、IMU |
| 移动机械臂 | odom、LiDAR、camera、arm joint states |
| 双足 / 四足 | IMU、foot contact sensor、joint states |
| 无人机 | IMU、pose、velocity、angular velocity |
| 云台 | encoder、camera optical frame |

传感器字段示例：

```yaml
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
```

注意：

- sensor 的 link / parent 必须在 links 中存在，或者明确要求生成固定安装 link；
- camera 需要额外注意 optical frame 约定；
- 移动机器人如果要做 Nav2，建议明确 `/odom`、`/tf`、`/scan` 或 `/camera`。

---

### 8.7 control 信息

控制信息决定 Simulink、ros2_control、controller 的接口如何连接。

| 字段 | 示例 | 说明 |
|---|---|---|
| `controller_type` | `joint_space_pd` | 控制器类型 |
| `control_space` | `joint_space` | 控制空间 |
| `sample_time_s` | `0.002` | 控制周期 |
| `command_input` | `joint_trajectory` | 控制器接收什么命令 |
| `feedback` | `[joint_position, joint_velocity]` | 控制器反馈 |
| `output` | `effort` | 控制器输出 |
| `limits.enforce_effort` | `true` | 是否限制 effort |
| `limits.enforce_velocity` | `true` | 是否限制 velocity |
| `limits.enforce_acceleration` | `true` | 是否限制 acceleration |

示例：

```yaml
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
```

关键原则：

```text
control.output 必须和 simulation.plant_input 对得上
control.output 必须和 actuator.command_interface 对得上
control.output 必须和 ros2_control.command_interfaces 对得上
```

例如：

| 控制输出 | Plant 输入 | ros2_control command interface | 常见场景 |
|---|---|---|---|
| `effort` | `effort` | `effort` | 机械臂力矩控制、腿式机器人 |
| `velocity` | `velocity` | `velocity` | 差速小车、轮式机器人 |
| `position` | `position` | `position` | 舵机云台、简单位置控制机械臂 |

---

### 8.8 simulation 信息

仿真信息决定 Plant 怎么建。

示例：

```yaml
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
```

关键字段说明：

| 字段 | 含义 |
|---|---|
| `plant_input` | Plant 接收的输入，通常是 effort / velocity / position / motor_speed |
| `plant_output` | Plant 输出，如 q、dq、odom、imu、pose、contact |
| `dynamic_simulation_required` | 是否要求真实动力学仿真 |
| `collision_required` | 是否必须生成 collision |
| `inertial_required` | 是否必须生成 inertial |
| `simscape.torque_driven` | Simscape 是否 torque-driven |
| `gazebo.use_gazebo_ros2_control` | Gazebo 是否接 ros2_control |

注意：

- 如果要求 torque-driven，就不能用 position-driven 动画伪装；
- 如果 Plant 输入是 effort，controller 输出也应该是 effort；
- 如果 Plant 输出需要 odom，就必须定义 odom 的来源和接口。

---

### 8.9 ros2_control 信息

示例：

```yaml
ros2_control:
  hardware_plugin: gazebo_ros2_control/GazeboSystem
  joints:
    - name: shoulder_pan_joint
      command_interfaces: [effort]
      state_interfaces: [position, velocity, effort]
  controllers:
    joint_state_broadcaster: true
    joint_trajectory_controller: true
```

常见映射：

| 机器人类型 | command interface | state interfaces | 常见 controller |
|---|---|---|---|
| 差速小车 | `velocity` | `position`, `velocity` | `diff_drive_controller` |
| 机械臂 | `effort` / `position` | `position`, `velocity`, `effort` | `joint_trajectory_controller` |
| 双足 / 四足 | `effort` | `position`, `velocity`, `effort` | effort controllers / custom controller |
| 云台 | `position` / `velocity` | `position`, `velocity` | position controller / velocity controller |

注意：

- ros2_control 的 joint name 必须和 URDF 一致；
- command interface 必须和 actuator 一致；
- controller 类型必须和 interface 匹配；
- `controllers.yaml` 里的 joint list 不能漏关节，也不能写不存在的关节。

---

### 8.10 validation 信息

推荐总是要求生成验证脚本：

```yaml
validation:
  generate_validate_script: true
  check_urdf: true
  check_joint_name_consistency: true
  check_inertial_collision: true
  check_limits_dynamics: true
  check_interface_contract: true
```

推荐总是保留禁止事项：

```yaml
forbidden:
  - toy_demo
  - readme_only
  - hardcoded_scattered_params
  - missing_inertial
  - missing_collision
  - fake_position_animation
```

---

## 9. 不同机器人类型需要补充的信息

### 9.1 差速小车

必须补充：

| 信息 | 示例 |
|---|---|
| 轮半径 | `wheel_radius: 0.08` |
| 轮宽 | `wheel_width: 0.03` |
| 轮距 | `wheel_separation: 0.30` |
| 底盘长宽高 | `0.36 x 0.28 x 0.12` |
| 左右轮 joint | `left_wheel_joint`, `right_wheel_joint` |
| 轮子 axis | 通常 `[0, 1, 0]`，视模型坐标而定 |
| cmd_vel 接口 | `/cmd_vel` |
| odom 输出 | `/odom` |
| 是否需要 LiDAR / Camera | Nav2 通常需要 LiDAR |
| controller | `diff_drive_controller` |

关键约束：

- 左右轮对称；
- 轮子 axis 正确；
- base_link 到 wheel 的 origin 正确；
- `cmd_vel` 到左右轮速度的映射正确；
- wheel joint 的 command interface 通常是 `velocity`。

---

### 9.2 四轮小车 / 阿克曼车

四轮小车必须补充：

- front_left_wheel / front_right_wheel / rear_left_wheel / rear_right_wheel；
- wheelbase；
- track_width；
- wheel_radius；
- 驱动方式：四驱 / 后驱 / 前驱；
- 转向方式：差速 / 阿克曼 / 全向。

阿克曼车还要补充：

- front_left_steering_joint；
- front_right_steering_joint；
- rear wheel drive joints；
- steering limit；
- steering geometry。

关键约束：

- 转向 joint 和驱动 wheel joint 不能混淆；
- steering command interface 和 wheel command interface 要分开；
- wheelbase 和 track_width 影响运动学模型，不能乱填。

---

### 9.3 履带车

必须补充：

- left_track_link / right_track_link；
- track_width；
- track_contact_length；
- sprocket_radius；
- 驱动方式：左右履带速度 / 左右 sprocket velocity / effort；
- `cmd_vel` 到左右履带速度的映射；
- 地面接触和摩擦参数；
- odom 输出。

关键约束：

- 左右履带对称；
- 接触模型不能只用视觉 mesh；
- 履带速度方向要和 base_link 坐标系一致。

---

### 9.4 机械臂

必须补充：

| 信息 | 示例 |
|---|---|
| 自由度 | `6` |
| 关节轴序列 | Z, Y, Y, X, Y, X |
| link 长度 | upper arm、forearm 等 |
| tool0 位置 | wrist3 到 tool0 的 fixed transform |
| 关节限位 | lower / upper |
| effort limit | 每个关节最大力矩 |
| velocity limit | 每个关节最大角速度 |
| controller | `joint_trajectory_controller` |
| 是否使用 MoveIt2 | true / false |

关键约束：

- joint axis 不要全部相同；
- tool0 必须存在；
- 每个 revolute joint 必须有 limit；
- 机械臂末端链路必须连续；
- 如果要 MoveIt2，joint names 和 planning group 后续也要一致。

---

### 9.5 移动机械臂

必须补充：

- mobile_base 部分；
- arm 部分；
- base_link 到 arm_base_link 的 fixed transform；
- 底盘控制接口；
- 机械臂控制接口；
- 是否生成 Nav2 配置；
- 是否生成 MoveIt2 配置。

关键约束：

- 移动底盘和机械臂必须通过 fixed joint 连接；
- `base_link` / `arm_base_link` / `tool0` 命名要清楚；
- 底盘 controller 和机械臂 controller 不要混成一个未定义接口；
- Nav2 控制底盘，MoveIt2 控制机械臂，两者通过任务层或行为树协调。

---

### 9.6 双足机器人

必须补充：

- pelvis_link / torso_link；
- left_leg links / right_leg links；
- hip yaw / roll / pitch joints；
- knee pitch joint；
- ankle pitch / roll joints；
- foot_link；
- 左右腿对称关系；
- 腿长；
- 脚底尺寸；
- 质心高度；
- IMU 安装位置；
- foot contact sensor；
- stand posture；
- walking gait primitive。

关键约束：

- 左右腿结构对称；
- foot_link 必须有 collision；
- 必须有 IMU；
- 最好有 contact sensor；
- 腿部 joint limit 要合理；
- effort control 和 position control 要明确。

---

### 9.7 四足机器人

必须补充：

- body_link；
- front_left_leg / front_right_leg / rear_left_leg / rear_right_leg；
- hip joints；
- thigh links；
- shank links；
- foot links；
- 每条腿的安装位置；
- 步态：walk / trot / bound；
- foot contact sensor；
- IMU；
- body velocity command。

关键约束：

- 四条腿结构镜像对称；
- foot collision 必须存在；
- 每条腿 joint axis 正确；
- 腿部控制接口通常是 effort 或 position，不要含糊。

---

### 9.8 轮腿机器人

必须补充：

- body_link；
- left_leg / right_leg 或四条腿结构；
- wheel_link 与 wheel_joint；
- hip / knee / ankle 或等效腿部 joints；
- 轮子半径；
- 轮距；
- 腿长；
- 足端或轮端接触模型；
- body velocity command；
- wheel velocity / leg effort 的混合控制接口；
- IMU 和 wheel odom；
- 站立高度、蹲起范围、轮地接触约束。

关键约束：

- 轮子 joint axis 与腿部 joint axis 分别正确；
- 轮速控制和腿部 effort / position 控制不能混成同一个未定义接口；
- 轮地接触和站立高度不能省略。

---

### 9.9 无人机

必须补充：

- base_link / body_link；
- motor links 和 propeller links；
- 机臂长度；
- 机身尺寸；
- 质量分布；
- 惯量矩阵；
- rotor 安装位置；
- rotor 旋向；
- thrust coefficient；
- torque coefficient；
- motor speed 或 thrust command 接口；
- IMU；
- pose / velocity / angular velocity feedback；
- 控制器：姿态 PID / 位置 PID / cascaded controller；
- 是否需要 Gazebo / Simscape / PX4 接口。

关键约束：

- 惯量矩阵和电机旋向不能省略；
- Plant 输入必须明确是 motor speed、thrust 还是 wrench；
- 电机旋向、推力系数、力矩系数会直接影响姿态动力学。

---

### 9.10 云台

必须补充：

- base_link；
- yaw_link / pitch_link / roll_link；
- camera_link 或 payload_link；
- yaw / pitch / roll joint axis；
- 每个轴的 limit、velocity limit、effort limit；
- command_interface：position 或 velocity；
- state_interface：position、velocity，可选 effort；
- 控制器：position PID / velocity PID；
- 负载质量、质心和惯量。

关键约束：

- 轴向顺序必须明确；
- camera optical frame 与 ROS optical frame 约定不能混淆；
- 负载质量和质心对控制性能影响很大。

---

## 10. robot_spec.yaml 说明

`robot_spec.yaml` 是整个流程的核心文件。

它不是普通配置文件，而是机器人仿真控制工程的 **单一事实源**。

推荐包含以下顶层字段：

```yaml
project:        # 项目信息
frames:         # 坐标系和语义 frame
links:          # 刚体列表
joints:         # 连接关系和运动学拓扑
actuators:      # 执行器和控制接口
sensors:        # 传感器，可选但推荐
control:        # 控制器输入输出约定
simulation:     # Plant / Gazebo / Simscape 仿真约定
ros2_control:   # ros2_control joint 和 controller 约定
outputs:        # 期望生成的文件结构
validation:     # 验证目标
forbidden:      # 禁止生成的低质量内容
```

---

### 10.1 source 标记规则

关键结构、几何、质量、惯量、关节限位、执行器和传感器参数必须区分来源。

| source | 含义 | 能否直接作为最终工程参数 |
|---|---|---|
| `user_provided` | 用户、CAD、数据手册或真实设计文件提供 | 可以 |
| `estimated` | 为推进建模给出的估计值 | 可以生成，但必须在 README/docs 标记 |
| `tbc` | 待确认 | 不应静默进入最终工程，除非用户明确接受占位 |

示例：

```yaml
links:
  - name: upper_arm_link
    source: estimated
    notes: "尺寸和质量为估计值，后续应替换为 CAD 或实测参数。"
```

---

### 10.2 单位规则

推荐统一单位：

| 量 | 单位 |
|---|---|
| 长度 | m |
| 角度 | rad |
| 质量 | kg |
| 力矩 | N·m |
| 线速度 | m/s |
| 角速度 | rad/s |
| 频率 | Hz |
| 时间 | s |

---

### 10.3 命名规则

推荐命名：

| 类型 | 示例 |
|---|---|
| base link | `base_link` |
| 机械臂底座 | `arm_base_link` |
| 机械臂末端 | `tool0` |
| 左轮 link | `left_wheel_link` |
| 左轮 joint | `left_wheel_joint` |
| 肩部关节 | `shoulder_pan_joint`, `shoulder_lift_joint` |
| 腕部关节 | `wrist1_joint`, `wrist2_joint`, `wrist3_joint` |
| IMU link | `imu_link` |
| 相机 link | `camera_link` |

硬规则：

```text
URDF、Xacro、Simulink、Simscape、Gazebo、ros2_control、controllers.yaml、launch、验证脚本中的 joint name 必须完全一致。
```

---

## 11. robot_spec.yaml 完整模板

下面是一个通用模板。实际使用时可以删掉不需要的字段，但不建议删掉核心结构。

```yaml
project:
  name: my_robot
  robot_type: arm_6dof
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
    source: estimated
    geometry:
      visual:
        type: box
        size: [0.20, 0.20, 0.08]
      collision:
        type: box
        size: [0.20, 0.20, 0.08]
    inertial:
      mass: 2.0
      com_xyz: [0.0, 0.0, 0.0]
      inertia:
        ixx: auto
        ixy: 0.0
        ixz: 0.0
        iyy: auto
        iyz: 0.0
        izz: auto

joints:
  - name: joint1
    type: revolute
    source: user_provided
    parent: base_link
    child: link1
    origin_xyz: [0.0, 0.0, 0.08]
    origin_rpy: [0.0, 0.0, 0.0]
    axis: [0.0, 0.0, 1.0]
    limit:
      lower: -3.14
      upper: 3.14
      effort: 80.0
      velocity: 2.5
    dynamics:
      damping: 0.5
      friction: 0.03

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
    - params/
    - urdf/
    - config/
    - launch/
    - scripts/
    - matlab/
    - test/
    - docs/
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

---

## 12. 6 自由度机械臂示例

下面是一个适合触发需求整理 skill 的自然语言输入：

```text
请使用 robot-sim-requirements-intake skill，帮我整理一个 6 自由度机械臂的 robot_spec.yaml。

目标：
- 用 Simulink / Simscape 做关节空间控制算法验证
- 用 ROS2 Humble + Gazebo + ros2_control 做部署接口验证
- 控制器输出 effort
- Simscape Plant 必须是 torque-driven，不要用 position 动画伪装
- Gazebo 使用 gazebo_ros2_control/GazeboSystem

结构：
- base_link
- shoulder_link
- upper_arm_link
- forearm_link
- wrist1_link
- wrist2_link
- wrist3_link
- tool0

关节：
- shoulder_pan_joint: Z axis
- shoulder_lift_joint: Y axis
- elbow_joint: Y axis
- wrist1_joint: X axis
- wrist2_joint: Y axis
- wrist3_joint: X axis
- tool0_fixed_joint: fixed

如果我没有提供质量、惯量、关节限位，请用 estimated 标记，并列出后续需要替换的参数。
最后给我一份可以直接粘贴给 Codex 的工程生成提示词。
```

生成后的机械臂 `robot_spec.yaml` 应该体现：

- `robot_type: arm_6dof`；
- revolute joint 数量为 6；
- `tool0` 存在；
- 每个 revolute joint 有 limit；
- joint axis 不全部相同；
- actuator command interface 为 effort；
- ros2_control command interface 为 effort；
- Plant input 为 effort；
- Simscape 为 torque-driven。

---

## 13. 差速小车示例

下面是一个适合触发需求整理 skill 的自然语言输入：

```text
请使用 robot-sim-requirements-intake skill，帮我整理一个差速小车 robot_spec.yaml。

目标平台：
- Ubuntu 22.04
- ROS2 Humble
- Gazebo
- ros2_control

机器人结构：
- base_link 是底盘
- left_wheel_link / right_wheel_link 是左右轮
- left_wheel_joint / right_wheel_joint 是 continuous joint
- 轮半径 0.08 m
- 轮宽 0.03 m
- 轮距 0.30 m
- 底盘尺寸 0.36 x 0.28 x 0.12 m

控制：
- 使用 diff_drive_controller
- 输入 /cmd_vel
- 输出左右轮 velocity
- 需要 /odom

传感器：
- 先不加 LiDAR 和 camera

请标记 source，并输出缺失信息清单和最终 Codex 工程生成提示词。
```

生成后的差速小车 `robot_spec.yaml` 应该体现：

- `robot_type: diff_drive`；
- 左右轮 joint 为 continuous；
- wheel command interface 为 velocity；
- state interfaces 包含 position 和 velocity；
- control input 为 `cmd_vel`；
- Plant output 包含 odom；
- controller 为 `diff_drive_controller`；
- Gazebo 使用 ros2_control。

---

## 14. 工程生成后会有哪些文件

当使用 `robot-sim-control-package-generation` 时，推荐生成的工程结构如下：

```text
my_robot_sim_control_pkg/
├── README.md
├── package.xml
├── CMakeLists.txt
├── params/
│   ├── robot_spec.yaml
│   ├── generated_parameters.yaml
│   └── parameter_sources.md
├── urdf/
│   ├── robot.urdf.xacro
│   ├── robot_links.xacro
│   ├── robot_joints.xacro
│   ├── inertial_macros.xacro
│   └── gazebo_plugins.xacro
├── config/
│   ├── ros2_control.xacro
│   ├── controllers.yaml
│   ├── gazebo.yaml
│   ├── rviz.rviz
│   └── joint_limits.yaml
├── launch/
│   ├── display.launch.py
│   ├── sim.launch.py
│   ├── rsp.launch.py
│   └── controllers.launch.py
├── scripts/
│   ├── validate_robot_spec.py
│   ├── validate_robot_package.py
│   ├── check_joint_consistency.py
│   └── smoke_test.sh
├── matlab/
│   ├── build_simscape_model.m
│   ├── build_controller_model.m
│   ├── run_closed_loop_sim.m
│   └── README.md
├── test/
│   ├── test_urdf_parse.py
│   ├── test_joint_names.py
│   └── test_interfaces.py
└── docs/
    ├── interface_contract.md
    ├── control_contract.md
    ├── simulation_contract.md
    ├── ros2_control_contract.md
    └── known_estimated_parameters.md
```

实际文件会根据目标平台变化。

例如：

- 如果只需要 Gazebo + ROS2，`matlab/` 可以不存在；
- 如果只需要 Simulink / Simscape，Gazebo 相关配置可以不存在；
- 如果需要 MoveIt2，后续可以扩展 `moveit_config/`；
- 如果需要 Nav2，后续可以扩展 `nav2_config/`。

---

## 15. 生成包里的关键文件分别干什么

| 文件 / 目录 | 作用 |
|---|---|
| `params/robot_spec.yaml` | 单一事实源，保存机器人结构、接口、仿真、控制、验证要求 |
| `params/generated_parameters.yaml` | 从 spec 派生出的参数，供 launch / controller / 脚本读取 |
| `params/parameter_sources.md` | 记录哪些参数是用户提供、估算、待确认 |
| `urdf/robot.urdf.xacro` | 机器人主模型入口 |
| `urdf/robot_links.xacro` | link、visual、collision、inertial 定义 |
| `urdf/robot_joints.xacro` | joint、origin、axis、limit、dynamics 定义 |
| `urdf/inertial_macros.xacro` | 常用几何体惯量宏 |
| `urdf/gazebo_plugins.xacro` | Gazebo 插件和仿真标签 |
| `config/ros2_control.xacro` | ros2_control hardware 和 joint interface 定义 |
| `config/controllers.yaml` | controller_manager 加载的控制器配置 |
| `config/joint_limits.yaml` | 关节限制，可用于 MoveIt2 或控制器 |
| `config/rviz.rviz` | RViz 可视化配置 |
| `launch/display.launch.py` | 只启动 robot_state_publisher 和 RViz |
| `launch/sim.launch.py` | 启动 Gazebo、robot_state_publisher、controller_manager 等 |
| `launch/controllers.launch.py` | 加载 joint_state_broadcaster 和目标 controller |
| `scripts/validate_robot_package.py` | 验证生成包的结构和接口一致性 |
| `scripts/check_joint_consistency.py` | 检查 URDF、ros2_control、controllers.yaml joint name 是否一致 |
| `matlab/build_simscape_model.m` | 程序化创建 Simscape Multibody Plant |
| `matlab/build_controller_model.m` | 程序化创建 Simulink 控制器模型 |
| `matlab/run_closed_loop_sim.m` | 运行闭环仿真 |
| `docs/interface_contract.md` | 记录工程接口契约 |
| `docs/known_estimated_parameters.md` | 记录估算参数和后续替换建议 |

---

## 16. Simulink / Simscape 生成规则

如果目标平台包含 MATLAB、Simulink 或 Simscape，生成 skill 应遵守以下规则。

### 16.1 不假装生成 `.slx`

如果当前环境不能可靠生成二进制 `.slx` 文件，应该生成 MATLAB `.m` 脚本，用脚本程序化构建模型。

正确做法：

```text
生成 matlab/build_simscape_model.m
生成 matlab/build_controller_model.m
生成 matlab/run_closed_loop_sim.m
在 README 中说明如何在 MATLAB 里运行这些脚本生成模型
```

错误做法：

```text
声称已经生成 valid_model.slx，但实际只是文本占位或空文件
```

---

### 16.2 Plant 输入输出必须明确

Simscape Multibody Plant 至少要明确：

| 内容 | 示例 |
|---|---|
| Plant 输入 | effort / velocity / position / motor_speed |
| Plant 输出 | q / dq / odom / imu / contact / pose |
| 驱动方式 | torque-driven / motion-driven |
| sensing | position sensing / velocity sensing |
| 接口转换 | Simulink-PS Converter / PS-Simulink Converter |

机械臂 effort control 示例：

```text
Controller 输出 tau_cmd
    ↓
Simulink-PS Converter
    ↓
Joint Torque Actuation
    ↓
Simscape Multibody Plant
    ↓
Joint Position / Velocity Sensing
    ↓
PS-Simulink Converter
    ↓
q, dq feedback
```

---

### 16.3 不允许假动力学

如果需求写的是：

```yaml
simulation:
  plant_input: effort
  simscape:
    torque_driven: true
```

那么生成结果不能用：

```text
输入 q_des，直接驱动关节位置变化
```

因为这只是 motion-driven 或动画式仿真，不是 effort-driven 动力学仿真。

---

## 17. ROS2 / ros2_control 生成规则

### 17.1 每个可控 joint 必须定义接口

每个可控 joint 都要有：

```yaml
command_interfaces: [...]
state_interfaces: [...]
```

示例：

```yaml
ros2_control:
  joints:
    - name: elbow_joint
      command_interfaces: [effort]
      state_interfaces: [position, velocity, effort]
```

---

### 17.2 controller 类型要和接口匹配

| 机器人 | 推荐接口 | 推荐 controller |
|---|---|---|
| 差速小车 | wheel velocity | `diff_drive_controller` |
| 机械臂 position control | position | `joint_trajectory_controller` |
| 机械臂 effort control | effort | `joint_trajectory_controller` 或自定义 effort controller |
| 腿式机器人 | effort | effort controllers / custom controller |
| 云台 | position / velocity | position controller / velocity controller |

---

### 17.3 launch 必须加载完整链路

一个基本仿真 launch 应该包含：

```text
robot_state_publisher
    ↓
robot_description
    ↓
Gazebo spawn_entity
    ↓
controller_manager
    ↓
joint_state_broadcaster
    ↓
target controller
```

验证时可以检查：

```bash
ros2 control list_controllers
ros2 control list_hardware_interfaces
ros2 topic list
ros2 topic echo /joint_states
```

---

## 18. Gazebo 生成规则

如果目标平台包含 Gazebo，通常需要：

- URDF / Xacro 中包含 Gazebo 插件；
- 使用 `gazebo_ros2_control/GazeboSystem` 或目标硬件插件；
- launch 中启动 Gazebo；
- spawn robot entity；
- 加载 controller_manager；
- 加载 joint_state_broadcaster；
- 加载目标 controller；
- 如果有传感器，加载对应 sensor plugin。

差速小车常见接口：

```text
/cmd_vel
/odom
/tf
/joint_states
```

机械臂常见接口：

```text
/joint_states
/joint_trajectory_controller/joint_trajectory
/joint_trajectory_controller/state
```

---

## 19. MoveIt2、Nav2 与本仓库的关系

这个仓库主要负责 **机器人仿真控制工程包生成**，不是专门生成 MoveIt2 或 Nav2 配置的仓库。

但是它可以为 MoveIt2 / Nav2 打基础。

### 19.1 和 MoveIt2 的关系

MoveIt2 依赖：

- 正确的 URDF；
- 正确的 joint limit；
- 正确的 planning group；
- 正确的 `ros2_control` controller；
- 正确的 `joint_trajectory_controller` 接口；
- 正确的 `tool0` / end effector frame。

本仓库可以先生成：

```text
URDF / Xacro
joint limits
ros2_control
controllers.yaml
launch
validation scripts
```

后续再基于这些文件生成 MoveIt2 config。

### 19.2 和 Nav2 的关系

Nav2 依赖：

- `base_link`；
- `odom`；
- `map`；
- `/tf`；
- `/cmd_vel`；
- `/odom`；
- LiDAR 或其他定位感知输入；
- 合理的底盘控制器。

本仓库可以先生成：

```text
移动底盘 URDF
wheel joints
ros2_control
controllers.yaml
diff_drive_controller
odom interface
```

后续再基于这些接口生成 Nav2 config。

### 19.3 移动机械臂推荐架构

```text
Behavior Tree / Task Manager
    ↓
Nav2：移动到底盘目标位姿
    ↓
MoveIt2：机械臂运动到 pre_grasp_pose
    ↓
RL / Servo / Grasp Skill：局部抓取或接触控制
    ↓
ros2_control
    ↓
Gazebo / Simscape / Real Robot
```

这个仓库负责其中的：

```text
机器人模型 + 控制接口 + ros2_control + 仿真 Plant + 验证脚本
```

---

## 20. 验证方式

### 20.1 验证 robot_spec.yaml

安装依赖：

```bash
python3 -m pip install pyyaml
```

运行：

```bash
python3 skills/robot-sim-requirements-intake/scripts/validate_robot_spec.py path/to/robot_spec.yaml
```

如果规格里故意保留了 `source: tbc`，可以使用：

```bash
python3 skills/robot-sim-requirements-intake/scripts/validate_robot_spec.py --allow-tbc path/to/robot_spec.yaml
```

### 20.2 验证生成后的 ROS2 包

进入工作空间：

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

检查 URDF / Xacro：

```bash
ros2 run xacro xacro src/my_robot_sim_control_pkg/urdf/robot.urdf.xacro > /tmp/robot.urdf
check_urdf /tmp/robot.urdf
```

检查 joint states：

```bash
ros2 launch my_robot_sim_control_pkg display.launch.py
ros2 topic echo /joint_states
```

检查 controllers：

```bash
ros2 launch my_robot_sim_control_pkg sim.launch.py
ros2 control list_controllers
ros2 control list_hardware_interfaces
```

运行包内验证脚本：

```bash
python3 src/my_robot_sim_control_pkg/scripts/validate_robot_package.py src/my_robot_sim_control_pkg
```

### 20.3 验证 Simulink / Simscape

在 MATLAB 中进入工程目录：

```matlab
cd matlab
build_simscape_model
build_controller_model
run_closed_loop_sim
```

需要确认：

- Plant 输入是否和控制器输出一致；
- q / dq feedback 是否正常；
- torque-driven 模型是否真的使用 torque actuation；
- 是否存在 joint position / velocity sensing；
- 输出曲线是否符合预期；
- 是否存在饱和、限幅、采样时间设置。

---

## 21. 常用提示词模板

### 21.1 需求整理提示词

```text
请使用 robot-sim-requirements-intake skill，帮我把下面的机器人需求整理成 robot_spec.yaml。

机器人类型：<填写机器人类型>
目标平台：<ROS2 / Gazebo / Simulink / Simscape / ros2_control>
控制目标：<控制算法验证 / ros2_control 部署 / Gazebo 仿真 / MoveIt2 对接 / Nav2 对接>
控制方式：<effort / velocity / position>
仿真方式：<Gazebo / Simscape / 两者都要>

已知结构：
<link / joint / actuator / sensor 信息>

要求：
1. 使用 ROS 坐标系：X forward, Y left, Z up。
2. 输出 robot_spec.yaml。
3. 对未知关键参数使用 source: tbc。
4. 对合理估计参数使用 source: estimated。
5. 不要把 estimated 或 tbc 伪装成真实参数。
6. 列出缺失信息清单。
7. 列出工程风险提醒。
8. 最后给我一份可以直接粘贴给 Codex 的工程生成提示词。
```

---

### 21.2 工程生成提示词

```text
请使用 robot-sim-control-package-generation skill，根据下面的 robot_spec.yaml 生成机器人仿真控制工程包。

要求：
1. 生成完整目录结构，不要只生成 README。
2. 使用 params/robot_spec.yaml 作为单一事实源。
3. 生成 URDF / Xacro。
4. 生成 ros2_control.xacro。
5. 生成 controllers.yaml。
6. 生成 launch 文件。
7. 如果目标平台包含 Gazebo，生成 Gazebo 启动和 gazebo_ros2_control 配置。
8. 如果目标平台包含 Simulink / Simscape，生成 MATLAB .m builder 脚本；如果不能生成真实 .slx，不要假装生成 .slx。
9. 生成验证脚本。
10. 生成 README，包含安装、构建、启动、验证命令。
11. 检查所有 joint name 在 URDF、ros2_control、controllers.yaml、launch、脚本中完全一致。
12. 所有主要 link 必须有 visual、collision、inertial。
13. 不要生成 toy demo，不要生成 fake position animation。

robot_spec.yaml：
<粘贴 robot_spec.yaml>
```

---

### 21.3 工程验证提示词

```text
请使用 robot-sim-control-package-validation skill，检查这个机器人仿真控制包。

重点检查：
1. URDF / Xacro 是否能解析。
2. link 是否都有 visual / collision / inertial。
3. joint 是否有 parent / child / origin / axis / limit / dynamics。
4. URDF、ros2_control、controllers.yaml、launch、脚本中的 joint name 是否一致。
5. actuator 是否引用存在的 joint。
6. sensor 是否引用存在的 link。
7. control.output、simulation.plant_input、ros2_control.command_interfaces 是否一致。
8. Simscape Plant 是否是假 position animation。
9. 是否保留 estimated / tbc 标记。
10. 是否有验证脚本和 README 运行命令。

请按以下结构输出：
1. 总体结论
2. 必修问题
3. 工程质量问题
4. 机器人类型专项问题
5. 建议修复顺序
6. 具体补丁或修改后的文件
7. 验证命令
```

---

## 22. 典型工作流示例

### 22.1 从机械臂想法到工程包

```text
用户：我想做一个 6 自由度机械臂，Simulink 里验证控制算法，ROS2 里用 ros2_control 接 Gazebo。

Step 1：requirements-intake
输出：robot_spec.yaml + 缺失参数

Step 2：用户补充或接受 estimated 参数
输出：更完整的 robot_spec.yaml

Step 3：control-package-generation
输出：ROS2 package + URDF + Simscape builder + controllers.yaml + launch + validation scripts

Step 4：control-package-validation
输出：检查 joint name、Plant 接口、controller 接口、动力学质量

Step 5：根据验证结果修补工程
```

---

### 22.2 从差速小车到 Nav2 基础包

```text
用户：我要生成一个差速小车，能在 Gazebo 里跑，后面要接 Nav2。

Step 1：requirements-intake
明确：wheel_radius、wheel_separation、cmd_vel、odom、diff_drive_controller

Step 2：generation
生成：URDF、ros2_control、diff_drive_controller、Gazebo launch

Step 3：validation
检查：左右轮 axis、轮距、cmd_vel 到 wheel velocity、odom 输出

Step 4：后续扩展
增加：LiDAR、map、Nav2 params、localization、planner/controller 配置
```

---

### 22.3 从生成包到修复补丁

```text
用户：这个包 launch 后 controller 激活失败，帮我检查。

validation skill 应该：
1. 提取 URDF joint names。
2. 提取 ros2_control joint names。
3. 提取 controllers.yaml joint names。
4. 对比差异。
5. 找出缺失或拼写不一致的 joint。
6. 给出具体修改文件和 patch。
7. 给出验证命令。
```

---

## 23. 常见问题

### Q1：这个仓库能直接生成 Simulink `.slx` 文件吗？

不一定。

如果当前运行环境不能可靠生成二进制 `.slx`，skill 应该生成 MATLAB `.m` 脚本，让 MATLAB 程序化创建 Simulink / Simscape 模型。

也就是说，正确输出可能是：

```text
matlab/build_simscape_model.m
matlab/build_controller_model.m
matlab/run_closed_loop_sim.m
```

而不是伪造一个不可用的 `.slx` 文件。

---

### Q2：为什么一定要先生成 robot_spec.yaml？

因为机器人控制工程最怕参数散落和命名不一致。

`robot_spec.yaml` 的作用是让所有文件都从同一个规格派生：

```text
robot_spec.yaml
    ├── URDF / Xacro
    ├── ros2_control.xacro
    ├── controllers.yaml
    ├── Simscape builder
    ├── launch files
    └── validation scripts
```

这样后续验证时也能反向检查所有文件是否一致。

---

### Q3：如果我不知道惯量怎么办？

可以先用估算值，但必须标记：

```yaml
source: estimated
```

并在 README 或 docs 中说明这些参数后续需要替换。

不要把估算惯量当成真实参数。

---

### Q4：如果我有 CAD 或真实机械参数怎么办？

把它们标记为：

```yaml
source: user_provided
```

并尽量提供：

- link 尺寸；
- mass；
- COM；
- inertia matrix；
- joint origin；
- joint axis；
- joint limits；
- actuator limits。

---

### Q5：这个仓库能生成 MoveIt2 配置吗？

当前核心目标不是 MoveIt2 配置生成，而是生成 MoveIt2 所依赖的底层模型和控制接口：

- URDF；
- joint limits；
- ros2_control；
- controllers.yaml；
- `joint_trajectory_controller`；
- `tool0`。

后续可以在此基础上扩展 MoveIt2 config skill。

---

### Q6：这个仓库能生成 Nav2 配置吗？

当前核心目标不是 Nav2 配置生成，但可以生成 Nav2 所依赖的移动底盘基础：

- `base_link`；
- wheel joints；
- diff_drive_controller；
- `/cmd_vel`；
- `/odom`；
- `/tf`。

后续可以扩展 Nav2 config。

---

### Q7：为什么禁止只生成 README？

因为本仓库的目标是工程包生成，不是文档生成。

合格输出至少应该包含：

- 模型文件；
- 控制配置；
- launch；
- 验证脚本；
- README。

README 只是工程的一部分，不是全部。

---

### Q8：estimated 和 tbc 有什么区别？

| 标记 | 含义 |
|---|---|
| `estimated` | 可以先用来推进建模，但必须明确是估算值 |
| `tbc` | 待确认，不应直接当最终参数使用 |

例如：

```yaml
source: estimated
notes: "质量为估计值，后续应替换为实测或 CAD 导出质量。"
```

---

### Q9：为什么说 position-driven Plant 不能伪装 torque control？

因为它们控制含义不同。

如果控制器输出 effort，那么 Plant 应该接收 torque / effort，并由动力学方程产生运动。

如果直接输入目标位置让关节按位置变化，就绕过了动力学，无法验证 torque controller 的真实效果。

---

## 24. 排错指南

### 24.1 Codex 没有使用 skill

现象：

- Codex 直接开始写代码；
- 没有输出 `robot_spec.yaml`；
- 没有缺失信息清单；
- 没有按 skill 的质量门检查。

处理：

```text
请明确使用 robot-sim-requirements-intake skill，不要直接生成工程代码。
```

或者：

```text
请明确使用 robot-sim-control-package-generation skill，根据我提供的 robot_spec.yaml 生成工程包。
```

---

### 24.2 `validate_robot_spec.py` 报 PyYAML 缺失

安装：

```bash
python3 -m pip install pyyaml
```

或者：

```bash
python3 -m pip install -r skills/robot-sim-requirements-intake/requirements.txt
```

---

### 24.3 报 `source: tbc` 未解决

如果你正在需求整理阶段，可以允许 tbc：

```bash
python3 scripts/validate_robot_spec.py --allow-tbc params/robot_spec.yaml
```

如果你已经进入工程生成阶段，建议先补齐关键 tbc 参数，或者明确告诉 Codex：

```text
允许使用 tbc 占位生成第一版工程，但必须在 README 和 docs 中标记为不可用于最终控制验证。
```

---

### 24.4 controller 激活失败

优先检查：

```bash
ros2 control list_hardware_interfaces
ros2 control list_controllers
```

常见原因：

- `controllers.yaml` 中 joint name 和 URDF 不一致；
- ros2_control 中没有定义对应 command interface；
- controller 类型和 command interface 不匹配；
- joint_state_broadcaster 没有先启动；
- Gazebo 插件没有加载；
- robot_description 没有正确传给 controller_manager。

建议使用 validation skill：

```text
请使用 robot-sim-control-package-validation skill，重点检查 URDF、ros2_control.xacro、controllers.yaml 中 joint name 和 interfaces 是否一致。
```

---

### 24.5 Gazebo 中机器人只显示但不能动

常见原因：

- 没有加载 ros2_control 插件；
- controller 没有 active；
- command topic 发错；
- joint command interface 不匹配；
- joint limit / effort limit 太小；
- Gazebo physics 或 joint damping 设置异常。

检查：

```bash
ros2 control list_controllers
ros2 control list_hardware_interfaces
ros2 topic list
ros2 topic echo /joint_states
```

---

### 24.6 RViz 能显示，但 TF 或 joint state 不对

常见原因：

- robot_state_publisher 没有启动；
- `/joint_states` 没有发布；
- joint_state_broadcaster 没有启动；
- URDF joint 名称和 controller joint 名称不一致；
- fixed joint / moving joint 定义错误。

检查：

```bash
ros2 topic echo /joint_states
ros2 run tf2_tools view_frames
```

---

### 24.7 Simscape 模型能动，但不像真实动力学

检查：

- 是否是 torque-driven；
- 是否使用真实 mass / inertia；
- 是否有 damping / friction；
- 是否使用 position input 直接驱动关节；
- 控制器输出是否经过 Simulink-PS Converter；
- Plant 输出是否通过 PS-Simulink Converter 回到控制器。

如果要求 effort control，但模型是 position-driven，应判定为 Major 或 Blocker 问题。

---

## 25. 维护与扩展建议

### 25.1 增加新的机器人类型

如果要支持新的机器人类型，建议同时修改：

```text
references/robot_type_appendix.md
references/validation_checklist.md
references/robot_spec_schema.md
assets/example_<robot_type>_robot_spec.yaml
```

并在三个 skill 的 `SKILL.md` 中补充触发描述。

---

### 25.2 增加新的生成目标

例如要支持 Isaac Sim、MuJoCo、Webots，可以扩展：

```yaml
project:
  target_platforms:
    simulation:
      - mujoco
      - isaac_sim
      - webots
```

然后补充：

- 对应仿真器的模型输出规则；
- Plant 输入输出契约；
- 传感器插件或接口；
- 验证脚本；
- 示例 robot_spec。

---

### 25.3 增加 MoveIt2 skill

可以新建：

```text
skills/robot-sim-moveit2-config-generation/
```

它应该依赖已有的：

- URDF / Xacro；
- joint limits；
- ros2_control；
- controllers.yaml；
- `tool0`；
- planning group 定义。

输出：

- SRDF；
- kinematics.yaml；
- joint_limits.yaml；
- moveit_controllers.yaml；
- planning pipelines；
- demo.launch.py。

---

### 25.4 增加 Nav2 skill

可以新建：

```text
skills/robot-sim-nav2-config-generation/
```

它应该依赖已有的：

- `base_link`；
- `odom`；
- `/tf`；
- `/cmd_vel`；
- `/odom`；
- LiDAR / depth / localization 输入；
- diff_drive_controller 或底盘控制器。

输出：

- nav2 params；
- map / localization 配置；
- lifecycle launch；
- RViz config；
- bringup launch；
- smoke test。

---

### 25.5 README 更新原则

README 应保持三个层次：

1. 用户怎么安装；
2. 用户怎么使用；
3. 用户需要给什么信息，最终会生成什么。

如果 skill 规则发生变化，README 也应该同步更新以下部分：

- 三个 skill 分工；
- 输入信息清单；
- robot_spec schema；
- 输出文件结构；
- 验证命令；
- 常见问题。

---

## 总结

这个仓库的核心思想可以压缩成一句话：

```text
先把机器人结构和接口整理成 robot_spec.yaml，再让 Codex 生成工程，最后用 validation skill 检查工程是否真的可运行、可维护、可验证。
```

它适合用来生成和检查：

- ROS2 / Gazebo 机器人仿真包；
- Simulink / Simscape 控制验证工程；
- ros2_control 配置；
- controllers.yaml；
- launch 文件；
- 验证脚本；
- 面向机械臂、小车、腿式机器人、无人机、云台等机器人的工程化规格。

如果你只是想快速看一个模型动起来，这个仓库可能显得“要求太多”。

但如果你的目标是后续接 MoveIt2、Nav2、Simulink 控制器、ros2_control，甚至迁移到真实机器人，那么这些约束就是必要的工程地基。
