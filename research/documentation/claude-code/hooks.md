<!-- source: https://code.claude.com/docs/en/hooks.md · fetched: 2026-04-18 -->
# Hooks reference

> Reference for Claude Code hook events, configuration schema, JSON input/output formats, exit codes, async hooks, HTTP hooks, prompt hooks, and MCP tool hooks.

<Tip>
  For a quickstart guide with examples, see [Automate workflows with hooks](/en/hooks-guide).
</Tip>

Hooks are user-defined shell commands, HTTP endpoints, or LLM prompts that execute automatically at specific points in Claude Code's lifecycle. Use this reference to look up event schemas, configuration options, JSON input/output formats, and advanced features like async hooks, HTTP hooks, and MCP tool hooks. If you're setting up hooks for the first time, start with the [guide](/en/hooks-guide) instead.

## Hook lifecycle

Hooks fire at specific points during a Claude Code session. When an event fires and a matcher matches, Claude Code passes JSON context about the event to your hook handler. For command hooks, input arrives on stdin. For HTTP hooks, it arrives as the POST request body. Your handler can then inspect the input, take action, and optionally return a decision. Events fall into three cadences: once per session (`SessionStart`, `SessionEnd`), once per turn (`UserPromptSubmit`, `Stop`, `StopFailure`), and on every tool call inside the agentic loop (`PreToolUse`, `PostToolUse`):

<div style={{maxWidth: "500px", margin: "0 auto"}}>
  <Frame>
    <img src="https://mintcdn.com/claude-code/UMJp-WgTWngzO609/images/hooks-lifecycle.svg?fit=max&auto=format&n=UMJp-WgTWngzO609&q=85&s=3f4de67df216c87dc313943b32c15f62" alt="Hook lifecycle diagram showing SessionStart, then a per-turn loop containing UserPromptSubmit, the nested agentic loop (PreToolUse, PermissionRequest, PostToolUse, SubagentStart/Stop, TaskCreated, TaskCompleted), and Stop or StopFailure, followed by TeammateIdle, PreCompact, PostCompact, and SessionEnd, with Elicitation and ElicitationResult nested inside MCP tool execution, PermissionDenied as a side branch from PermissionRequest for auto-mode denials, and WorktreeCreate, WorktreeRemove, Notification, ConfigChange, InstructionsLoaded, CwdChanged, and FileChanged as standalone async events" width="520" height="1155" data-path="images/hooks-lifecycle.svg" />
  </Frame>
</div>

