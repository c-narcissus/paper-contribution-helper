# Positive Reframing Patterns

Use these patterns to turn real but incremental contributions into stronger, evidence-bounded paper stories.

## New Problem Contract

Plain-language meaning: the paper is not just adding a module; it is working under a constraint where old assumptions no longer hold.

Use when: the target PDF has a new resource, privacy, decentralization, label-scarcity, robustness, deployment, or protocol constraint.

Safe output: define what resources are unavailable, what failure appears, and why the proposed design is needed under that contract.

## Hidden Failure Mode

Plain-language meaning: the paper is useful because it identifies a failure that existing methods quietly suffer from.

Use when: the PDF has ablations, stress tests, non-IID splits, label-ratio experiments, topology changes, or subgroup evidence.

Safe output: name the failure mode and bind each module to the failure it repairs.

## Constraint-Driven Coupling

Plain-language meaning: the components may be familiar, but the way they must work together is forced by the target setting.

Use when: the method looks like A+B/C but each component answers a different missing signal or constraint.

Safe output: show pressure -> component -> evidence. Do not claim every primitive is new.

## Evidence-System Contribution

Plain-language meaning: the value is not only the method, but the organized evidence that answers likely reviewer doubts.

Use when: the PDF already has main results, ablation, robustness, appendix, runtime, or protocol details that are not narratively connected.

Safe output: turn tables and figures into a reviewer-question roadmap.

## Future-Boundary Hook

Plain-language meaning: the paper hints at a bigger scientific question, but current evidence only supports a bounded first step.

Use when: the paper suggests a broad conceptual boundary but lacks theory or broad evidence.

Safe output: place it in motivation or discussion, not as a completed main contribution.
