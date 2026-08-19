# CompanyGameAgent

Local orchestration layer for CompanyGameV2.

## Current milestone: Cline bridge

The first executable adapter invokes the installed Cline CLI in headless JSON mode. Cline CLI supports `--json`, `--cwd`, `--auto-approve`, `--thinking`, `--retries`, and model/provider overrides, making it suitable as a replaceable execution provider. citeturn0search0turn0search1

Architecture:

```text
Task JSON
   |
   v
CompanyGameAgent
   |
   v
Cline CLI (--json)
   |
   v
Cline MCP configuration
   |
   v
Unity MCP / CoplayDev
   |
   v
Unity
```

## Local setup

1. Pull this branch into the local CompanyGameV2 checkout.
2. Ensure `cline.cmd --version` works in PowerShell.
3. Ensure Cline CLI has the same Unity MCP server configured as the working Cline/VS Code setup. Cline CLI supports MCP servers. citeturn0search3
4. Edit `tasks/unity-read-test.json` and set `project_path` to the local Unity project.
5. From `CompanyGameAgent`, run:

```powershell
python run_task.py tasks/unity-read-test.json --auto-approve=false
```

For the first smoke test, keep approval disabled. Once the bridge is verified, autonomous execution can be enabled deliberately with `--auto-approve=true`.

## Design rules

- Provider/adapter based: do not hard-code Cline or CoplayDev into the core task engine.
- Configuration over source-code constants.
- Every task has explicit execution and validation requirements.
- A task is not complete merely because the agent exits successfully; validation must pass.
- Failed validation will feed a bounded repair cycle in the next milestone.
- Never fabricate Unity/test results.
- Secrets and machine-specific paths stay out of source control.