The table below summarizes when each event fires. The [Hook events](#hook-events) section documents the full input schema and decision control options for each one.

| Event                | When it fires                                                                                                                                          |
| :------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SessionStart`       | When a session begins or resumes                                                                                                                       |
| `UserPromptSubmit`   | When you submit a prompt, before Claude processes it                                                                                                   |
| `PreToolUse`         | Before a tool call executes. Can block it                                                                                                              |
| `PermissionRequest`  | When a permission dialog appears                                                                                                                       |
| `PermissionDenied`   | When a tool call is denied by the auto mode classifier. Return `{retry: true}` to tell the model it may retry the denied tool call                     |
| `PostToolUse`        | After a tool call succeeds                                                                                                                             |
| `PostToolUseFailure` | After a tool call fails                                                                                                                                |
| `Notification`       | When Claude Code sends a notification                                                                                                                  |
| `SubagentStart`      | When a subagent is spawned                                                                                                                             |
| `SubagentStop`       | When a subagent finishes                                                                                                                               |
| `TaskCreated`        | When a task is being created via `TaskCreate`                                                                                                          |
| `TaskCompleted`      | When a task is being marked as completed                                                                                                               |
| `Stop`               | When Claude finishes responding                                                                                                                        |
| `StopFailure`        | When the turn ends due to an API error. Output and exit code are ignored                                                                               |
| `TeammateIdle`       | When an [agent team](/en/agent-teams) teammate is about to go idle                                                                                     |
| `InstructionsLoaded` | When a CLAUDE.md or `.claude/rules/*.md` file is loaded into context. Fires at session start and when files are lazily loaded during a session         |
| `ConfigChange`       | When a configuration file changes during a session                                                                                                     |
| `CwdChanged`         | When the working directory changes, for example when Claude executes a `cd` command. Useful for reactive environment management with tools like direnv |
| `FileChanged`        | When a watched file changes on disk. The `matcher` field specifies which filenames to watch                                                            |
| `WorktreeCreate`     | When a worktree is being created via `--worktree` or `isolation: "worktree"`. Replaces default git behavior                                            |
| `WorktreeRemove`     | When a worktree is being removed, either at session exit or when a subagent finishes                                                                   |
| `PreCompact`         | Before context compaction                                                                                                                              |
| `PostCompact`        | After context compaction completes                                                                                                                     |
| `Elicitation`        | When an MCP server requests user input during a tool call                                                                                              |
| `ElicitationResult`  | After a user responds to an MCP elicitation, before the response is sent back to the server                                                            |
| `SessionEnd`         | When a session terminates                                                                                                                              |

### How a hook resolves

To see how these pieces fit together, consider this `PreToolUse` hook that blocks destructive shell commands. The `matcher` narrows to Bash tool calls and the `if` condition narrows further to commands starting with `rm`, so `block-rm.sh` only spawns when both filters match:

```json theme={null}
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(rm *)",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-rm.sh"
          }
        ]
      }
    ]
  }
}
```

The script reads the JSON input from stdin, extracts the command, and returns a `permissionDecision` of `"deny"` if it contains `rm -rf`:

```bash theme={null}
#!/bin/bash
# .claude/hooks/block-rm.sh
COMMAND=$(jq -r '.tool_input.command')

if echo "$COMMAND" | grep -q 'rm -rf'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Destructive command blocked by hook"
    }
  }'
else
  exit 0  # allow the command
fi
```

Now suppose Claude Code decides to run `Bash "rm -rf /tmp/build"`. Here's what happens:

<Frame>
  <img src="https://mintcdn.com/claude-code/-tYw1BD_DEqfyyOZ/images/hook-resolution.svg?fit=max&auto=format&n=-tYw1BD_DEqfyyOZ&q=85&s=c73ebc1eeda2037570427d7af1e0a891" alt="Hook resolution flow: PreToolUse event fires, matcher checks for Bash match, if condition checks for Bash(rm *) match, hook handler runs, result returns to Claude Code" width="930" height="290" data-path="images/hook-resolution.svg" />
</Frame>

<Steps>
  <Step title="Event fires">
    The `PreToolUse` event fires. Claude Code sends the tool input as JSON on stdin to the hook:

    ```json theme={null}
    { "tool_name": "Bash", "tool_input": { "command": "rm -rf /tmp/build" }, ... }
    ```
  </Step>

  <Step title="Matcher checks">
    The matcher `"Bash"` matches the tool name, so this hook group activates. If you omit the matcher or use `"*"`, the group activates on every occurrence of the event.
  </Step>

  <Step title="If condition checks">
    The `if` condition `"Bash(rm *)"` matches because the command starts with `rm`, so this handler spawns. If the command had been `npm test`, the `if` check would fail and `block-rm.sh` would never run, avoiding the process spawn overhead. The `if` field is optional; without it, every handler in the matched group runs.
  </Step>

  <Step title="Hook handler runs">
    The script inspects the full command and finds `rm -rf`, so it prints a decision to stdout:

    ```json theme={null}
    {
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Destructive command blocked by hook"
      }
    }
    ```

    If the command had been a safer `rm` variant like `rm file.txt`, the script would hit `exit 0` instead, which tells Claude Code to allow the tool call with no further action.
  </Step>

  <Step title="Claude Code acts on the result">
    Claude Code reads the JSON decision, blocks the tool call, and shows Claude the reason.
  </Step>
</Steps>

The [Configuration](#configuration) section below documents the full schema, and each [hook event](#hook-events) section documents what input your command receives and what output it can return.

## Configuration

Hooks are defined in JSON settings files. The configuration has three levels of nesting:

1. Choose a [hook event](#hook-events) to respond to, like `PreToolUse` or `Stop`
2. Add a [matcher group](#matcher-patterns) to filter when it fires, like "only for the Bash tool"
3. Define one or more [hook handlers](#hook-handler-fields) to run when matched

See [How a hook resolves](#how-a-hook-resolves) above for a complete walkthrough with an annotated example.

<Note>
  This page uses specific terms for each level: **hook event** for the lifecycle point, **matcher group** for the filter, and **hook handler** for the shell command, HTTP endpoint, prompt, or agent that runs. "Hook" on its own refers to the general feature.
</Note>

### Hook locations

Where you define a hook determines its scope:

| Location                                                   | Scope                         | Shareable                          |
| :--------------------------------------------------------- | :---------------------------- | :--------------------------------- |
| `~/.claude/settings.json`                                  | All your projects             | No, local to your machine          |
| `.claude/settings.json`                                    | Single project                | Yes, can be committed to the repo  |
| `.claude/settings.local.json`                              | Single project                | No, gitignored                     |
| Managed policy settings                                    | Organization-wide             | Yes, admin-controlled              |
| [Plugin](/en/plugins) `hooks/hooks.json`                   | When plugin is enabled        | Yes, bundled with the plugin       |
| [Skill](/en/skills) or [agent](/en/sub-agents) frontmatter | While the component is active | Yes, defined in the component file |

For details on settings file resolution, see [settings](/en/settings). Enterprise administrators can use `allowManagedHooksOnly` to block user, project, and plugin hooks. Hooks from plugins force-enabled in managed settings `enabledPlugins` are exempt, so administrators can distribute vetted hooks through an organization marketplace. See [Hook configuration](/en/settings#hook-configuration).

### Matcher patterns

The `matcher` field filters when hooks fire. How a matcher is evaluated depends on the characters it contains:

| Matcher value                       | Evaluated as                                          | Example                                                                                                            |
| :---------------------------------- | :---------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------- |
| `"*"`, `""`, or omitted             | Match all                                             | fires on every occurrence of the event                                                                             |
| Only letters, digits, `_`, and `\|` | Exact string, or `\|`-separated list of exact strings | `Bash` matches only the Bash tool; `Edit\|Write` matches either tool exactly                                       |
| Contains any other character        | JavaScript regular expression                         | `^Notebook` matches any tool starting with Notebook; `mcp__memory__.*` matches every tool from the `memory` server |

The `FileChanged` event does not follow these rules when building its watch list. See [FileChanged](#filechanged).

Each event type matches on a different field:

| Event                                                                                                          | What the matcher filters                                     | Example matcher values                                                                                                    |
| :------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------ |
| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`                     | tool name                                                    | `Bash`, `Edit\|Write`, `mcp__.*`                                                                                          |
| `SessionStart`                                                                                                 | how the session started                                      | `startup`, `resume`, `clear`, `compact`                                                                                   |
| `SessionEnd`                                                                                                   | why the session ended                                        | `clear`, `resume`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other`                                  |
| `Notification`                                                                                                 | notification type                                            | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`                                                  |
| `SubagentStart`                                                                                                | agent type                                                   | `Bash`, `Explore`, `Plan`, or custom agent names                                                                          |
| `PreCompact`, `PostCompact`                                                                                    | what triggered compaction                                    | `manual`, `auto`                                                                                                          |
| `SubagentStop`                                                                                                 | agent type                                                   | same values as `SubagentStart`                                                                                            |
| `ConfigChange`                                                                                                 | configuration source                                         | `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills`                                        |
| `CwdChanged`                                                                                                   | no matcher support                                           | always fires on every directory change                                                                                    |
| `FileChanged`                                                                                                  | literal filenames to watch (see [FileChanged](#filechanged)) | `.envrc\|.env`                                                                                                            |
| `StopFailure`                                                                                                  | error type                                                   | `rate_limit`, `authentication_failed`, `billing_error`, `invalid_request`, `server_error`, `max_output_tokens`, `unknown` |
| `InstructionsLoaded`                                                                                           | load reason                                                  | `session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact`                                              |
| `Elicitation`                                                                                                  | MCP server name                                              | your configured MCP server names                                                                                          |
| `ElicitationResult`                                                                                            | MCP server name                                              | same values as `Elicitation`                                                                                              |
| `UserPromptSubmit`, `Stop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove` | no matcher support                                           | always fires on every occurrence                                                                                          |

The matcher runs against a field from the [JSON input](#hook-input-and-output) that Claude Code sends to your hook on stdin. For tool events, that field is `tool_name`. Each [hook event](#hook-events) section lists the full set of matcher values and the input schema for that event.

This example runs a linting script only when Claude writes or edits a file:

```json theme={null}
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/lint-check.sh"
          }
        ]
      }
    ]
  }
}
```

`UserPromptSubmit`, `Stop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`, and `CwdChanged` don't support matchers and always fire on every occurrence. If you add a `matcher` field to these events, it is silently ignored.

For tool events, you can filter more narrowly by setting the [`if` field](#common-fields) on individual hook handlers. `if` uses [permission rule syntax](/en/permissions) to match against the tool name and arguments together, so `"Bash(git *)"` runs only for `git` commands and `"Edit(*.ts)"` runs only for TypeScript files.

#### Match MCP tools

[MCP](/en/mcp) server tools appear as regular tools in tool events (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`), so you can match them the same way you match any other tool name.

MCP tools follow the naming pattern `mcp__<server>__<tool>`, for example:

* `mcp__memory__create_entities`: Memory server's create entities tool
* `mcp__filesystem__read_file`: Filesystem server's read file tool
* `mcp__github__search_repositories`: GitHub server's search tool

To match every tool from a server, append `.*` to the server prefix. The `.*` is required: a matcher like `mcp__memory` contains only letters and underscores, so it is compared as an exact string and matches no tool.

* `mcp__memory__.*` matches all tools from the `memory` server
* `mcp__.*__write.*` matches any tool whose name starts with `write` from any server

This example logs all memory server operations and validates write operations from any MCP server:

```json theme={null}
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__memory__.*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Memory operation initiated' >> ~/mcp-operations.log"
          }
        ]
      },
      {
        "matcher": "mcp__.*__write.*",
        "hooks": [
          {
            "type": "command",
            "command": "/home/user/scripts/validate-mcp-write.py"
          }
        ]
      }
    ]
  }
}
```

### Hook handler fields

Each object in the inner `hooks` array is a hook handler: the shell command, HTTP endpoint, LLM prompt, or agent that runs when the matcher matches. There are four types:

* **[Command hooks](#command-hook-fields)** (`type: "command"`): run a shell command. Your script receives the event's [JSON input](#hook-input-and-output) on stdin and communicates results back through exit codes and stdout.
* **[HTTP hooks](#http-hook-fields)** (`type: "http"`): send the event's JSON input as an HTTP POST request to a URL. The endpoint communicates results back through the response body using the same [JSON output format](#json-output) as command hooks.
* **[Prompt hooks](#prompt-and-agent-hook-fields)** (`type: "prompt"`): send a prompt to a Claude model for single-turn evaluation. The model returns a yes/no decision as JSON. See [Prompt-based hooks](#prompt-based-hooks).
* **[Agent hooks](#prompt-and-agent-hook-fields)** (`type: "agent"`): spawn a subagent that can use tools like Read, Grep, and Glob to verify conditions before returning a decision. See [Agent-based hooks](#agent-based-hooks).

#### Common fields

These fields apply to all hook types:

| Field           | Required | Description                                                                                                                                                                                                                                                                                                                                                                                              |
| :-------------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `type`          | yes      | `"command"`, `"http"`, `"prompt"`, or `"agent"`                                                                                                                                                                                                                                                                                                                                                          |
| `if`            | no       | Permission rule syntax to filter when this hook runs, such as `"Bash(git *)"` or `"Edit(*.ts)"`. The hook only spawns if the tool call matches the pattern. Only evaluated on tool events: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, and `PermissionDenied`. On other events, a hook with `if` set never runs. Uses the same syntax as [permission rules](/en/permissions) |
| `timeout`       | no       | Seconds before canceling. Defaults: 600 for command, 30 for prompt, 60 for agent                                                                                                                                                                                                                                                                                                                         |
| `statusMessage` | no       | Custom spinner message displayed while the hook runs                                                                                                                                                                                                                                                                                                                                                     |
| `once`          | no       | If `true`, runs once per session then is removed. Only honored for hooks declared in [skill frontmatter](#hooks-in-skills-and-agents); ignored in settings files and agent frontmatter                                                                                                                                                                                                                   |

#### Command hook fields

In addition to the [common fields](#common-fields), command hooks accept these fields:

| Field         | Required | Description                                                                                                                                                                                                                           |
| :------------ | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `command`     | yes      | Shell command to execute                                                                                                                                                                                                              |
| `async`       | no       | If `true`, runs in the background without blocking. See [Run hooks in the background](#run-hooks-in-the-background)                                                                                                                   |
| `asyncRewake` | no       | If `true`, runs in the background and wakes Claude on exit code 2. Implies `async`. The hook's stderr, or stdout if stderr is empty, is shown to Claude as a system reminder so it can react to a long-running background failure     |
| `shell`       | no       | Shell to use for this hook. Accepts `"bash"` (default) or `"powershell"`. Setting `"powershell"` runs the command via PowerShell on Windows. Does not require `CLAUDE_CODE_USE_POWERSHELL_TOOL` since hooks spawn PowerShell directly |

#### HTTP hook fields

In addition to the [common fields](#common-fields), HTTP hooks accept these fields:

| Field            | Required | Description                                                                                                                                                                                      |
| :--------------- | :------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`            | yes      | URL to send the POST request to                                                                                                                                                                  |
| `headers`        | no       | Additional HTTP headers as key-value pairs. Values support environment variable interpolation using `$VAR_NAME` or `${VAR_NAME}` syntax. Only variables listed in `allowedEnvVars` are resolved  |
| `allowedEnvVars` | no       | List of environment variable names that may be interpolated into header values. References to unlisted variables are replaced with empty strings. Required for any env var interpolation to work |

Claude Code sends the hook's [JSON input](#hook-input-and-output) as the POST request body with `Content-Type: application/json`. The response body uses the same [JSON output format](#json-output) as command hooks.

Error handling differs from command hooks: non-2xx responses, connection failures, and timeouts all produce non-blocking errors that allow execution to continue. To block a tool call or deny a permission, return a 2xx response with a JSON body containing `decision: "block"` or a `hookSpecificOutput` with `permissionDecision: "deny"`.

This example sends `PreToolUse` events to a local validation service, authenticating with a token from the `MY_TOKEN` environment variable:

```json theme={null}
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "http",
            "url": "http://localhost:8080/hooks/pre-tool-use",
            "timeout": 30,
            "headers": {
              "Authorization": "Bearer $MY_TOKEN"
            },
            "allowedEnvVars": ["MY_TOKEN"]
          }
        ]
      }
    ]
  }
}
```

#### Prompt and agent hook fields

In addition to the [common fields](#common-fields), prompt and agent hooks accept these fields:

| Field    | Required | Description                                                                                 |
| :------- | :------- | :------------------------------------------------------------------------------------------ |
| `prompt` | yes      | Prompt text to send to the model. Use `$ARGUMENTS` as a placeholder for the hook input JSON |
| `model`  | no       | Model to use for evaluation. Defaults to a fast model                                       |

All matching hooks run in parallel, and identical handlers are deduplicated automatically. Command hooks are deduplicated by command string, and HTTP hooks are deduplicated by URL. Handlers run in the current directory with Claude Code's environment. The `$CLAUDE_CODE_REMOTE` environment variable is set to `"true"` in remote web environments and not set in the local CLI.

### Reference scripts by path

Use environment variables to reference hook scripts relative to the project or plugin root, regardless of the working directory when the hook runs:

* `$CLAUDE_PROJECT_DIR`: the project root. Wrap in quotes to handle paths with spaces.
* `${CLAUDE_PLUGIN_ROOT}`: the plugin's installation directory, for scripts bundled with a [plugin](/en/plugins). Changes on each plugin update.
* `${CLAUDE_PLUGIN_DATA}`: the plugin's [persistent data directory](/en/plugins-reference#persistent-data-directory), for dependencies and state that should survive plugin updates.

<Tabs>
  <Tab title="Project scripts">
    This example uses `$CLAUDE_PROJECT_DIR` to run a style checker from the project's `.claude/hooks/` directory after any `Write` or `Edit` tool call:

    ```json theme={null}
    {
      "hooks": {
        "PostToolUse": [
          {
            "matcher": "Write|Edit",
            "hooks": [
              {
                "type": "command",
                "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-style.sh"
              }
            ]
          }
        ]
      }
    }
    ```
  </Tab>

  <Tab title="Plugin scripts">
    Define plugin hooks in `hooks/hooks.json` with an optional top-level `description` field. When a plugin is enabled, its hooks merge with your user and project hooks.

    This example runs a formatting script bundled with the plugin:

    ```json theme={null}
    {
      "description": "Automatic code formatting",
      "hooks": {
        "PostToolUse": [
          {
            "matcher": "Write|Edit",
            "hooks": [
              {
                "type": "command",
                "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
                "timeout": 30
              }
            ]
          }
        ]
      }
    }
    ```

    See the [plugin components reference](/en/plugins-reference#hooks) for details on creating plugin hooks.
  </Tab>
</Tabs>

### Hooks in skills and agents

In addition to settings files and plugins, hooks can be defined directly in [skills](/en/skills) and [subagents](/en/sub-agents) using frontmatter. These hooks are scoped to the component's lifecycle and only run when that component is active.

All hook events are supported. For subagents, `Stop` hooks are automatically converted to `SubagentStop` since that is the event that fires when a subagent completes.

Hooks use the same configuration format as settings-based hooks but are scoped to the component's lifetime and cleaned up when it finishes.

This skill defines a `PreToolUse` hook that runs a security validation script before each `Bash` command:

```yaml theme={null}
---
name: secure-operations
description: Perform operations with security checks
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
---
```

Agents use the same format in their YAML frontmatter.

### The `/hooks` menu

Type `/hooks` in Claude Code to open a read-only browser for your configured hooks. The menu shows every hook event with a count of configured hooks, lets you drill into matchers, and shows the full details of each hook handler. Use it to verify configuration, check which settings file a hook came from, or inspect a hook's command, prompt, or URL.

The menu displays all four hook types: `command`, `prompt`, `agent`, and `http`. Each hook is labeled with a `[type]` prefix and a source indicating where it was defined:

* `User`: from `~/.claude/settings.json`
* `Project`: from `.claude/settings.json`
* `Local`: from `.claude/settings.local.json`
* `Plugin`: from a plugin's `hooks/hooks.json`
* `Session`: registered in memory for the current session
* `Built-in`: registered internally by Claude Code

Selecting a hook opens a detail view showing its event, matcher, type, source file, and the full command, prompt, or URL. The menu is read-only: to add, modify, or remove hooks, edit the settings JSON directly or ask Claude to make the change.

### Disable or remove hooks

To remove a hook, delete its entry from the settings JSON file.

To temporarily disable all hooks without removing them, set `"disableAllHooks": true` in your settings file. There is no way to disable an individual hook while keeping it in the configuration.

The `disableAllHooks` setting respects the managed settings hierarchy. If an administrator has configured hooks through managed policy settings, `disableAllHooks` set in user, project, or local settings cannot disable those managed hooks. Only `disableAllHooks` set at the managed settings level can disable managed hooks.

Direct edits to hooks in settings files are normally picked up automatically by the file watcher.

## Hook input and output

Command hooks receive JSON data via stdin and communicate results through exit codes, stdout, and stderr. HTTP hooks receive the same JSON as the POST request body and communicate results through the HTTP response body. This section covers fields and behavior common to all events. Each event's section under [Hook events](#hook-events) includes its specific input schema and decision control options.

### Common input fields

Hook events receive these fields as JSON, in addition to event-specific fields documented in each [hook event](#hook-events) section. For command hooks, this JSON arrives via stdin. For HTTP hooks, it arrives as the POST request body.

| Field             | Description                                                                                                                                                                                                                           |
| :---------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `session_id`      | Current session identifier                                                                                                                                                                                                            |
| `transcript_path` | Path to conversation JSON                                                                                                                                                                                                             |
| `cwd`             | Current working directory when the hook is invoked                                                                                                                                                                                    |
| `permission_mode` | Current [permission mode](/en/permissions#permission-modes): `"default"`, `"plan"`, `"acceptEdits"`, `"auto"`, `"dontAsk"`, or `"bypassPermissions"`. Not all events receive this field: see each event's JSON example below to check |
| `hook_event_name` | Name of the event that fired                                                                                                                                                                                                          |

When running with `--agent` or inside a subagent, two additional fields are included:

| Field        | Description                                                                                                                                                                                                                          |
| :----------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `agent_id`   | Unique identifier for the subagent. Present only when the hook fires inside a subagent call. Use this to distinguish subagent hook calls from main-thread calls.                                                                     |
| `agent_type` | Agent name (for example, `"Explore"` or `"security-reviewer"`). Present when the session uses `--agent` or the hook fires inside a subagent. For subagents, the subagent's type takes precedence over the session's `--agent` value. |

For example, a `PreToolUse` hook for a Bash command receives this on stdin:

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/home/user/.claude/projects/.../transcript.jsonl",
  "cwd": "/home/user/my-project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test"
  }
}
```

The `tool_name` and `tool_input` fields are event-specific. Each [hook event](#hook-events) section documents the additional fields for that event.

### Exit code output

The exit code from your hook command tells Claude Code whether the action should proceed, be blocked, or be ignored.

**Exit 0** means success. Claude Code parses stdout for [JSON output fields](#json-output). JSON output is only processed on exit 0. For most events, stdout is written to the debug log but not shown in the transcript. The exceptions are `UserPromptSubmit` and `SessionStart`, where stdout is added as context that Claude can see and act on.

**Exit 2** means a blocking error. Claude Code ignores stdout and any JSON in it. Instead, stderr text is fed back to Claude as an error message. The effect depends on the event: `PreToolUse` blocks the tool call, `UserPromptSubmit` rejects the prompt, and so on. See [exit code 2 behavior](#exit-code-2-behavior-per-event) for the full list.

**Any other exit code** is a non-blocking error for most hook events. The transcript shows a `<hook name> hook error` notice followed by the first line of stderr, so you can identify the cause without `--debug`. Execution continues and the full stderr is written to the debug log.

For example, a hook command script that blocks dangerous Bash commands:

```bash theme={null}
#!/bin/bash
# Reads JSON input from stdin, checks the command
command=$(jq -r '.tool_input.command' < /dev/stdin)

if [[ "$command" == rm* ]]; then
  echo "Blocked: rm commands are not allowed" >&2
  exit 2  # Blocking error: tool call is prevented
fi

exit 0  # Success: tool call proceeds
```

<Warning>
  For most hook events, only exit code 2 blocks the action. Claude Code treats exit code 1 as a non-blocking error and proceeds with the action, even though 1 is the conventional Unix failure code. If your hook is meant to enforce a policy, use `exit 2`. The exception is `WorktreeCreate`, where any non-zero exit code aborts worktree creation.
</Warning>

#### Exit code 2 behavior per event

Exit code 2 is the way a hook signals "stop, don't do this." The effect depends on the event, because some events represent actions that can be blocked (like a tool call that hasn't happened yet) and others represent things that already happened or can't be prevented.

| Hook event           | Can block? | What happens on exit 2                                                                                                               |
| :------------------- | :--------- | :----------------------------------------------------------------------------------------------------------------------------------- |
| `PreToolUse`         | Yes        | Blocks the tool call                                                                                                                 |
| `PermissionRequest`  | Yes        | Denies the permission                                                                                                                |
| `UserPromptSubmit`   | Yes        | Blocks prompt processing and erases the prompt                                                                                       |
| `Stop`               | Yes        | Prevents Claude from stopping, continues the conversation                                                                            |
| `SubagentStop`       | Yes        | Prevents the subagent from stopping                                                                                                  |
| `TeammateIdle`       | Yes        | Prevents the teammate from going idle (teammate continues working)                                                                   |
| `TaskCreated`        | Yes        | Rolls back the task creation                                                                                                         |
| `TaskCompleted`      | Yes        | Prevents the task from being marked as completed                                                                                     |
| `ConfigChange`       | Yes        | Blocks the configuration change from taking effect (except `policy_settings`)                                                        |
| `StopFailure`        | No         | Output and exit code are ignored                                                                                                     |
| `PostToolUse`        | No         | Shows stderr to Claude (tool already ran)                                                                                            |
| `PostToolUseFailure` | No         | Shows stderr to Claude (tool already failed)                                                                                         |
| `PermissionDenied`   | No         | Exit code and stderr are ignored (denial already occurred). Use JSON `hookSpecificOutput.retry: true` to tell the model it may retry |
| `Notification`       | No         | Shows stderr to user only                                                                                                            |
| `SubagentStart`      | No         | Shows stderr to user only                                                                                                            |
| `SessionStart`       | No         | Shows stderr to user only                                                                                                            |
| `SessionEnd`         | No         | Shows stderr to user only                                                                                                            |
| `CwdChanged`         | No         | Shows stderr to user only                                                                                                            |
| `FileChanged`        | No         | Shows stderr to user only                                                                                                            |
| `PreCompact`         | Yes        | Blocks compaction                                                                                                                    |
| `PostCompact`        | No         | Shows stderr to user only                                                                                                            |
| `Elicitation`        | Yes        | Denies the elicitation                                                                                                               |
| `ElicitationResult`  | Yes        | Blocks the response (action becomes decline)                                                                                         |
| `WorktreeCreate`     | Yes        | Any non-zero exit code causes worktree creation to fail                                                                              |
| `WorktreeRemove`     | No         | Failures are logged in debug mode only                                                                                               |
| `InstructionsLoaded` | No         | Exit code is ignored                                                                                                                 |

### HTTP response handling

HTTP hooks use HTTP status codes and response bodies instead of exit codes and stdout:

* **2xx with an empty body**: success, equivalent to exit code 0 with no output
* **2xx with a plain text body**: success, the text is added as context
* **2xx with a JSON body**: success, parsed using the same [JSON output](#json-output) schema as command hooks
* **Non-2xx status**: non-blocking error, execution continues
* **Connection failure or timeout**: non-blocking error, execution continues

Unlike command hooks, HTTP hooks cannot signal a blocking error through status codes alone. To block a tool call or deny a permission, return a 2xx response with a JSON body containing the appropriate decision fields.

### JSON output

Exit codes let you allow or block, but JSON output gives you finer-grained control. Instead of exiting with code 2 to block, exit 0 and print a JSON object to stdout. Claude Code reads specific fields from that JSON to control behavior, including [decision control](#decision-control) for blocking, allowing, or escalating to the user.

<Note>
  You must choose one approach per hook, not both: either use exit codes alone for signaling, or exit 0 and print JSON for structured control. Claude Code only processes JSON on exit 0. If you exit 2, any JSON is ignored.
</Note>

Your hook's stdout must contain only the JSON object. If your shell profile prints text on startup, it can interfere with JSON parsing. See [JSON validation failed](/en/hooks-guide#json-validation-failed) in the troubleshooting guide.

Hook output injected into context (`additionalContext`, `systemMessage`, or plain stdout) is capped at 10,000 characters. Output that exceeds this limit is saved to a file and replaced with a preview and file path, the same way large tool results are handled.

The JSON object supports three kinds of fields:

* **Universal fields** like `continue` work across all events. These are listed in the table below.
* **Top-level `decision` and `reason`** are used by some events to block or provide feedback.
* **`hookSpecificOutput`** is a nested object for events that need richer control. It requires a `hookEventName` field set to the event name.

| Field            | Default | Description                                                                                                                |
| :--------------- | :------ | :------------------------------------------------------------------------------------------------------------------------- |
| `continue`       | `true`  | If `false`, Claude stops processing entirely after the hook runs. Takes precedence over any event-specific decision fields |
| `stopReason`     | none    | Message shown to the user when `continue` is `false`. Not shown to Claude                                                  |
| `suppressOutput` | `false` | If `true`, omits stdout from the debug log                                                                                 |
| `systemMessage`  | none    | Warning message shown to the user                                                                                          |

To stop Claude entirely regardless of event type:

```json theme={null}
{ "continue": false, "stopReason": "Build failed, fix errors before continuing" }
```

#### Decision control

Not every event supports blocking or controlling behavior through JSON. The events that do each use a different set of fields to express that decision. Use this table as a quick reference before writing a hook:

| Events                                                                                                          | Decision pattern               | Key fields                                                                                                                                                          |
| :-------------------------------------------------------------------------------------------------------------- | :----------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| UserPromptSubmit, PostToolUse, PostToolUseFailure, Stop, SubagentStop, ConfigChange, PreCompact                 | Top-level `decision`           | `decision: "block"`, `reason`                                                                                                                                       |
| TeammateIdle, TaskCreated, TaskCompleted                                                                        | Exit code or `continue: false` | Exit code 2 blocks the action with stderr feedback. JSON `{"continue": false, "stopReason": "..."}` also stops the teammate entirely, matching `Stop` hook behavior |
| PreToolUse                                                                                                      | `hookSpecificOutput`           | `permissionDecision` (allow/deny/ask/defer), `permissionDecisionReason`                                                                                             |
| PermissionRequest                                                                                               | `hookSpecificOutput`           | `decision.behavior` (allow/deny)                                                                                                                                    |
| PermissionDenied                                                                                                | `hookSpecificOutput`           | `retry: true` tells the model it may retry the denied tool call                                                                                                     |
| WorktreeCreate                                                                                                  | path return                    | Command hook prints path on stdout; HTTP hook returns `hookSpecificOutput.worktreePath`. Hook failure or missing path fails creation                                |
| Elicitation                                                                                                     | `hookSpecificOutput`           | `action` (accept/decline/cancel), `content` (form field values for accept)                                                                                          |
| ElicitationResult                                                                                               | `hookSpecificOutput`           | `action` (accept/decline/cancel), `content` (form field values override)                                                                                            |
| WorktreeRemove, Notification, SessionEnd, PostCompact, InstructionsLoaded, StopFailure, CwdChanged, FileChanged | None                           | No decision control. Used for side effects like logging or cleanup                                                                                                  |

Here are examples of each pattern in action:

<Tabs>
  <Tab title="Top-level decision">
    Used by `UserPromptSubmit`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `SubagentStop`, `ConfigChange`, and `PreCompact`. The only value is `"block"`. To allow the action to proceed, omit `decision` from your JSON, or exit 0 without any JSON at all:

    ```json theme={null}
    {
      "decision": "block",
      "reason": "Test suite must pass before proceeding"
    }
    ```
  </Tab>

  <Tab title="PreToolUse">
    Uses `hookSpecificOutput` for richer control: allow, deny, or escalate to the user. You can also modify tool input before it runs or inject additional context for Claude. See [PreToolUse decision control](#pretooluse-decision-control) for the full set of options.

    ```json theme={null}
    {
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Database writes are not allowed"
      }
    }
    ```
  </Tab>

  <Tab title="PermissionRequest">
    Uses `hookSpecificOutput` to allow or deny a permission request on behalf of the user. When allowing, you can also modify the tool's input or apply permission rules so the user isn't prompted again. See [PermissionRequest decision control](#permissionrequest-decision-control) for the full set of options.

    ```json theme={null}
    {
      "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
          "behavior": "allow",
          "updatedInput": {
            "command": "npm run lint"
          }
        }
      }
    }
    ```
  </Tab>
</Tabs>

For extended examples including Bash command validation, prompt filtering, and auto-approval scripts, see [What you can automate](/en/hooks-guide#what-you-can-automate) in the guide and the [Bash command validator reference implementation](https://github.com/anthropics/claude-code/blob/main/examples/hooks/bash_command_validator_example.py).

## Hook events

Each event corresponds to a point in Claude Code's lifecycle where hooks can run. The sections below are ordered to match the lifecycle: from session setup through the agentic loop to session end. Each section describes when the event fires, what matchers it supports, the JSON input it receives, and how to control behavior through output.

### SessionStart

Runs when Claude Code starts a new session or resumes an existing session. Useful for loading development context like existing issues or recent changes to your codebase, or setting up environment variables. For static context that does not require a script, use [CLAUDE.md](/en/memory) instead.

SessionStart runs on every session, so keep these hooks fast. Only `type: "command"` hooks are supported.

The matcher value corresponds to how the session was initiated:

| Matcher   | When it fires                          |
| :-------- | :------------------------------------- |
| `startup` | New session                            |
| `resume`  | `--resume`, `--continue`, or `/resume` |
| `clear`   | `/clear`                               |
| `compact` | Auto or manual compaction              |

#### SessionStart input

In addition to the [common input fields](#common-input-fields), SessionStart hooks receive `source`, `model`, and optionally `agent_type`. The `source` field indicates how the session started: `"startup"` for new sessions, `"resume"` for resumed sessions, `"clear"` after `/clear`, or `"compact"` after compaction. The `model` field contains the model identifier. If you start Claude Code with `claude --agent <name>`, an `agent_type` field contains the agent name.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "hook_event_name": "SessionStart",
  "source": "startup",
  "model": "claude-sonnet-4-6"
}
```

#### SessionStart decision control

Any text your hook script prints to stdout is added as context for Claude. In addition to the [JSON output fields](#json-output) available to all hooks, you can return these event-specific fields:

| Field               | Description                                                               |
| :------------------ | :------------------------------------------------------------------------ |
| `additionalContext` | String added to Claude's context. Multiple hooks' values are concatenated |

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "My additional context here"
  }
}
```

#### Persist environment variables

SessionStart hooks have access to the `CLAUDE_ENV_FILE` environment variable, which provides a file path where you can persist environment variables for subsequent Bash commands.

To set individual environment variables, write `export` statements to `CLAUDE_ENV_FILE`. Use append (`>>`) to preserve variables set by other hooks:

```bash theme={null}
#!/bin/bash

if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
  echo 'export DEBUG_LOG=true' >> "$CLAUDE_ENV_FILE"
  echo 'export PATH="$PATH:./node_modules/.bin"' >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

To capture all environment changes from setup commands, compare the exported variables before and after:

```bash theme={null}
#!/bin/bash

ENV_BEFORE=$(export -p | sort)

# Run your setup commands that modify the environment
source ~/.nvm/nvm.sh
nvm use 20

if [ -n "$CLAUDE_ENV_FILE" ]; then
  ENV_AFTER=$(export -p | sort)
  comm -13 <(echo "$ENV_BEFORE") <(echo "$ENV_AFTER") >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

Any variables written to this file will be available in all subsequent Bash commands that Claude Code executes during the session.

<Note>
  `CLAUDE_ENV_FILE` is available for SessionStart, [CwdChanged](#cwdchanged), and [FileChanged](#filechanged) hooks. Other hook types do not have access to this variable.
</Note>

### InstructionsLoaded

Fires when a `CLAUDE.md` or `.claude/rules/*.md` file is loaded into context. This event fires at session start for eagerly-loaded files and again later when files are lazily loaded, for example when Claude accesses a subdirectory that contains a nested `CLAUDE.md` or when conditional rules with `paths:` frontmatter match. The hook does not support blocking or decision control. It runs asynchronously for observability purposes.

The matcher runs against `load_reason`. For example, use `"matcher": "session_start"` to fire only for files loaded at session start, or `"matcher": "path_glob_match|nested_traversal"` to fire only for lazy loads.

#### InstructionsLoaded input

In addition to the [common input fields](#common-input-fields), InstructionsLoaded hooks receive these fields:

| Field               | Description                                                                                                                                                                                                   |
| :------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `file_path`         | Absolute path to the instruction file that was loaded                                                                                                                                                         |
| `memory_type`       | Scope of the file: `"User"`, `"Project"`, `"Local"`, or `"Managed"`                                                                                                                                           |
| `load_reason`       | Why the file was loaded: `"session_start"`, `"nested_traversal"`, `"path_glob_match"`, `"include"`, or `"compact"`. The `"compact"` value fires when instruction files are re-loaded after a compaction event |
| `globs`             | Path glob patterns from the file's `paths:` frontmatter, if any. Present only for `path_glob_match` loads                                                                                                     |
| `trigger_file_path` | Path to the file whose access triggered this load, for lazy loads                                                                                                                                             |
| `parent_file_path`  | Path to the parent instruction file that included this one, for `include` loads                                                                                                                               |

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../transcript.jsonl",
  "cwd": "/Users/my-project",
  "hook_event_name": "InstructionsLoaded",
  "file_path": "/Users/my-project/CLAUDE.md",
  "memory_type": "Project",
  "load_reason": "session_start"
}
```

#### InstructionsLoaded decision control

InstructionsLoaded hooks have no decision control. They cannot block or modify instruction loading. Use this event for audit logging, compliance tracking, or observability.

### UserPromptSubmit

Runs when the user submits a prompt, before Claude processes it. This allows you to add additional context based on the prompt/conversation, validate prompts, or block certain types of prompts.

#### UserPromptSubmit input

In addition to the [common input fields](#common-input-fields), UserPromptSubmit hooks receive the `prompt` field containing the text the user submitted.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "Write a function to calculate the factorial of a number"
}
```

#### UserPromptSubmit decision control

`UserPromptSubmit` hooks can control whether a user prompt is processed and add context. All [JSON output fields](#json-output) are available.

There are two ways to add context to the conversation on exit code 0:

* **Plain text stdout**: any non-JSON text written to stdout is added as context
* **JSON with `additionalContext`**: use the JSON format below for more control. The `additionalContext` field is added as context

Plain stdout is shown as hook output in the transcript. The `additionalContext` field is added more discretely.

To block a prompt, return a JSON object with `decision` set to `"block"`:

| Field               | Description                                                                                                        |
| :------------------ | :----------------------------------------------------------------------------------------------------------------- |
| `decision`          | `"block"` prevents the prompt from being processed and erases it from context. Omit to allow the prompt to proceed |
| `reason`            | Shown to the user when `decision` is `"block"`. Not added to context                                               |
| `additionalContext` | String added to Claude's context                                                                                   |
| `sessionTitle`      | Sets the session title, same effect as `/rename`. Use to name sessions automatically based on the prompt content   |

```json theme={null}
{
  "decision": "block",
  "reason": "Explanation for decision",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "My additional context here",
    "sessionTitle": "My session title"
  }
}
```

<Note>
  The JSON format isn't required for simple use cases. To add context, you can print plain text to stdout with exit code 0. Use JSON when you need to
  block prompts or want more structured control.
</Note>

### PreToolUse

Runs after Claude creates tool parameters and before processing the tool call. Matches on tool name: `Bash`, `Edit`, `Write`, `Read`, `Glob`, `Grep`, `Agent`, `WebFetch`, `WebSearch`, `AskUserQuestion`, `ExitPlanMode`, and any [MCP tool names](#match-mcp-tools).

Use [PreToolUse decision control](#pretooluse-decision-control) to allow, deny, ask, or defer the tool call.

#### PreToolUse input

In addition to the [common input fields](#common-input-fields), PreToolUse hooks receive `tool_name`, `tool_input`, and `tool_use_id`. The `tool_input` fields depend on the tool:

##### Bash

Executes shell commands.

| Field               | Type    | Example            | Description                                   |
| :------------------ | :------ | :----------------- | :-------------------------------------------- |
| `command`           | string  | `"npm test"`       | The shell command to execute                  |
| `description`       | string  | `"Run test suite"` | Optional description of what the command does |
| `timeout`           | number  | `120000`           | Optional timeout in milliseconds              |
| `run_in_background` | boolean | `false`            | Whether to run the command in background      |

##### Write

Creates or overwrites a file.

| Field       | Type   | Example               | Description                        |
| :---------- | :----- | :-------------------- | :--------------------------------- |
| `file_path` | string | `"/path/to/file.txt"` | Absolute path to the file to write |
| `content`   | string | `"file content"`      | Content to write to the file       |

##### Edit

Replaces a string in an existing file.

| Field         | Type    | Example               | Description                        |
| :------------ | :------ | :-------------------- | :--------------------------------- |
| `file_path`   | string  | `"/path/to/file.txt"` | Absolute path to the file to edit  |
| `old_string`  | string  | `"original text"`     | Text to find and replace           |
| `new_string`  | string  | `"replacement text"`  | Replacement text                   |
| `replace_all` | boolean | `false`               | Whether to replace all occurrences |

##### Read

Reads file contents.

| Field       | Type   | Example               | Description                                |
| :---------- | :----- | :-------------------- | :----------------------------------------- |
| `file_path` | string | `"/path/to/file.txt"` | Absolute path to the file to read          |
| `offset`    | number | `10`                  | Optional line number to start reading from |
| `limit`     | number | `50`                  | Optional number of lines to read           |

##### Glob

Finds files matching a glob pattern.

| Field     | Type   | Example          | Description                                                            |
| :-------- | :----- | :--------------- | :--------------------------------------------------------------------- |
| `pattern` | string | `"**/*.ts"`      | Glob pattern to match files against                                    |
| `path`    | string | `"/path/to/dir"` | Optional directory to search in. Defaults to current working directory |

##### Grep

Searches file contents with regular expressions.

| Field         | Type    | Example          | Description                                                                           |
| :------------ | :------ | :--------------- | :------------------------------------------------------------------------------------ |
| `pattern`     | string  | `"TODO.*fix"`    | Regular expression pattern to search for                                              |
| `path`        | string  | `"/path/to/dir"` | Optional file or directory to search in                                               |
| `glob`        | string  | `"*.ts"`         | Optional glob pattern to filter files                                                 |
| `output_mode` | string  | `"content"`      | `"content"`, `"files_with_matches"`, or `"count"`. Defaults to `"files_with_matches"` |
| `-i`          | boolean | `true`           | Case insensitive search                                                               |
| `multiline`   | boolean | `false`          | Enable multiline matching                                                             |

##### WebFetch

Fetches and processes web content.

| Field    | Type   | Example                       | Description                          |
| :------- | :----- | :---------------------------- | :----------------------------------- |
| `url`    | string | `"https://example.com/api"`   | URL to fetch content from            |
| `prompt` | string | `"Extract the API endpoints"` | Prompt to run on the fetched content |

##### WebSearch

Searches the web.

| Field             | Type   | Example                        | Description                                       |
| :---------------- | :----- | :----------------------------- | :------------------------------------------------ |
| `query`           | string | `"react hooks best practices"` | Search query                                      |
| `allowed_domains` | array  | `["docs.example.com"]`         | Optional: only include results from these domains |
| `blocked_domains` | array  | `["spam.example.com"]`         | Optional: exclude results from these domains      |

##### Agent

Spawns a [subagent](/en/sub-agents).

| Field           | Type   | Example                    | Description                                  |
| :-------------- | :----- | :------------------------- | :------------------------------------------- |
| `prompt`        | string | `"Find all API endpoints"` | The task for the agent to perform            |
| `description`   | string | `"Find API endpoints"`     | Short description of the task                |
| `subagent_type` | string | `"Explore"`                | Type of specialized agent to use             |
| `model`         | string | `"sonnet"`                 | Optional model alias to override the default |

##### AskUserQuestion

Asks the user one to four multiple-choice questions.

| Field       | Type   | Example                                                                                                            | Description                                                                                                                                                                                      |
| :---------- | :----- | :----------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `questions` | array  | `[{"question": "Which framework?", "header": "Framework", "options": [{"label": "React"}], "multiSelect": false}]` | Questions to present, each with a `question` string, short `header`, `options` array, and optional `multiSelect` flag                                                                            |
| `answers`   | object | `{"Which framework?": "React"}`                                                                                    | Optional. Maps question text to the selected option label. Multi-select answers join labels with commas. Claude does not set this field; supply it via `updatedInput` to answer programmatically |

#### PreToolUse decision control

`PreToolUse` hooks can control whether a tool call proceeds. Unlike other hooks that use a top-level `decision` field, PreToolUse returns its decision inside a `hookSpecificOutput` object. This gives it richer control: four outcomes (allow, deny, ask, or defer) plus the ability to modify tool input before execution.

| Field                      | Description                                                                                                                                                                                                                                                                                |
| :------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `permissionDecision`       | `"allow"` skips the permission prompt. `"deny"` prevents the tool call. `"ask"` prompts the user to confirm. `"defer"` exits gracefully so the tool can be resumed later. [Deny and ask rules](/en/permissions#manage-permissions) are still evaluated regardless of what the hook returns |
| `permissionDecisionReason` | For `"allow"` and `"ask"`, shown to the user but not Claude. For `"deny"`, shown to Claude. For `"defer"`, ignored                                                                                                                                                                         |
| `updatedInput`             | Modifies the tool's input parameters before execution. Replaces the entire input object, so include unchanged fields alongside modified ones. Combine with `"allow"` to auto-approve, or `"ask"` to show the modified input to the user. For `"defer"`, ignored                            |
| `additionalContext`        | String added to Claude's context before the tool executes. For `"defer"`, ignored                                                                                                                                                                                                          |

When multiple PreToolUse hooks return different decisions, precedence is `deny` > `defer` > `ask` > `allow`.

When a hook returns `"ask"`, the permission prompt displayed to the user includes a label identifying where the hook came from: for example, `[User]`, `[Project]`, `[Plugin]`, or `[Local]`. This helps users understand which configuration source is requesting confirmation.

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "My reason here",
    "updatedInput": {
      "field_to_modify": "new value"
    },
    "additionalContext": "Current environment: production. Proceed with caution."
  }
}
```

`AskUserQuestion` and `ExitPlanMode` require user interaction and normally block in [non-interactive mode](/en/headless) with the `-p` flag. Returning `permissionDecision: "allow"` together with `updatedInput` satisfies that requirement: the hook reads the tool's input from stdin, collects the answer through your own UI, and returns it in `updatedInput` so the tool runs without prompting. Returning `"allow"` alone is not sufficient for these tools. For `AskUserQuestion`, echo back the original `questions` array and add an [`answers`](#askuserquestion) object mapping each question's text to the chosen answer.

<Note>
  PreToolUse previously used top-level `decision` and `reason` fields, but these are deprecated for this event. Use `hookSpecificOutput.permissionDecision` and `hookSpecificOutput.permissionDecisionReason` instead. The deprecated values `"approve"` and `"block"` map to `"allow"` and `"deny"` respectively. Other events like PostToolUse and Stop continue to use top-level `decision` and `reason` as their current format.
</Note>

#### Defer a tool call for later

`"defer"` is for integrations that run `claude -p` as a subprocess and read its JSON output, such as an Agent SDK app or a custom UI built on top of Claude Code. It lets that calling process pause Claude at a tool call, collect input through its own interface, and resume where it left off. Claude Code honors this value only in [non-interactive mode](/en/headless) with the `-p` flag. In interactive sessions it logs a warning and ignores the hook result.

<Note>
  The `defer` value requires Claude Code v2.1.89 or later. Earlier versions do not recognize it and the tool proceeds through the normal permission flow.
</Note>

The `AskUserQuestion` tool is the typical case: Claude wants to ask the user something, but there is no terminal to answer in. The round trip works like this:

1. Claude calls `AskUserQuestion`. The `PreToolUse` hook fires.
2. The hook returns `permissionDecision: "defer"`. The tool does not execute. The process exits with `stop_reason: "tool_deferred"` and the pending tool call preserved in the transcript.
3. The calling process reads `deferred_tool_use` from the SDK result, surfaces the question in its own UI, and waits for an answer.
4. The calling process runs `claude -p --resume <session-id>`. The same tool call fires `PreToolUse` again.
5. The hook returns `permissionDecision: "allow"` with the answer in `updatedInput`. The tool executes and Claude continues.

The `deferred_tool_use` field carries the tool's `id`, `name`, and `input`. The `input` is the parameters Claude generated for the tool call, captured before execution:

```json theme={null}
{
  "type": "result",
  "subtype": "success",
  "stop_reason": "tool_deferred",
  "session_id": "abc123",
  "deferred_tool_use": {
    "id": "toolu_01abc",
    "name": "AskUserQuestion",
    "input": { "questions": [{ "question": "Which framework?", "header": "Framework", "options": [{"label": "React"}, {"label": "Vue"}], "multiSelect": false }] }
  }
}
```

There is no timeout or retry limit. The session remains on disk until you resume it. If the answer is not ready when you resume, the hook can return `"defer"` again and the process exits the same way. The calling process controls when to break the loop by eventually returning `"allow"` or `"deny"` from the hook.

`"defer"` only works when Claude makes a single tool call in the turn. If Claude makes several tool calls at once, `"defer"` is ignored with a warning and the tool proceeds through the normal permission flow. The constraint exists because resume can only re-run one tool: there is no way to defer one call from a batch without leaving the others unresolved.

If the deferred tool is no longer available when you resume, the process exits with `stop_reason: "tool_deferred_unavailable"` and `is_error: true` before the hook fires. This happens when an MCP server that provided the tool is not connected for the resumed session. The `deferred_tool_use` payload is still included so you can identify which tool went missing.

<Warning>
  `--resume` does not restore the permission mode from the prior session. Pass the same `--permission-mode` flag on resume that was active when the tool was deferred. Claude Code logs a warning if the modes differ.
</Warning>

### PermissionRequest

Runs when the user is shown a permission dialog.
Use [PermissionRequest decision control](#permissionrequest-decision-control) to allow or deny on behalf of the user.

Matches on tool name, same values as PreToolUse.

#### PermissionRequest input

PermissionRequest hooks receive `tool_name` and `tool_input` fields like PreToolUse hooks, but without `tool_use_id`. An optional `permission_suggestions` array contains the "always allow" options the user would normally see in the permission dialog. The difference is when the hook fires: PermissionRequest hooks run when a permission dialog is about to be shown to the user, while PreToolUse hooks run before tool execution regardless of permission status.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PermissionRequest",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf node_modules",
    "description": "Remove node_modules directory"
  },
  "permission_suggestions": [
    {
      "type": "addRules",
      "rules": [{ "toolName": "Bash", "ruleContent": "rm -rf node_modules" }],
      "behavior": "allow",
      "destination": "localSettings"
    }
  ]
}
```

