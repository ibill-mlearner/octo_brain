# Spatial Memory Engineering Explanation

This file is intentionally not a user-facing README. It is a technical engineering note for reasoning about the mathematical shape of the spatial memory prototype: what tensors represent, what functions are being approximated, what invariants are desirable, and which parts of the current code are still placeholders for a deeper dynamical system.

The explanations below describe the system we are trying to engineer, not a claim that the current prototype already satisfies every property.

## 1. Core state space

Let the persistent memory field be a channelized 3D tensor:

```text
M_t \in R^{C x X x Y x Z}
```

where:

- `C` is the number of channels per cell;
- `(X, Y, Z)` is the global memory size;
- `t` is the discrete system step.

A node occupies a window whose lower-left-front origin is:

```text
p_t = (x_t, y_t, z_t)
```

with window dimensions:

```text
W = (w_x, w_y, w_z)
```

The visible memory patch is a spatial slice:

```text
P_t = read(M_t, p_t) \in R^{1 x C x w_x x w_y x w_z}
```

The active state is a separate transient tensor:

```text
A_t \in R^{1 x C x w_x x w_y x w_z}
```

The intended separation is:

- `M_t` stores persistent spatial traces;
- `P_t` is the local view of persistence;
- `A_t` is the moving process state that interprets and perturbs that local view.

In other words, the agent state at one step is not only the global field. It is approximately:

```text
S_t = (M_t, A_t, p_t, v_t, r_t)
```

where `v_t` is velocity or recent displacement and `r_t` is the current role-specific context.

## 2. Locality constraint

The system is designed around a locality constraint. The update function should not depend on all of `M_t`; it should depend on only a local patch and local carried state:

```text
F_theta: (A_t, P_t, u_t) -> (A_{t+1}, Delta_t, G_t, m_t, e_t)
```

where:

- `u_t` is optional external input placed into the active state or patch;
- `Delta_t` is a candidate memory write delta;
- `G_t` is a write gate;
- `m_t` is a movement proposal;
- `e_t` is an error, surprise, or pressure signal.

The locality constraint is important because it makes the field more like a physical substrate than a normal fully connected parameter block. A useful local rule should be reusable across positions:

```text
same rule + different patch -> different local behavior
```

This implies translational reuse of update logic while preserving spatially distinct memory content.

## 3. Boundary/interior write model

A node window has a boundary shell and an interior. Let the set of all local window coordinates be:

```text
Omega_W = {0..w_x-1} x {0..w_y-1} x {0..w_z-1}
```

The mutable interior is:

```text
I_W = {1..w_x-2} x {1..w_y-2} x {1..w_z-2}
```

when each dimension is larger than two. The boundary is:

```text
B_W = Omega_W \ I_W
```

The engineering intent is:

```text
B_W: read/context/contact surface
I_W: writeable local workspace
```

A preserve-boundary write can be expressed as:

```text
M_{t+1}[p_t + q] =
    candidate[q]   if q in I_W
    M_t[p_t + q]   if q in B_W
```

This gives the local process a protected sensory surface. The surrounding field can influence the node through the boundary without the node automatically overwriting that boundary every step.

## 4. Memory update equation

A generic gated memory update is:

```text
candidate_t = P_t + G_t ⊙ Delta_t
```

where `⊙` is elementwise multiplication. Written back into global memory:

```text
M_{t+1} = write(M_t, p_t, candidate_t, mask=I_W)
```

A more conservative version includes a write scale `alpha_M`:

```text
candidate_t = P_t + alpha_M * G_t ⊙ Delta_t
```

A bounded-delta variant is:

```text
Delta'_t = tanh(Delta_t)
candidate_t = P_t + alpha_M * G_t ⊙ Delta'_t
```

A bounded-memory variant is:

```text
candidate_t = clamp(candidate_t, -b_M, b_M)
```

Those are not interchangeable design choices:

- scaling controls step size;
- `tanh` controls delta amplitude;
- clamping controls state range;
- gates control where writes occur.

The system should eventually make these choices explicit because each one implies a different memory semantics.

## 5. Active-state update equation

The current conceptual update is residual:

```text
A_{t+1} = A_t + Phi_A(A_t, P_t)
```

where `Phi_A` is a learned local function. A safer recurrent form is:

```text
A_{t+1} = A_t + alpha_A * tanh(Phi_A(A_t, P_t))
```

A bounded-state form is:

```text
A_{t+1} = tanh(A_t + alpha_A * Phi_A(A_t, P_t))
```

These functions mean different things:

- residual unbounded `A_t` treats active state as an accumulator;
- scaled residual `A_t` treats active state as a slow dynamical variable;
- bounded `A_t` treats active state as a normalized signal manifold.

The open engineering question is not merely how to avoid numerical explosion. It is what physical analogy `A_t` should obey. If it is a voltage-like activation, bounded values are natural. If it is a mass/energy accumulation, bounded values may erase meaningful magnitude.

## 6. Prediction as live pressure, not only loss

Let a prediction head estimate either the current patch, the next patch, or a transformed local observation:

