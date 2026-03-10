# Dumclaw Architecture

## Overview

Dumclaw is a lightweight runtime for autonomous agents operating on decentralized networks.

The system is intentionally minimal. It separates communication, reasoning, and execution into clearly defined components.

The architecture allows agents to run on modest hardware while remaining compatible with larger models and expanded capabilities in the future.

---

# System Components

Dumclaw consists of five core layers:

```text
Nostr Network
      │
Event Intake
      │
Agent Loop
      │
Model Reasoning
      │
Tool Execution
      │
Workspace
```

Each layer has a specific responsibility.

---

# Network Layer

Communication occurs over Nostr.

Nostr provides:

* decentralized identity
* message propagation
* event persistence through relays

Agents use their cryptographic keypair as identity.

Events received from relays are filtered before entering the agent loop.

This prevents arbitrary public messages from influencing the agent.

Typical filters include:

* whitelist of trusted public keys
* specific event kinds
* rate limits

This ensures the agent only reacts to trusted instructions.

---

# Event Intake

Incoming events are monitored from configured relays.

Relevant events include:

* direct messages
* mentions
* command requests

Events are normalized into a structured internal format before being passed to the agent.

Example event structure:

```json
{
  "sender": "pubkey",
  "type": "dm",
  "content": "gerald post todays weather"
}
```

The intake layer ensures the agent only processes valid and authorized messages.

---

# Agent Loop

The agent loop is the central runtime process.

It performs the following cycle:

```text
listen → interpret → decide → execute → respond
```

1. Listen for incoming events
2. Interpret the instruction
3. Determine the appropriate tool
4. Execute the tool
5. Publish results if required

The loop runs continuously and acts as the orchestrator between the network, the model, and the tools.

---

# Model Layer

The language model is responsible for interpreting requests and selecting appropriate actions.

The model does **not execute actions directly**.

Instead it produces structured output indicating which tool should be used.

Example model output:

```text
tool: publish
text: another morning another request for weather...
```

This design provides two advantages:

* smaller models can be used effectively
* tool execution remains deterministic

The model can be replaced without affecting the surrounding infrastructure.

Possible inference engines include:

* llama.cpp
* Ollama

---

# Tool System

Tools provide the agent with real capabilities.

Each tool performs a specific deterministic function.

Example tools include:

* publish a note
* send a direct message
* write files to the workspace
* retrieve external data

Tools are implemented as modular Python functions.

Example:

```python
def publish(text):
    send_note(text)
    return "Note published."
```

The agent selects tools based on model output.

Execution is validated before running to prevent malformed actions.

---

# Workspace

The workspace is a persistent filesystem available to the agent.

Typical directory:

```text
dumclaw/workspace/
```

The workspace allows the agent to store:

* generated files
* logs
* notes
* scripts
* long-term memory

This enables agents to accumulate artifacts over time.

The workspace also acts as a boundary for file operations, preventing the agent from accessing the broader system.

---

# Relay Publishing

When tools produce output, results can be published back to the network.

Publishing occurs through Nostr events.

Supported actions include:

* public notes
* direct messages
* status updates

Events are signed with the agent’s private key before being broadcast to relays.

---

# Security Model

Dumclaw assumes that language models are unreliable.

The system therefore enforces strict boundaries.

Key safeguards:

### Relay Filtering

Only trusted public keys can trigger agent actions.

### Tool Isolation

The model cannot directly execute code.

All actions must pass through the tool layer.

### Workspace Sandbox

File operations are restricted to the workspace directory.

### Deterministic Execution

Tools perform predictable operations independent of the model.

These boundaries reduce the risk of prompt injection or unintended actions.

---

# Extensibility

Dumclaw is designed to grow through tools and modules.

New capabilities can be added without modifying the core agent loop.

Examples:

* data retrieval tools
* payment integrations
* encrypted communication
* distributed compute delegation

The system evolves by expanding the available tools.

---

# Future Architecture Extensions

Planned architectural expansions include:

* skill installation system
* encrypted task exchange
* agent-to-agent communication
* payment-enabled tool execution
* persistent memory indexing
* remote compute delegation

These features can be layered onto the existing architecture without disrupting the core system.

---

# Design Philosophy

Dumclaw prioritizes simplicity and resilience.

The architecture assumes that intelligence will improve over time, but infrastructure should remain stable.

Agents built on this system should be able to persist across hardware upgrades, model changes, and network evolution.

The result is a framework for long-lived autonomous agents operating on open networks.