#### PermissionRequest decision control

`PermissionRequest` hooks can allow or deny permission requests. In addition to the [JSON output fields](#json-output) available to all hooks, your hook script can return a `decision` object with these event-specific fields:

| Field                | Description                                                                                                                                                                                                                     |
| :------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `behavior`           | `"allow"` grants the permission, `"deny"` denies it. [Deny and ask rules](/en/permissions#manage-permissions) are still evaluated, so a hook returning `"allow"` does not override a matching deny rule                         |
| `updatedInput`       | For `"allow"` only: modifies the tool's input parameters before execution. Replaces the entire input object, so include unchanged fields alongside modified ones. The modified input is re-evaluated against deny and ask rules |
| `updatedPermissions` | For `"allow"` only: array of [permission update entries](#permission-update-entries) to apply, such as adding an allow rule or changing the session permission mode                                                             |
| `message`            | For `"deny"` only: tells Claude why the permission was denied                                                                                                                                                                   |
| `interrupt`          | For `"deny"` only: if `true`, stops Claude                                                                                                                                                                                      |

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": {
        "command": "npm run lint"
      }
    }
  }
}
```

#### Permission update entries

The `updatedPermissions` output field and the [`permission_suggestions` input field](#permissionrequest-input) both use the same array of entry objects. Each entry has a `type` that determines its other fields, and a `destination` that controls where the change is written.

| `type`              | Fields                             | Effect                                                                                                                                                                      |
| :------------------ | :--------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `addRules`          | `rules`, `behavior`, `destination` | Adds permission rules. `rules` is an array of `{toolName, ruleContent?}` objects. Omit `ruleContent` to match the whole tool. `behavior` is `"allow"`, `"deny"`, or `"ask"` |
| `replaceRules`      | `rules`, `behavior`, `destination` | Replaces all rules of the given `behavior` at the `destination` with the provided `rules`                                                                                   |
| `removeRules`       | `rules`, `behavior`, `destination` | Removes matching rules of the given `behavior`                                                                                                                              |
| `setMode`           | `mode`, `destination`              | Changes the permission mode. Valid modes are `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, and `plan`                                                           |
| `addDirectories`    | `directories`, `destination`       | Adds working directories. `directories` is an array of path strings                                                                                                         |
| `removeDirectories` | `directories`, `destination`       | Removes working directories                                                                                                                                                 |