```text
hat{P}_{t+k} = H_psi(A_t, P_t)
```

A simple mean squared error is:

```text
E_t = mean((hat{P}_{t+k} - P_{t+k})^2)
```

For normal model training, `E_t` is a loss. In this system, `E_t` is also a live control signal. It can influence:

- reflex triggering;
- movement direction;
- write permission;
- confidence;
- node-to-node messages;
- whether a region should be revisited.

The intended engineering move is to treat prediction error as a spatial pressure field. If an area repeatedly produces high error, the system can mark it, avoid it, inspect it, or allocate more local updates to it.

## 7. Movement function

The movement proposal can be modeled as:

```text
m_t = V_theta(A_t, P_t, E_t, v_t)
```

A discrete next position is:

```text
p_{t+1} = clamp_position(p_t + round(k * m_t))
```

where `k` is the movement radius. A more general movement rule would sample or choose from a local action set:

```text
D = {-1, 0, 1}^3
p_{t+1} = p_t + argmax_{d in D} score(d | A_t, P_t, E_t, v_t)
```

The engineering goal is not just locomotion. Movement determines which memory neighborhoods get computation. That makes movement an attention mechanism over the spatial field.

Useful movement should balance:

- local exploitation of a meaningful region;
- exploration of unknown or stale regions;
- retreat from dangerous/high-urgency regions;
- return to regions with unresolved prediction error;
- coverage of the global field over time.

## 8. Raw sensor projection

A raw sensor stream is a sequence of scalar readings:

```text
s_t = [s_{t,0}, s_{t,1}, ..., s_{t,n-1}]
```

The placement function maps values into local coordinates:

```text
Q: i -> (x_i, y_i, z_i)
```

with the current default ordering filling `x`, then `y`, then `z`:

```text
x_i = i mod w_x
y_i = floor(i / w_x) mod w_y
z_i = floor(i / (w_x * w_y))
```

Then values are written into a frame:

```text
Frame[Q(i)] = normalize(s_{t,i})
```

This is intentionally not semantic tokenization. The function should preserve numerical continuity and placement consistency before the system learns higher-order structure.

## 9. Node-role functions

Each role can be viewed as a constrained function over shared node state.

Sensor role:

```text
A'_t = inject(A_t, normalize(raw_t), placement=Q)
```

Reflex role:

```text
rho_t = urgency(E_t, feedback_t, timeout_t, danger_t)
trigger_t = rho_t > tau
```

Decision role:

```text
a_t = D_phi(summary(A_t), E_t, v_t, messages_t)
```

Actor role:

```text
world_{t+1}, feedback_t = act(world_t, a_t)
```

The role split prevents one monolithic function from owning all responsibilities. Sensor functions inject raw values, reflex functions handle immediate pressure, decision functions arbitrate, and actor functions close the loop through consequences.

## 10. Stability invariants to engineer toward

A recurrent spatial system needs explicit invariants. Candidate invariants include:

```text
finite(A_t) for all t
finite(M_t) for all t
||Delta_t||_infinity <= d_max
0 <= G_t <= 1
p_t inside valid field bounds
writes restricted to I_W unless explicitly allowed
```

If memory is bounded, add:

```text
||M_t||_infinity <= b_M
```

If active state is bounded, add:

```text
||A_t||_infinity <= b_A
```

If neither is bounded, then the system still needs an energy-style condition, such as:

```text
E[||A_{t+1}||^2 - ||A_t||^2] <= epsilon
```

or a decay/normalization mechanism that prevents untrained feedback from dominating.

The key engineering point is that stability should be a declared property, not an accidental outcome of initialization.

## 11. Logging targets for technical runs

A technical run should log enough values to reconstruct the local dynamics:

- `step`;
- `position`;
- `velocity`;
- `patch_mean`, `patch_std`, `patch_abs_max`;
- `active_mean`, `active_std`, `active_abs_max`;
- `delta_mean`, `delta_std`, `delta_abs_max`;
- `gate_mean`, `gate_min`, `gate_max`;
- `prediction_error`;
- `reflex_urgency`;
- `reflex_triggered`;
- `write_back`;
- `boundary_preserved`;
- optional clamp or normalization counters.

Those logs are more important than visual neatness at this stage. Without them, runaway behavior, frozen movement, overactive gates, and destructive writes are hard to distinguish.

## 12. Practical interpretation of the current prototype

The current code is best interpreted as a minimal tensor skeleton for the equations above:

- the global memory tensor implements `M_t`;
- `read_patch` implements local spatial observation;
- `write_patch` implements masked local mutation;
- `LocalUpdateNet` approximates `F_theta`;
- `PredictionHead` approximates `H_psi`;
- `DecisionModule` approximates a small action policy;
- node roles separate sensor, reflex, decision, and actor responsibilities.

The next engineering step is not to make the architecture larger. It is to make the recurrent loop mathematically inspectable: define the numeric ranges, choose explicit update scales or bounds, and test whether repeated steps preserve the intended invariants.
