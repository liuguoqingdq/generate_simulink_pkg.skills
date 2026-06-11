#!/usr/bin/env python3
"""
Static validator for robot_spec.yaml used by robot-sim-control skills.

It checks generation-readiness: schema coverage, topology, dynamics fields,
actuator/sensor references, ros2_control consistency, and unresolved TBC values.
"""
from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


REQUIRED_TOP = [
    "project",
    "frames",
    "links",
    "joints",
    "actuators",
    "control",
    "simulation",
    "ros2_control",
    "validation",
    "forbidden",
]
ALLOWED_ROBOT_TYPES = {
    "diff_drive",
    "four_wheel",
    "ackermann",
    "tracked",
    "arm_6dof",
    "serial_manipulator",
    "biped",
    "quadruped",
    "wheel_legged",
    "mobile_manipulator",
    "uav",
    "gimbal",
}
ALLOWED_JOINT_TYPES = {"fixed", "revolute", "continuous", "prismatic", "floating", "planar"}
ALLOWED_INTERFACES = {"position", "velocity", "effort"}
ALLOWED_SOURCES = {"user_provided", "estimated", "tbc"}
INERTIA_KEYS = ["ixx", "ixy", "ixz", "iyy", "iyz", "izz"]
REQUIRED_VALIDATION_FLAGS = [
    "generate_validate_script",
    "check_urdf",
    "check_joint_name_consistency",
    "check_inertial_collision",
    "check_limits_dynamics",
    "check_interface_contract",
]
REQUIRED_FORBIDDEN = {
    "toy_demo",
    "readme_only",
    "hardcoded_scattered_params",
    "missing_inertial",
    "missing_collision",
    "fake_position_animation",
}


def fail(counts: dict[str, int], msg: str) -> None:
    counts["errors"] += 1
    print(f"[FAIL] {msg}")


def warn(counts: dict[str, int], msg: str) -> None:
    counts["warnings"] += 1
    print(f"[WARN] {msg}")