<Note>
  `setMode` with `bypassPermissions` only takes effect if the session was launched with bypass mode already available: `--dangerously-skip-permissions`, `--permission-mode bypassPermissions`, `--allow-dangerously-skip-permissions`, or `permissions.defaultMode: "bypassPermissions"` in settings, and the mode is not disabled by [`permissions.disableBypassPermissionsMode`](/en/permissions#managed-settings). Otherwise the update is a no-op. `bypassPermissions` is never persisted as `defaultMode` regardless of `destination`.
</Note>

The `destination` field on every entry determines whether the change stays in memory or persists to a settings file.

| `destination`     | Writes to                                       |
| :---------------- | :---------------------------------------------- |
| `session`         | in-memory only, discarded when the session ends |
| `localSettings`   | `.claude/settings.local.json`                   |
| `projectSettings` | `.claude/settings.json`                         |
| `userSettings`    | `~/.claude/settings.json`                       |

A hook can echo one of the `permission_suggestions` it received as its own `updatedPermissions` output, which is equivalent to the user selecting that "always allow" option in the dialog.

### PostToolUse

Runs immediately after a tool completes successfully.

Matches on tool name, same values as PreToolUse.

#### PostToolUse input

`PostToolUse` hooks fire after a tool has already executed successfully. The input includes both `tool_input`, the arguments sent to the tool, and `tool_response`, the result it returned. The exact schema for both depends on the tool.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

#### PostToolUse decision control

`PostToolUse` hooks can provide feedback to Claude after tool execution. In addition to the [JSON output fields](#json-output) available to all hooks, your hook script can return these event-specific fields:

| Field                  | Description                                                                                |
| :--------------------- | :----------------------------------------------------------------------------------------- |
| `decision`             | `"block"` prompts Claude with the `reason`. Omit to allow the action to proceed            |
| `reason`               | Explanation shown to Claude when `decision` is `"block"`                                   |
| `additionalContext`    | Additional context for Claude to consider                                                  |
| `updatedMCPToolOutput` | For [MCP tools](#match-mcp-tools) only: replaces the tool's output with the provided value |

```json theme={null}
{
  "decision": "block",
  "reason": "Explanation for decision",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Additional information for Claude"
  }
}
```

### PostToolUseFailure

Runs when a tool execution fails. This event fires for tool calls that throw errors or return failure results. Use this to log failures, send alerts, or provide corrective feedback to Claude.

Matches on tool name, same values as PreToolUse.

#### PostToolUseFailure input

PostToolUseFailure hooks receive the same `tool_name` and `tool_input` fields as PostToolUse, along with error information as top-level fields:

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PostToolUseFailure",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run test suite"
  },
  "tool_use_id": "toolu_01ABC123...",
  "error": "Command exited with non-zero status code 1",
  "is_interrupt": false
}
```

| Field          | Description                                                                     |
| :------------- | :------------------------------------------------------------------------------ |
| `error`        | String describing what went wrong                                               |
| `is_interrupt` | Optional boolean indicating whether the failure was caused by user interruption |

#### PostToolUseFailure decision control

`PostToolUseFailure` hooks can provide context to Claude after a tool failure. In addition to the [JSON output fields](#json-output) available to all hooks, your hook script can return these event-specific fields:

| Field               | Description                                                   |
| :------------------ | :------------------------------------------------------------ |
| `additionalContext` | Additional context for Claude to consider alongside the error |

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUseFailure",
    "additionalContext": "Additional information about the failure for Claude"
  }
}
```

### PermissionDenied

Runs when the [auto mode](/en/permission-modes#eliminate-prompts-with-auto-mode) classifier denies a tool call. This hook only fires in auto mode: it does not run when you manually deny a permission dialog, when a `PreToolUse` hook blocks a call, or when a `deny` rule matches. Use it to log classifier denials, adjust configuration, or tell the model it may retry the tool call.

Matches on tool name, same values as PreToolUse.

#### PermissionDenied input

In addition to the [common input fields](#common-input-fields), PermissionDenied hooks receive `tool_name`, `tool_input`, `tool_use_id`, and `reason`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "auto",
  "hook_event_name": "PermissionDenied",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf /tmp/build",
    "description": "Clean build directory"
  },
  "tool_use_id": "toolu_01ABC123...",
  "reason": "Auto mode denied: command targets a path outside the project"
}
```

| Field    | Description                                                   |
| :------- | :------------------------------------------------------------ |
| `reason` | The classifier's explanation for why the tool call was denied |

#### PermissionDenied decision control

PermissionDenied hooks can tell the model it may retry the denied tool call. Return a JSON object with `hookSpecificOutput.retry` set to `true`:

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionDenied",
    "retry": true
  }
}
```

When `retry` is `true`, Claude Code adds a message to the conversation telling the model it may retry the tool call. The denial itself is not reversed. If your hook does not return JSON, or returns `retry: false`, the denial stands and the model receives the original rejection message.

### Notification

Runs when Claude Code sends notifications. Matches on notification type: `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`. Omit the matcher to run hooks for all notification types.

Use separate matchers to run different handlers depending on the notification type. This configuration triggers a permission-specific alert script when Claude needs permission approval and a different notification when Claude has been idle:

```json theme={null}
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/permission-alert.sh"
          }
        ]
      },
      {
        "matcher": "idle_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/idle-notification.sh"
          }
        ]
      }
    ]
  }
}
```

#### Notification input

In addition to the [common input fields](#common-input-fields), Notification hooks receive `message` with the notification text, an optional `title`, and `notification_type` indicating which type fired.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "hook_event_name": "Notification",
  "message": "Claude needs your permission to use Bash",
  "title": "Permission needed",
  "notification_type": "permission_prompt"
}
```

Notification hooks cannot block or modify notifications. In addition to the [JSON output fields](#json-output) available to all hooks, you can return `additionalContext` to add context to the conversation:

| Field               | Description                      |
| :------------------ | :------------------------------- |
| `additionalContext` | String added to Claude's context |

### SubagentStart

Runs when a Claude Code subagent is spawned via the Agent tool. Supports matchers to filter by agent type name (built-in agents like `Bash`, `Explore`, `Plan`, or custom agent names from `.claude/agents/`).

#### SubagentStart input

In addition to the [common input fields](#common-input-fields), SubagentStart hooks receive `agent_id` with the unique identifier for the subagent and `agent_type` with the agent name (built-in agents like `"Bash"`, `"Explore"`, `"Plan"`, or custom agent names).

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "hook_event_name": "SubagentStart",
  "agent_id": "agent-abc123",
  "agent_type": "Explore"
}
```

SubagentStart hooks cannot block subagent creation, but they can inject context into the subagent. In addition to the [JSON output fields](#json-output) available to all hooks, you can return:

| Field               | Description                            |
| :------------------ | :------------------------------------- |
| `additionalContext` | String added to the subagent's context |

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "Follow security guidelines for this task"
  }
}
```

### SubagentStop

Runs when a Claude Code subagent has finished responding. Matches on agent type, same values as SubagentStart.

#### SubagentStop input

In addition to the [common input fields](#common-input-fields), SubagentStop hooks receive `stop_hook_active`, `agent_id`, `agent_type`, `agent_transcript_path`, and `last_assistant_message`. The `agent_type` field is the value used for matcher filtering. The `transcript_path` is the main session's transcript, while `agent_transcript_path` is the subagent's own transcript stored in a nested `subagents/` folder. The `last_assistant_message` field contains the text content of the subagent's final response, so hooks can access it without parsing the transcript file.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../abc123.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SubagentStop",
  "stop_hook_active": false,
  "agent_id": "def456",
  "agent_type": "Explore",
  "agent_transcript_path": "~/.claude/projects/.../abc123/subagents/agent-def456.jsonl",
  "last_assistant_message": "Analysis complete. Found 3 potential issues..."
}
```

