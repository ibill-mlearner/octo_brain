import torch

from spatial_memory_system import SpatialMemorySystem
from node_roles import NodeRoleServer


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    core = SpatialMemorySystem(channels=8, field_size=(100, 100, 100), window_size=(10, 10, 10), movement_mode="learned").to(device)

    roles = NodeRoleServer(core)
    sensor = roles.connect("sensor", node_id="sensor-1")
    reflex = roles.connect("reflex", node_id="reflex-1")
    decision = roles.connect("decision", node_id="decision-1")
    actor = roles.connect("actor", node_id="actor-1")

    for step in range(500):
        sensor.sync_from(actor)
        decision.sync_from(actor)
        patch, pred = sensor.sense_and_predict()
        error = float((pred - patch).pow(2).mean().detach().item())

        trigger, urgency = reflex.check(error)
        action = decision.decide(error)
        if trigger:
            action = -actor.velocity if torch.norm(actor.velocity) > 0 else torch.zeros(3, device=actor.position.device)

        feedback = actor.act(action)
        actor.active_state, _, _ = core.step(actor.active_state, actor.position, write_back=True)

        if step % 50 == 0 or trigger:
            print(f"step={step:03d} role=sensor error={error:.5f} role=reflex urgency={urgency:.3f} trigger={trigger} role=actor feedback={feedback:.3f}")


if __name__ == "__main__":
    main()
