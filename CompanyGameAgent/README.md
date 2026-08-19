# CompanyGameAgent

Local orchestration layer for CompanyGameV2.

## Purpose

This project is the bridge between an external task producer (eventually ChatGPT), a coding agent (initially Cline CLI), Unity/CoplayDev, validation, and Git.

```text
Task Producer
     |
     v
CompanyGameAgent
     |
     +--> Agent Provider (Cline first; replaceable)
     |
     +--> Validation Provider
     |
     +--> Git Provider
     |
     v
CompanyGameV2 / Unity
```

## Design rules

- Provider/adapter based: do not hard-code Cline or CoplayDev into the core task engine.
- Configuration over source-code constants.
- Every task has explicit execution and validation requirements.
- A task is not complete merely because the agent exits successfully; validation must pass.
- Failed validation produces a repair cycle with bounded attempts.
- Never fabricate Unity/test results. Results must come from executed tools or explicit user input.
- Git is a version-control/reporting boundary, not a required transport layer for every local operation.
- Secrets and machine-specific paths stay out of source control.

## Initial PoC scope

1. Define a machine-readable task format.
2. Define agent/validation/git provider interfaces.
3. Implement a Cline CLI adapter.
4. Implement a local command validation adapter.
5. Persist task state and execution logs.
6. Provide a dry-run mode before enabling autonomous execution.

The Unity/CoplayDev adapter is intentionally represented as an integration boundary first. Actual Unity execution requires the local machine to have Unity, CoplayDev, and Cline configured.