SubagentStop hooks use the same decision control format as [Stop hooks](#stop-decision-control).

### TaskCreated

Runs when a task is being created via the `TaskCreate` tool. Use this to enforce naming conventions, require task descriptions, or prevent certain tasks from being created.

When a `TaskCreated` hook exits with code 2, the task is not created and the stderr message is fed back to the model as feedback. To stop the teammate entirely instead of re-running it, return JSON with `{"continue": false, "stopReason": "..."}`. TaskCreated hooks do not support matchers and fire on every occurrence.

#### TaskCreated input

In addition to the [common input fields](#common-input-fields), TaskCreated hooks receive `task_id`, `task_subject`, and optionally `task_description`, `teammate_name`, and `team_name`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "TaskCreated",
  "task_id": "task-001",
  "task_subject": "Implement user authentication",
  "task_description": "Add login and signup endpoints",
  "teammate_name": "implementer",
  "team_name": "my-project"
}
```

| Field              | Description                                           |
| :----------------- | :---------------------------------------------------- |
| `task_id`          | Unique identifier for the task being created          |
| `task_subject`     | The task's title or subject                           |
| `task_description` | Optional description of the task                      |
| `teammate_name`    | Name of the teammate creating the task, if applicable |
| `team_name`        | Name of the team, if the session is using agent teams |

#### TaskCreated decision control

TaskCreated hooks can prevent task creation, similar to PreToolUse. Exit with code 2 to reject the task, or return JSON with `{"decision": "block"}`:

| Field               | Description                                                                                                                                       |
| :------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------ |
| `decision`          | `"block"` prevents the task from being created. Omit to allow task creation                                                                      |
| `reason`            | Shown to Claude when `decision` is `"block"`                                                                                                     |
| `additionalContext` | Additional context for Claude to consider                                                                                                        |
| `continue`          | If `false`, stops the teammate entirely instead of just preventing this specific task. Use when you want to halt the entire teammate operation |

```json theme={null}
{
  "decision": "block",
  "reason": "Task must include a description. Please provide more details.",
  "hookSpecificOutput": {
    "hookEventName": "TaskCreated",
    "additionalContext": "All tasks require descriptions for tracking"
  }
}
```

### TaskCompleted

Runs when a task is being marked as completed via the `TaskComplete` tool. Use this to validate task completion, enforce review requirements, or log completion events.

When a `TaskCompleted` hook exits with code 2, the task is not marked as completed and the stderr message is fed back to the model as feedback. To stop the teammate entirely, return JSON with `{"continue": false, "stopReason": "..."}`. TaskCompleted hooks do not support matchers and fire on every occurrence.

#### TaskCompleted input

In addition to the [common input fields](#common-input-fields), TaskCompleted hooks receive `task_id`, `task_subject`, and optionally `task_description`, `completion_reason`, `teammate_name`, and `team_name`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "TaskCompleted",
  "task_id": "task-001",
  "task_subject": "Implement user authentication",
  "task_description": "Add login and signup endpoints",
  "completion_reason": "Authentication endpoints fully implemented and tested",
  "teammate_name": "implementer",
  "team_name": "my-project"
}
```

| Field               | Description                                                      |
| :------------------ | :--------------------------------------------------------------- |
| `task_id`           | Unique identifier for the task being completed                   |
| `task_subject`      | The task's title or subject                                      |
| `task_description`  | Optional original description of the task                        |
| `completion_reason` | Optional reason provided by the teammate for the task completion |
| `teammate_name`     | Name of the teammate completing the task, if applicable          |
| `team_name`         | Name of the team, if the session is using agent teams            |

#### TaskCompleted decision control

TaskCompleted hooks use the same decision control pattern as TaskCreated:

| Field               | Description                                                                                                                                              |
| :------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `decision`          | `"block"` prevents the task from being marked as completed. Omit to allow completion                                                                    |
| `reason`            | Shown to Claude when `decision` is `"block"`                                                                                                            |
| `additionalContext` | Additional context for Claude to consider                                                                                                               |
| `continue`          | If `false`, stops the teammate entirely instead of just preventing this specific task completion. Use when you want to halt the entire teammate operation |

```json theme={null}
{
  "decision": "block",
  "reason": "Tests are failing. Please fix failures before marking complete.",
  "hookSpecificOutput": {
    "hookEventName": "TaskCompleted",
    "additionalContext": "Test suite shows 5 failing tests that must be resolved"
  }
}
```

### Stop

Runs when Claude finishes responding. This includes normal responses and [error cases](/en/permission-modes). Use this to log, analyze responses, or prevent Claude from stopping.

Matches on tool name, but Stop has no matcher support. This hook always fires.

#### Stop input

In addition to the [common input fields](#common-input-fields), Stop hooks receive `tool_name` and `tool_input`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Stop"
}
```

#### Stop decision control

`Stop` hooks can prevent Claude from stopping. Return a JSON object with `decision` set to `"block"`:

| Field    | Description                                           |
| :------- | :---------------------------------------------------- |
| `decision` | `"block"` prevents Claude from stopping             |
| `reason`   | Explanation shown to Claude when action is blocked  |

```json theme={null}
{
  "decision": "block",
  "reason": "Tests are still running, please wait for completion"
}
```

### StopFailure

Runs when a turn ends due to an API error. This is informational only; the hook cannot block or provide feedback, as the error has already occurred. Use this for logging or alerting.

Matches on error type: `rate_limit`, `authentication_failed`, `billing_error`, `invalid_request`, `server_error`, `max_output_tokens`, or `unknown`. Omit the matcher to fire on all error types.

#### StopFailure input

In addition to the [common input fields](#common-input-fields), StopFailure hooks receive `error_type` and `error_message`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "hook_event_name": "StopFailure",
  "error_type": "rate_limit",
  "error_message": "Rate limit exceeded. Please try again later."
}
```

#### StopFailure decision control

StopFailure hooks have no decision control. This hook fires for logging and observability purposes only. Output and exit codes are ignored.

### TeammateIdle

Runs when an [agent team](/en/agent-teams) teammate is about to go idle, meaning the teammate has finished its current task but hasn't been assigned a new one. Use this to log idle states, assign new tasks, or prevent teammates from going idle.

Matches on tool name, but TeammateIdle has no matcher support. This hook always fires.

#### TeammateIdle input

In addition to the [common input fields](#common-input-fields), TeammateIdle hooks receive `teammate_id`, `teammate_name`, and optionally `team_name`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "TeammateIdle",
  "teammate_id": "mate-abc123",
  "teammate_name": "reviewer",
  "team_name": "my-team"
}
```

#### TeammateIdle decision control

TeammateIdle hooks can prevent the teammate from going idle. Exit with code 2 to block, or return JSON with `{"continue": false}`. Unlike `Stop` hooks which block the entire response, a blocked TeammateIdle keeps the teammate active and working:

| Field               | Description                                                                   |
| :------------------ | :---------------------------------------------------------------------------- |
| `continue`          | If `false`, prevents the teammate from going idle; they continue working      |
| `additionalContext` | Additional context or task instructions for the teammate                      |

```json theme={null}
{
  "continue": false,
  "hookSpecificOutput": {
    "hookEventName": "TeammateIdle",
    "additionalContext": "Review the implementation for security issues"
  }
}
```

### ConfigChange

Runs when a configuration file changes during a session. This includes changes to `.claude/settings.json`, `.claude/settings.local.json`, CLAUDE.md files, and other configuration sources. Use this to validate configuration changes or prevent unsafe configurations from being applied.

Matches on configuration source: `user_settings`, `project_settings`, `local_settings`, `policy_settings`, or `skills`. Omit the matcher to run on all configuration changes.

#### ConfigChange input

In addition to the [common input fields](#common-input-fields), ConfigChange hooks receive `config_source` and optionally `file_path`, `config_keys`, and `change_type`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "ConfigChange",
  "config_source": "project_settings",
  "file_path": "/Users/my-project/.claude/settings.json",
  "config_keys": ["permissions", "hooks"],
  "change_type": "modified"
}
```

#### ConfigChange decision control

ConfigChange hooks can prevent configuration changes from taking effect (except for policy settings, which always apply). Return a JSON object with `decision` set to `"block"`:

| Field    | Description                                                      |
| :------- | :--------------------------------------------------------------- |
| `decision` | `"block"` reverts the configuration change                     |
| `reason`   | Explanation shown to Claude when configuration is blocked       |

```json theme={null}
{
  "decision": "block",
  "reason": "Configuration contains invalid hook syntax"
}
```

### CwdChanged

Runs when the current working directory changes, for example when Claude executes a `cd` command. Use this for reactive environment management, such as loading per-directory environment files with tools like `direnv`, or updating development environment state.

CwdChanged hooks have no matcher support and fire on every directory change.

#### CwdChanged input

In addition to the [common input fields](#common-input-fields), CwdChanged hooks receive `previous_cwd` and `new_cwd`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/my-project/packages/core",
  "hook_event_name": "CwdChanged",
  "previous_cwd": "/Users/my-project",
  "new_cwd": "/Users/my-project/packages/core"
}
```

#### CwdChanged decision control

CwdChanged hooks have no decision control, but they have access to the `CLAUDE_ENV_FILE` environment variable, which lets you persist environment variables for subsequent tool calls (see [Persist environment variables](#persist-environment-variables) in the SessionStart section).

CwdChanged hooks cannot block the directory change. If you want to trigger environment setup or logging on directory changes, this is the event to use.

### FileChanged

Runs when a watched file changes on disk during a session. Use this for reactive file handling: for example, re-installing dependencies when `package.json` changes, or rebuilding when a source file changes.

The `matcher` field specifies which filenames or glob patterns to watch. Separate multiple patterns with `|`. Literal filenames like `.env` and `.envrc` are compared case-sensitively and exactly, without glob expansion. Patterns containing glob characters like `*`, `?`, `[`, or `]` are treated as glob patterns. For example:

```json theme={null}
{
  "hooks": {
    "FileChanged": [
      {
        "matcher": ".env|.envrc",
        "hooks": [...]
      },
      {
        "matcher": "*.lock",
        "hooks": [...]
      }
    ]
  }
}
```

This matches exact filenames `.env` and `.envrc`, and any file ending in `.lock`.

#### FileChanged input

In addition to the [common input fields](#common-input-fields), FileChanged hooks receive `file_path`, `relative_path`, and `change_type`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/my-project",
  "hook_event_name": "FileChanged",
  "file_path": "/Users/my-project/.env",
  "relative_path": ".env",
  "change_type": "modified"
}
```

#### FileChanged decision control

FileChanged hooks have no decision control, but they have access to the `CLAUDE_ENV_FILE` environment variable (see [Persist environment variables](#persist-environment-variables)).

FileChanged hooks cannot block file changes. They run for observability and side effects.

### WorktreeCreate

Runs when a worktree is being created via `--worktree` or `isolation: "worktree"`. By default, Claude Code creates a git worktree. This hook lets you replace that behavior with a custom setup strategy.

WorktreeCreate hooks do not support matchers and fire on every worktree creation.

#### WorktreeCreate input

In addition to the [common input fields](#common-input-fields), WorktreeCreate hooks receive `worktree_id`, `branch_name`, `source_path`, and optionally `is_temporary`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/my-project",
  "hook_event_name": "WorktreeCreate",
  "worktree_id": "wt-abc123",
  "branch_name": "feature/new-api",
  "source_path": "/Users/my-project",
  "is_temporary": false
}
```

#### WorktreeCreate decision control

WorktreeCreate hooks can take over worktree creation by printing a path to stdout or returning one via JSON. Any non-zero exit code fails creation:

| Result format | Behavior                                                                |
| :------------ | :---------------------------------------------------------------------- |
| Exit code 0 + path on stdout | Uses the provided path as the worktree                                  |
| JSON with `hookSpecificOutput.worktreePath` | Uses the provided path as the worktree                                  |
| Exit code non-zero | Fails worktree creation; the hook is responsible for any cleanup        |

For example, a hook that creates a Docker container instead of a git worktree:

```bash theme={null}
#!/bin/bash
WORKTREE_ID=$1
CONTAINER_ID=$(docker run -d -v "$source_path":/workspace my-image)
echo "/var/lib/docker/volumes/$CONTAINER_ID/_data"
exit 0
```

Or returning JSON:

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "WorktreeCreate",
    "worktreePath": "/path/to/worktree"
  }
}
```

### WorktreeRemove

Runs when a worktree is being removed, either at session exit or when a subagent finishes. Use this for cleanup when a custom worktree hook takes over worktree creation.

WorktreeRemove hooks do not support matchers and fire on every worktree removal.

#### WorktreeRemove input

In addition to the [common input fields](#common-input-fields), WorktreeRemove hooks receive `worktree_id`, `worktree_path`, `branch_name`, and `reason`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/my-project",
  "hook_event_name": "WorktreeRemove",
  "worktree_id": "wt-abc123",
  "worktree_path": "/path/to/worktree",
  "branch_name": "feature/new-api",
  "reason": "session_end"
}
```

#### WorktreeRemove decision control

WorktreeRemove hooks have no decision control. Failures are logged in debug mode only. Use this for cleanup operations.

### PreCompact

Runs before context compaction begins. Use this to prevent compaction if certain conditions aren't met, or to log when compaction is about to happen.

Matches on what triggered compaction: `manual` (user-initiated) or `auto` (automatic).

#### PreCompact input

In addition to the [common input fields](#common-input-fields), PreCompact hooks receive `trigger` indicating what caused the compaction.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PreCompact",
  "trigger": "auto"
}
```

#### PreCompact decision control

PreCompact hooks can block compaction. Return a JSON object with `decision` set to `"block"`:

| Field    | Description                                  |
| :------- | :-------------------------------------------- |
| `decision` | `"block"` prevents context compaction        |
| `reason`   | Explanation shown to Claude when blocked     |

```json theme={null}
{
  "decision": "block",
  "reason": "Tests are running, cannot compact now"
}
```

### PostCompact

Runs after context compaction completes. Use this for logging or cleanup after compaction.

Matches on what triggered compaction: `manual` or `auto`.

#### PostCompact input

In addition to the [common input fields](#common-input-fields), PostCompact hooks receive `trigger` indicating what caused the compaction.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PostCompact",
  "trigger": "auto"
}
```

#### PostCompact decision control

PostCompact hooks have no decision control. Use this for observability and logging.

### Elicitation

Runs when an MCP server requests user input during a tool call. This is the hook point for validating or intercepting MCP elicitation requests.

Matches on MCP server name (your configured MCP server names). Omit the matcher to run on all elicitation requests.

#### Elicitation input

In addition to the [common input fields](#common-input-fields), Elicitation hooks receive `mcp_server_name`, `tool_name`, `form`, and optionally `message` and `description`.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Elicitation",
  "mcp_server_name": "my-server",
  "tool_name": "my-server-tool",
  "form": {
    "fields": [
      {
        "name": "username",
        "type": "string",
        "description": "Enter username"
      }
    ]
  },
  "message": "Please provide user information",
  "description": "User input required"
}
```

#### Elicitation decision control

Elicitation hooks can accept, decline, or cancel the elicitation. Return a JSON object with `hookSpecificOutput.action`:

| Field      | Values                            | Description                                                     |
| :--------- | :-------------------------------- | :-------------------------------------------------------------- |
| `action`   | `accept`, `decline`, `cancel`     | How to handle the elicitation                                   |
| `content`  | object mapping field names to values | For `accept`: the form field values to submit                    |

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "Elicitation",
    "action": "accept",
    "content": {
      "username": "user@example.com"
    }
  }
}
```

### ElicitationResult

Runs after a user responds to an MCP elicitation, before the response is sent back to the server. Use this to validate, transform, or block responses.

Matches on MCP server name, same values as Elicitation.

#### ElicitationResult input

In addition to the [common input fields](#common-input-fields), ElicitationResult hooks receive `mcp_server_name`, `tool_name`, `form`, and `user_response` (object mapping field names to values).

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "ElicitationResult",
  "mcp_server_name": "my-server",
  "tool_name": "my-server-tool",
  "form": {
    "fields": [
      {
        "name": "username",
        "type": "string"
      }
    ]
  },
  "user_response": {
    "username": "user@example.com"
  }
}
```

#### ElicitationResult decision control

ElicitationResult hooks can modify the response or block it entirely. Return a JSON object with `hookSpecificOutput.action`:

| Field     | Values                            | Description                                                             |
| :-------- | :-------------------------------- | :---------------------------------------------------------------------- |
| `action`  | `accept`, `decline`, `cancel`     | How to handle the response                                              |
| `content` | object mapping field names to values | For `accept`: modified field values (overrides user response)            |

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "ElicitationResult",
    "action": "accept",
    "content": {
      "username": "sanitized@example.com"
    }
  }
}
```

### SessionEnd

Runs when a session terminates. Use this for cleanup, logging, archival, or sending completion notifications.

Matches on why the session ended: `clear`, `resume`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, or `other`.

#### SessionEnd input

In addition to the [common input fields](#common-input-fields), SessionEnd hooks receive `end_reason` indicating why the session ended.

```json theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "hook_event_name": "SessionEnd",
  "end_reason": "logout"
}
```

#### SessionEnd decision control

SessionEnd hooks have no decision control. Use this for observability and cleanup.