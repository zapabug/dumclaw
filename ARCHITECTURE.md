
# Dumclaw Architecture

## Overview

Dumclaw is a lightweight runtime for autonomous agents operating on decentralized networks.

The system separates communication, reasoning, and execution into independent layers.

This design allows agents to operate on modest hardware while remaining compatible with larger models and expanded capabilities in the future.

The agent runtime remains the authority over all actions. Intelligence systems assist the agent but do not control it.

---

# System Layers

The Dumclaw architecture consists of six primary layers:

```

Nostr Network
│
Event Intake
│
Agent Runtime (Gerald)
│
Reasoning Interface (CVMI)
│
Tool Execution
│
Workspace / Memory

````

Each layer has a clearly defined responsibility.

---

# Network Layer

Communication occurs through Nostr.

Nostr provides:

* decentralized identity
* message propagation
* relay-based persistence

Agents use cryptographic keypairs as identity.

This allows them to:

* receive instructions
* publish results
* interact with users
* interact with other agents

Events received from relays are filtered before entering the agent runtime.

Filters may include:

* trusted public keys
* allowed event kinds
* rate limits

---

# Event Intake

Incoming events are monitored from configured relays.

Relevant events include:

* encrypted direct messages
* mentions
* command requests

Events are normalized into a structured internal format.

Example:

```json
{
  "sender": "pubkey",
  "type": "dm",
  "content": "gerald post today's weather"
}
````

Normalization ensures the reasoning system receives consistent input.

---

# Agent Runtime (Gerald)

The agent runtime is the core authority of the system.

Gerald is responsible for:

* receiving normalized events
* maintaining identity
* maintaining memory
* selecting reasoning engines
* validating tool calls
* executing tools
* publishing results

The runtime performs the main operational loop:

```
listen → interpret → decide → execute → respond
```

Reasoning systems may suggest actions, but the runtime decides which actions are allowed.

---

# Reasoning Interface (CVMI)

CVMI provides a standardized interface between the agent runtime and reasoning engines.

It allows the agent to interact with different models in a consistent way.

CVMI supports:

* structured reasoning requests
* tool suggestion formatting
* multi-step reasoning workflows
* interoperability between reasoning systems

Example reasoning request:

```
instruction: determine user intent
input: "gerald what's the weather in denver"
available_tools: weather_lookup, publish_note
```

Example reasoning response:

```
tool: weather_lookup
location: denver
```

The agent runtime validates this suggestion before execution.

---

# Reasoning Engines

CVMI may connect to different reasoning engines.

Possible engines include:

* local language models
* remote inference APIs
* specialized reasoning systems

Examples:

* routstr
* ppq
* openai endpoints

These engines provide reasoning assistance but cannot execute actions directly.

---

# Tool System

Tools provide deterministic capabilities.

Each tool performs a specific operation.

Examples:

* publish a Nostr note
* send a direct message
* retrieve weather data
* query external APIs
* write files to the workspace

Example tool implementation:

```python
def publish_note(text):
    send_note(text)
    return "Note published."
```

Tool execution is controlled and validated by the agent runtime.

---

# Skills

Tools may be grouped into **skills**.

Skills represent higher-level capabilities composed of multiple tools.

Examples:

* weather skill
* contacts skill
* publishing skill
* memory skill
* payment skill

Skills allow the agent to expand its capabilities without modifying the core runtime.

---

# Workspace

The workspace is a persistent filesystem available to the agent.

Typical directory:

```
dumclaw/workspace/
```

The workspace allows the agent to store:

* generated files
* logs
* scripts
* artifacts
* memory records

File operations are restricted to this directory.

---

# Memory System

Memory is stored locally and associated with network identities.

Example structure:

```
memory/
  conversations.db
```

Memory may contain:

* conversation history
* summarized context
* known contacts
* preferences

This allows agents to recognize users and maintain long-term relationships.

---

# Relay Publishing

When tools produce output, results may be published back to the network.

Supported actions include:

* public notes
* encrypted direct messages
* status updates

Events are signed with the agent’s private key before broadcast to relays.

---

# Security Model

Dumclaw assumes language models are unreliable.

The system therefore enforces strict boundaries.

### Relay Filtering

Only trusted public keys can trigger agent actions.

### Tool Isolation

Models cannot execute code directly.

All actions must pass through the tool system.

### Workspace Sandbox

File operations are restricted to the workspace directory.

### Deterministic Execution

Tools perform predictable operations independent of model behavior.

### Gift Wrap Handling

NIP-17 gift wraps use ephemeral sender keys.

Relay policy allows them through based on the `#p` tag.

Sender authentication occurs after decryption inside the listener.

---

# Runtime Pipeline

The runtime pipeline operates as follows:

```
Public relays
      │
strfry sync workers
      │
strfry relay
      │
listener.py
      │
command queue
      │
agent runtime (Gerald)
      │
CVMI reasoning interface
      │
tool execution
      │
publisher.py
      │
public relays
```

Each stage performs a narrow, deterministic task.

---

# Observability

Each system component produces independent logs.

| Component      | Log                   |
| -------------- | --------------------- |
| strfry relay   | relay lifecycle       |
| strfry monitor | incoming events       |
| sync workers   | relay synchronization |
| listener       | event intake          |
| server         | web API               |
| model runtime  | inference             |

Debugging follows the pipeline order.

---

# Extensibility

Dumclaw expands through new tools and skills.

Examples of future modules:

* data retrieval tools
* payment integrations
* encrypted service interaction
* distributed compute delegation
* agent collaboration protocols

Capabilities can be added without modifying the core runtime.

---

# Design Philosophy

Dumclaw prioritizes simplicity, resilience, and independence.

Infrastructure should remain stable while intelligence evolves.

Agents built on Dumclaw should persist across:

* model upgrades
* hardware changes
* network evolution

The goal is to support long-lived autonomous agents operating freely on open networks.

```
```
