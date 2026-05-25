"""Core propulsion model data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MotorSpec:
    """Motor electrical parameters.

    Units:
    - kv_rpm_per_v: RPM / V
    - resistance_ohm: ohm
    - no_load_current_a: A
    - current_max_a: A
    """

    kv_rpm_per_v: float
    resistance_ohm: float
    no_load_current_a: float
    current_max_a: float
    back_emf_scale: float = 1.0


@dataclass(frozen=True)
class BatterySpec:
    """Battery pack parameters.

    Units:
    - voltage_v: V
    - discharge_efficiency: 0-1
    """

    voltage_v: float
    discharge_efficiency: float = 1.0


@dataclass(frozen=True)
class ESCSpec:
    """ESC efficiency model.

    Units:
    - efficiency: 0-1
    """

    efficiency: float = 1.0


@dataclass(frozen=True)
class PropellerSpec:
    """Propeller geometry.

    Units:
    - diameter_m: m
    - pitch_m: m (optional)
    """

    diameter_m: float
    blade_count: int = 2
    pitch_m: Optional[float] = None


@dataclass(frozen=True)
class OperatingPoint:
    """Solved operating point for a given condition."""

    rpm: float
    advance_ratio: float
    ct: float
    cp: float
    thrust_n: float
    torque_nm: float
    shaft_power_w: float
    motor_power_w: float
    battery_power_w: float
    motor_current_a: float
    motor_voltage_v: float
    is_feasible: bool
    infeasible_reason: Optional[str] = None