def ok(msg: str) -> None:
    print(f"[ OK ] {msg}")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_vec3(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 3 and all(is_number(v) for v in value)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        print(
            "ERROR: PyYAML is required to parse robot_spec.yaml.\n"
            "Install with one of:\n"
            "  python3 -m pip install -r requirements.txt\n"
            "  python3 -m pip install pyyaml",
            file=sys.stderr,
        )
        raise SystemExit(2)

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("robot_spec.yaml root must be a mapping")
    return data


def check_source(
    counts: dict[str, int],
    obj: dict[str, Any],
    label: str,
    allow_tbc: bool,
    require_source: bool = False,
) -> None:
    source = obj.get("source")
    if source is None:
        if require_source:
            warn(counts, f"{label} missing source marker")
        return
    if source not in ALLOWED_SOURCES:
        fail(counts, f"{label} has invalid source: {source}")
    elif source == "tbc" and not allow_tbc:
        fail(counts, f"{label} contains unresolved source: tbc")


def infer_interface(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.lower()
    if normalized in ALLOWED_INTERFACES:
        return normalized
    if "effort" in normalized or "torque" in normalized:
        return "effort"
    if "velocity" in normalized or "speed" in normalized:
        return "velocity"
    if "position" in normalized:
        return "position"
    return None


def validate_project(counts: dict[str, int], spec: dict[str, Any]) -> None:
    project = spec.get("project") or {}
    if not isinstance(project, dict):
        fail(counts, "project must be a mapping")
        return
    robot_type = project.get("robot_type")
    if robot_type not in ALLOWED_ROBOT_TYPES:
        fail(counts, f"project.robot_type unsupported or missing: {robot_type}")
    else:
        ok(f"robot type is supported: {robot_type}")


def validate_frames(counts: dict[str, int], spec: dict[str, Any], link_names: set[str]) -> str | None:
    frames = spec.get("frames") or {}
    if not isinstance(frames, dict):
        fail(counts, "frames must be a mapping")
        return None
    base_link = frames.get("base_link")
    if base_link not in link_names:
        fail(counts, f"frames.base_link not defined in links: {base_link}")
    axes = frames.get("axes") or {}
    if not isinstance(axes, dict):
        fail(counts, "frames.axes must be a mapping")
    else:
        for axis in ["x", "y", "z"]:
            if axis not in axes:
                fail(counts, f"frames.axes missing {axis}")
    return base_link if isinstance(base_link, str) else None


def validate_links(
    counts: dict[str, int],
    links: list[Any],
    allow_tbc: bool,
) -> set[str]:
    link_names: set[str] = set()
    for i, link in enumerate(links):
        label = f"links[{i}]"
        if not isinstance(link, dict):
            fail(counts, f"{label} must be a mapping")
            continue
        name = link.get("name")
        if not name:
            fail(counts, f"{label} missing name")
            continue
        label = f"link {name}"
        if name in link_names:
            fail(counts, f"duplicate link name: {name}")
        link_names.add(name)
        check_source(counts, link, label, allow_tbc, require_source=True)

        geom = link.get("geometry")
        if not isinstance(geom, dict):
            fail(counts, f"{label} missing geometry mapping")
        else:
            for part in ["visual", "collision"]:
                if part not in geom:
                    fail(counts, f"{label} missing geometry.{part}")

        inertial = link.get("inertial")
        if not isinstance(inertial, dict):
            fail(counts, f"{label} missing inertial mapping")
            continue
        mass = inertial.get("mass")
        if not is_number(mass) or mass <= 0:
            fail(counts, f"{label} inertial.mass must be a positive number")
        if not is_vec3(inertial.get("com_xyz")):
            fail(counts, f"{label} inertial.com_xyz must be a 3D numeric vector")
        inertia = inertial.get("inertia")
        if isinstance(inertia, dict):
            for key in INERTIA_KEYS:
                if key not in inertia:
                    fail(counts, f"{label} inertial.inertia missing {key}")
                elif not (is_number(inertia[key]) or inertia[key] == "auto"):
                    fail(counts, f"{label} inertial.inertia.{key} must be numeric or auto")
        elif isinstance(inertia, str) and inertia.startswith("auto_"):
            warn(counts, f"{label} uses estimated inertia placeholder: {inertia}")
        else:
            fail(counts, f"{label} inertial.inertia must be a matrix mapping or auto_* placeholder")
    return link_names


def validate_joints(
    counts: dict[str, int],
    joints: list[Any],
    link_names: set[str],
    allow_tbc: bool,
) -> tuple[set[str], dict[str, str], dict[str, list[str]]]:
    joint_names: set[str] = set()
    parent_by_child: dict[str, str] = {}
    graph: dict[str, list[str]] = defaultdict(list)

    for i, joint in enumerate(joints):
        label = f"joints[{i}]"
        if not isinstance(joint, dict):
            fail(counts, f"{label} must be a mapping")
            continue
        name = joint.get("name")
        if not name:
            fail(counts, f"{label} missing name")
            continue
        label = f"joint {name}"
        if name in joint_names:
            fail(counts, f"duplicate joint name: {name}")
        joint_names.add(name)
        check_source(counts, joint, label, allow_tbc, require_source=True)

        jtype = joint.get("type")
        if jtype not in ALLOWED_JOINT_TYPES:
            fail(counts, f"{label} has unsupported type: {jtype}")
        parent = joint.get("parent")
        child = joint.get("child")
        if parent not in link_names:
            fail(counts, f"{label} parent link not defined: {parent}")
        if child not in link_names:
            fail(counts, f"{label} child link not defined: {child}")
        if isinstance(parent, str) and isinstance(child, str) and parent in link_names and child in link_names:
            if child in parent_by_child:
                fail(counts, f"link {child} has multiple parent joints: {parent_by_child[child]} and {name}")
            parent_by_child[child] = name
            graph[parent].append(child)

        for field in ["origin_xyz", "origin_rpy"]:
            if not is_vec3(joint.get(field)):
                fail(counts, f"{label} {field} must be a 3D numeric vector")

        if jtype != "fixed":
            axis = joint.get("axis")
            if not is_vec3(axis):
                fail(counts, f"{label} axis must be a 3D numeric vector")
            else:
                norm = math.sqrt(sum(float(v) * float(v) for v in axis))
                if norm <= 1e-9:
                    fail(counts, f"{label} axis must be non-zero")
                elif not math.isclose(norm, 1.0, rel_tol=1e-3, abs_tol=1e-3):
                    warn(counts, f"{label} axis should be normalized; norm={norm:.4f}")
        elif "limit" in joint:
            warn(counts, f"{label} is fixed but still defines limit")

        limit = joint.get("limit") or {}
        if jtype == "revolute":
            for key in ["lower", "upper", "effort", "velocity"]:
                if key not in limit:
                    fail(counts, f"{label} missing limit.{key}")
        elif jtype == "continuous":
            for key in ["effort", "velocity"]:
                if key not in limit:
                    fail(counts, f"{label} missing limit.{key}")

        if jtype in {"revolute", "continuous", "prismatic"}:
            dynamics = joint.get("dynamics") or {}
            if not isinstance(dynamics, dict):
                fail(counts, f"{label} dynamics must be a mapping")
            else:
                for key in ["damping", "friction"]:
                    if key not in dynamics:
                        warn(counts, f"{label} missing dynamics.{key}")

    return joint_names, parent_by_child, graph


def validate_topology(
    counts: dict[str, int],
    link_names: set[str],
    base_link: str | None,
    graph: dict[str, list[str]],
) -> None:
    if not base_link or base_link not in link_names:
        return

    reachable: set[str] = set()
    queue: deque[str] = deque([base_link])
    while queue:
        link = queue.popleft()
        if link in reachable:
            continue
        reachable.add(link)
        queue.extend(graph.get(link, []))

    unreachable = sorted(link_names - reachable)
    if unreachable:
        fail(counts, f"links are disconnected from {base_link}: {unreachable}")
    else:
        ok("all links are reachable from base_link")

    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(link: str) -> bool:
        if link in visiting:
            return True
        if link in visited:
            return False
        visiting.add(link)
        for child in graph.get(link, []):
            if dfs(child):
                return True
        visiting.remove(link)
        visited.add(link)
        return False

    if dfs(base_link):
        fail(counts, "joint topology contains a cycle")
    else:
        ok("joint topology has no cycle")


def validate_actuators(
    counts: dict[str, int],
    spec: dict[str, Any],
    joint_names: set[str],
    allow_tbc: bool,
) -> dict[str, dict[str, Any]]:
    actuators = spec.get("actuators") or []
    if not isinstance(actuators, list) or not actuators:
        fail(counts, "actuators must be a non-empty list")
        return {}

    by_joint: dict[str, dict[str, Any]] = {}
    expected_interface = infer_interface((spec.get("control") or {}).get("output"))

    for i, actuator in enumerate(actuators):
        label = f"actuators[{i}]"
        if not isinstance(actuator, dict):
            fail(counts, f"{label} must be a mapping")
            continue
        name = actuator.get("name") or label
        label = f"actuator {name}"
        check_source(counts, actuator, label, allow_tbc, require_source=True)
        joint = actuator.get("joint")
        if joint not in joint_names:
            fail(counts, f"{label} references undefined joint: {joint}")
        elif isinstance(joint, str):
            by_joint[joint] = actuator

        command = actuator.get("command_interface")
        if command not in ALLOWED_INTERFACES:
            fail(counts, f"{label} command_interface invalid: {command}")
        elif expected_interface and command != expected_interface:
            fail(counts, f"{label} command_interface {command} does not match control.output {expected_interface}")

        states = actuator.get("state_interfaces")
        if not isinstance(states, list) or not states:
            fail(counts, f"{label} state_interfaces must be a non-empty list")
        else:
            invalid = sorted(set(states) - ALLOWED_INTERFACES)
            if invalid:
                fail(counts, f"{label} has invalid state_interfaces: {invalid}")
    return by_joint


def validate_sensors(
    counts: dict[str, int],
    spec: dict[str, Any],
    link_names: set[str],
    allow_tbc: bool,
) -> None:
    sensors = spec.get("sensors", [])
    if sensors in (None, []):
        return
    if not isinstance(sensors, list):
        fail(counts, "sensors must be a list when present")
        return
    for i, sensor in enumerate(sensors):
        label = f"sensors[{i}]"
        if not isinstance(sensor, dict):
            fail(counts, f"{label} must be a mapping")
            continue
        name = sensor.get("name") or label
        label = f"sensor {name}"
        check_source(counts, sensor, label, allow_tbc, require_source=False)
        for key in ["link", "parent"]:
            value = sensor.get(key)
            if value is not None and value not in link_names:
                fail(counts, f"{label} {key} references undefined link: {value}")
        for field in ["origin_xyz", "origin_rpy"]:
            if field in sensor and not is_vec3(sensor.get(field)):
                fail(counts, f"{label} {field} must be a 3D numeric vector")


def validate_ros2_control(
    counts: dict[str, int],
    spec: dict[str, Any],
    joint_names: set[str],
    actuators_by_joint: dict[str, dict[str, Any]],
) -> None:
    rc = spec.get("ros2_control") or {}
    if not isinstance(rc, dict):
        fail(counts, "ros2_control must be a mapping")
        return
    rc_joints = rc.get("joints") or []
    if not isinstance(rc_joints, list) or not rc_joints:
        fail(counts, "ros2_control.joints must be a non-empty list")
        return

    rc_joint_names: set[str] = set()
    for i, item in enumerate(rc_joints):
        label = f"ros2_control.joints[{i}]"
        if not isinstance(item, dict):
            fail(counts, f"{label} must be a mapping")
            continue
        name = item.get("name")
        if name not in joint_names:
            fail(counts, f"{label} references undefined joint: {name}")
            continue
        rc_joint_names.add(name)

        commands = set(as_list(item.get("command_interfaces")))
        states = set(as_list(item.get("state_interfaces")))
        if not commands:
            fail(counts, f"ros2_control joint {name} missing command_interfaces")
        if not states:
            fail(counts, f"ros2_control joint {name} missing state_interfaces")
        invalid = (commands | states) - ALLOWED_INTERFACES
        if invalid:
            fail(counts, f"ros2_control joint {name} has invalid interfaces: {sorted(invalid)}")

        actuator = actuators_by_joint.get(name)
        if actuator:
            command = actuator.get("command_interface")
            actuator_states = set(as_list(actuator.get("state_interfaces")))
            if command not in commands:
                fail(counts, f"ros2_control joint {name} missing actuator command interface: {command}")
            missing_states = actuator_states - states
            if missing_states:
                fail(counts, f"ros2_control joint {name} missing actuator state interfaces: {sorted(missing_states)}")

    missing_rc = sorted(set(actuators_by_joint) - rc_joint_names)
    if missing_rc:
        fail(counts, f"actuator joints missing from ros2_control: {missing_rc}")
    else:
        ok("ros2_control covers all actuator joints")


def validate_contract_sections(counts: dict[str, int], spec: dict[str, Any]) -> None:
    simulation = spec.get("simulation") or {}
    if not isinstance(simulation, dict):
        fail(counts, "simulation must be a mapping")
    else:
        for key in ["plant_input", "plant_output"]:
            if key not in simulation:
                fail(counts, f"simulation missing {key}")
        for key in ["dynamic_simulation_required", "collision_required", "inertial_required"]:
            if simulation.get(key) is not True:
                fail(counts, f"simulation.{key} must be true")
        expected = infer_interface((spec.get("control") or {}).get("output"))
        plant_input = infer_interface(simulation.get("plant_input"))
        if expected and plant_input and expected != plant_input:
            fail(counts, f"simulation.plant_input {plant_input} does not match control.output {expected}")

    validation = spec.get("validation") or {}
    if not isinstance(validation, dict):
        fail(counts, "validation must be a mapping")
    else:
        for key in REQUIRED_VALIDATION_FLAGS:
            if validation.get(key) is not True:
                fail(counts, f"validation.{key} must be true")

    forbidden = spec.get("forbidden") or []
    if not isinstance(forbidden, list):
        fail(counts, "forbidden must be a list")
    else:
        missing = sorted(REQUIRED_FORBIDDEN - set(forbidden))
        if missing:
            fail(counts, f"forbidden missing required items: {missing}")

    outputs = spec.get("outputs") or {}
    if outputs and not isinstance(outputs, dict):
        fail(counts, "outputs must be a mapping when present")
    elif isinstance(outputs, dict):
        required_files = outputs.get("required_files")
        if required_files is not None and not isinstance(required_files, list):
            fail(counts, "outputs.required_files must be a list")


def validate(spec: dict[str, Any], allow_tbc: bool = False) -> int:
    counts = {"errors": 0, "warnings": 0}

    for key in REQUIRED_TOP:
        if key not in spec:
            fail(counts, f"missing top-level key: {key}")
        else:
            ok(f"top-level key exists: {key}")

    validate_project(counts, spec)

    links = spec.get("links") or []
    joints = spec.get("joints") or []
    if not isinstance(links, list) or not links:
        fail(counts, "links must be a non-empty list")
        links = []
    if not isinstance(joints, list):
        fail(counts, "joints must be a list")
        joints = []

    link_names = validate_links(counts, links, allow_tbc)
    base_link = validate_frames(counts, spec, link_names)
    joint_names, _parent_by_child, graph = validate_joints(counts, joints, link_names, allow_tbc)
    validate_topology(counts, link_names, base_link, graph)
    actuators_by_joint = validate_actuators(counts, spec, joint_names, allow_tbc)
    validate_sensors(counts, spec, link_names, allow_tbc)
    validate_ros2_control(counts, spec, joint_names, actuators_by_joint)
    validate_contract_sections(counts, spec)

    print(f"\nValidation completed with {counts['errors']} error(s), {counts['warnings']} warning(s).")
    return 1 if counts["errors"] else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a robot_spec.yaml before generating a robot simulation/control package.",
        epilog=(
            "Dependency: PyYAML. Install with `python3 -m pip install -r requirements.txt` "
            "or `python3 -m pip install pyyaml`."
        ),
    )
    parser.add_argument("spec", nargs="?", help="Path to robot_spec.yaml")
    parser.add_argument(
        "--allow-tbc",
        action="store_true",
        help="Allow source: tbc for requirement-intake drafts. Generation-ready specs should not use this.",
    )
    args = parser.parse_args()

    if not args.spec:
        parser.print_help()
        return 2

    path = Path(args.spec)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    return validate(load_yaml(path), allow_tbc=args.allow_tbc)


if __name__ == "__main__":
    raise SystemExit(main())
