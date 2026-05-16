"""Base file for a Raspberry Pi controlled 3-axis servo arm.

This is intentionally only a starting point. The real robot arm model, linkage
geometry, servo part numbers, GPIO pins, and PWM library are still unknown.

Hardware assumption for this first test:
- Raspberry Pi sends the control signals.
- Three small servos move the arm axes.
- Servos are 5V-class motors.
- Servo power should come from a suitable external 5V supply, not from GPIO.
- Raspberry Pi ground and servo power ground must be connected together.

No hardware driver is implemented here yet. Add one only after the exact Pi
library and wiring are chosen.
"""

from dataclasses import dataclass
from time import sleep


@dataclass(frozen=True)
class ServoAxisConfig:
    """Configuration for one servo-driven robot arm axis."""

    name: str
    gpio_pin: int
    min_angle: float = 0.0
    max_angle: float = 180.0
    home_angle: float = 90.0


class ThreeAxisServoArmBase:
    """Small safety-first base for a 3-axis servo arm."""

    def __init__(
        self,
        base_axis: ServoAxisConfig,
        shoulder_axis: ServoAxisConfig,
        elbow_axis: ServoAxisConfig,
        step_delay_seconds: float = 0.05,
    ) -> None:
        self.axes = {
            base_axis.name: base_axis,
            shoulder_axis.name: shoulder_axis,
            elbow_axis.name: elbow_axis,
        }
        self.current_angles = {
            base_axis.name: base_axis.home_angle,
            shoulder_axis.name: shoulder_axis.home_angle,
            elbow_axis.name: elbow_axis.home_angle,
        }
        self.step_delay_seconds = step_delay_seconds
        self.locked_out = True

    def unlock_for_manual_test(self) -> None:
        """Allow movement after the human has checked wiring and workspace."""

        self.locked_out = False

    def lockout(self) -> None:
        """Disable movement requests until a human unlocks the arm again."""

        self.locked_out = True

    def move_axis_to(
        self,
        axis_name: str,
        target_angle: float,
    ) -> None:
        """Move one axis to a bounded target angle."""

        if self.locked_out:
            raise RuntimeError("Arm is locked out. Call unlock_for_manual_test() first.")

        axis = self.axes[axis_name]
        bounded_angle = self._bound_angle(axis, target_angle)
        self._write_servo_angle(axis, bounded_angle)
        self.current_angles[axis_name] = bounded_angle
        sleep(self.step_delay_seconds)

    def move_home(self) -> None:
        """Move all axes to their configured home angles, one at a time."""

        for axis_name, axis in self.axes.items():
            self.move_axis_to(axis_name, axis.home_angle)

    def _bound_angle(
        self,
        axis: ServoAxisConfig,
        target_angle: float,
    ) -> float:
        return max(axis.min_angle, min(axis.max_angle, target_angle))

    def _write_servo_angle(
        self,
        axis: ServoAxisConfig,
        angle: float,
    ) -> None:
        """Replace this placeholder with the chosen Raspberry Pi PWM library."""

        raise NotImplementedError(
            "Choose the Raspberry Pi PWM library and implement servo output for "
            f"GPIO pin {axis.gpio_pin} before running real hardware."
        )


if __name__ == "__main__":
    arm = ThreeAxisServoArmBase(
        base_axis=ServoAxisConfig(name="base", gpio_pin=17),
        shoulder_axis=ServoAxisConfig(name="shoulder", gpio_pin=27),
        elbow_axis=ServoAxisConfig(name="elbow", gpio_pin=22),
    )

    print("Base file loaded. Confirm wiring, choose a PWM library, then implement _write_servo_angle().")
