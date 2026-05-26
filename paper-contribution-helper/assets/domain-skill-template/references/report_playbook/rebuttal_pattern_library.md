# Rebuttal Pattern Library

The rebuttal library must help authors defend strongly without overclaiming.

## Effective Patterns

### Setting Boundary Defense

Use when a reviewer asks for a broader setting than the paper claims.

Strong posture: clarify the resource or protocol boundary and show why the current claim is scoped.

### Constraint-Driven Coupling Defense

Use when a reviewer says the method is A+B/C.

Strong posture: acknowledge that primitives may be known, then explain why the coupling is forced by the target constraint.

### Failure-Mode Evidence Defense

Use when mechanism evidence is questioned.

Strong posture: connect existing ablations, robustness tests, or appendix evidence to the failure mode. Avoid saying "proves" unless direct proof exists.

### Fair Comparison Contract

Use when baseline fairness is questioned.

Strong posture: separate same-contract baselines from diagnostic baselines with extra resources.

### Existing-Evidence Resurfacing

Use when the evidence is present but not visible to the reviewer.

Strong posture: point to existing tables, figures, ablations, or appendix material and state how the manuscript will reorganize them.

## Dangerous Patterns

- only saying "we clarify";
- only promising camera-ready changes;
- vague future work without current boundary;
- saying a baseline is unfair without explaining the comparison contract;
- over-self-downgrading as "incremental";
- turning a future-boundary hook into a completed contribution;
- saying ablation "proves" mechanism when it only supports it.
