# generate_simulink_pkg.skills

Codex skills for generating and validating engineering-grade robot simulation and control packages.

This repository contains three installable skills:

| Skill | Use when | Main output |
|---|---|---|
| `robot-sim-requirements-intake` | Turn rough robot ideas into structured requirements | `robot_spec.yaml`, missing-information checklist, final Codex prompt |
| `robot-sim-control-package-generation` | Generate a package from `robot_spec.yaml` | ROS2/Gazebo/Simscape/Simulink/ros2_control package files |
| `robot-sim-control-package-validation` | Review an existing generated package | Findings, fix plan, validation commands, optional patches |

## Install From GitHub

In Codex, ask:

```text
Install the skills from liuguoqingdq/generate_simulink_pkg.skills:
- skills/robot-sim-requirements-intake
- skills/robot-sim-control-package-generation
- skills/robot-sim-control-package-validation
```

Or use the installer script directly:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo liuguoqingdq/generate_simulink_pkg.skills \
  --path skills/robot-sim-requirements-intake \
  --path skills/robot-sim-control-package-generation \
  --path skills/robot-sim-control-package-validation
```

Restart Codex after installing so the new skills are discovered.

## Manual Local Install

```bash
mkdir -p ~/.codex/skills
cp -R skills/robot-sim-requirements-intake ~/.codex/skills/
cp -R skills/robot-sim-control-package-generation ~/.codex/skills/
cp -R skills/robot-sim-control-package-validation ~/.codex/skills/
```

## Typical Workflow

1. Use `robot-sim-requirements-intake` to produce a complete `robot_spec.yaml`.
2. Use `robot-sim-control-package-generation` to generate the engineering package.
3. Use `robot-sim-control-package-validation` to audit naming, topology, dynamics, ros2_control, and simulation contracts.

## Validator Dependency

Each skill includes `scripts/validate_robot_spec.py`. It requires PyYAML:

```bash
python3 -m pip install -r skills/robot-sim-requirements-intake/requirements.txt
python3 skills/robot-sim-requirements-intake/scripts/validate_robot_spec.py path/to/robot_spec.yaml
```

For requirement drafts that intentionally contain unresolved values:

```bash
python3 skills/robot-sim-requirements-intake/scripts/validate_robot_spec.py --allow-tbc path/to/robot_spec.yaml
```

## Repository Layout

```text
skills/
  robot-sim-requirements-intake/
  robot-sim-control-package-generation/
  robot-sim-control-package-validation/
```

The `skills/` directories are already unpacked. They are intended for direct GitHub installation by Codex skill installers.
