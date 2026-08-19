# CompanyGameAgent

Local execution worker for CompanyGameV2. The supported workflow is a GitHub-backed task queue: ChatGPT writes a task JSON into `agent-queue/pending/`, this worker pulls it, runs Cline against the requested Unity project, and publishes the verified Cline result into `agent-results/`.

## Architecture

```text
ChatGPT
   |
   | creates JSON on GitHub
   v
agent-queue/pending/
   |
   | local watcher: git pull
   v
CompanyGameAgent / github_agent_watcher.py
   |
   v
Cline CLI (--json)
   |
   v
Unity MCP
   |
   v
Unity project
   |
   | result JSON
   v
agent-results/
   |
   | git push
   v
GitHub -> ChatGPT
```

## Local setup

1. Pull the branch `agent/cline-bridge-impl12` into `D:\CompanyGameV2Agent`.
2. Make sure `cline.cmd --help` works and the Cline CLI has the Unity MCP server configured.
3. Make sure the local checkout is clean (`git status` should show no changes). The watcher intentionally refuses to overwrite uncommitted local work.
4. From `CompanyGameAgent`, run `StartGitHubAgent.bat` once and leave that window running.

The watcher polls GitHub every 5 seconds by default. Override with `AGENT_POLL_SECONDS`. The branch defaults to `agent/cline-bridge-impl12`; override with `AGENT_BRANCH` if the worker is moved to another branch.

## Task format

A task is a JSON file under `agent-queue/pending/`:

```json
{
  "id": "unique-task-id",
  "goal": "Perform the requested change in Unity.",
  "project_path": "D:/CompanyGameV2Unity",
  "validation": [
    "Verify the change through Unity MCP.",
    "Do not claim success without verification."
  ],
  "auto_approve": true,
  "thinking": "high",
  "retries": 3
}
```

The watcher moves claimed tasks to `agent-queue/processing/`, runs Cline, then writes `agent-results/<task-id>.json` and removes the processing file.

## Important limitation

The watcher is local software, so the PC must be running, connected to GitHub, and have the watcher window running. ChatGPT does not directly execute processes on the PC; GitHub is the handoff channel.

Never put API keys or other secrets into task JSON or committed files.
