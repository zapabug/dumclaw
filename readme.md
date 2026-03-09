# Dumclaw

**Dumclaw** is a lightweight framework for running autonomous agents on decentralized infrastructure.

It is designed to operate on small hardware, communicate through the Nostr network, and execute real-world actions through modular tools.

The project explores a simple idea:

> An agent does not need to be intelligent if it has the right tools.

Instead of relying on large centralized AI services, Dumclaw focuses on building the **infrastructure layer** that allows agents to exist independently of any single model provider.

---

# Vision

Modern AI systems are tightly coupled to centralized APIs and large compute providers.

Dumclaw explores an alternative architecture built around open protocols and replaceable intelligence.

Core principles:

* **Decentralized identity**
* **Local compute**
* **Tool-driven capability**
* **Modular intelligence**

The intelligence layer can evolve over time, but the agent's identity, tools, and memory remain persistent.

Protocols like Nostr enable agents to exist as independent network participants rather than application features.

Payments and economic interactions can eventually be enabled through systems like Lightning Network or Cashu.

---

# Current MVP

The current version focuses on a minimal working agent.

The agent, **Gerald**, demonstrates a simple autonomous workflow.

1. Gerald listens for incoming Nostr messages.
2. Messages from a whitelist are interpreted by a small language model.
3. The model selects a tool.
4. The tool performs the action.
5. Results can be published back to Nostr.

Example interaction:

User sends DM:

```
gerald post todays weather
```

Agent workflow:

```
receive dm
→ interpret request
→ call weather tool
→ publish nostr note
```

Result:

```
another morning another request for weather...
apparently humans require umbrellas again
```

This demonstrates:

* decentralized messaging
* tool-driven actions
* autonomous publishing
* persistent identity

---

# Architecture

Dumclaw is intentionally simple.

```
Nostr Relays
      │
Event Filter (Whitelist)
      │
   Gerald Agent
      │
 Language Model
      │
   Tool System
      │
  Workspace
```

### Components

**Agent**

The agent interprets instructions and decides which tools to execute.

**Tools**

Tools perform deterministic actions such as:

* publishing Nostr notes
* sending direct messages
* interacting with local files
* calling external services

**Workspace**

A persistent filesystem where the agent can store artifacts, scripts, and memory.

**Model**

The language model is replaceable and can scale with available hardware.

Small models can perform routing and interpretation, while larger models can provide deeper reasoning.

---

# Why Build This?

Most AI agent frameworks assume access to powerful models hosted by centralized providers.

Dumclaw takes the opposite approach:

Start with minimal hardware and minimal intelligence, then grow capabilities through tools and modular upgrades.

This allows the same agent identity to persist as compute improves.

A node running a small model today could later upgrade to a larger model without redesigning the system.

---

# Design Goals

* Run on modest hardware
* Operate over decentralized protocols
* Remain model-agnostic
* Allow tools to expand capabilities
* Preserve persistent identity

The long-term goal is to enable **sovereign software agents** that can operate independently across open networks.

---

# Future Directions

Planned capabilities include:

* skill marketplace
* encrypted tool interactions
* payment-enabled agents
* distributed compute delegation
* long-term agent memory
* dynamic tool installation

As models improve, the same agent infrastructure can support increasingly capable systems.

---

# Gerald

Gerald is the first Dumclaw agent.

He is intentionally slow, grumpy, and somewhat reluctant to help humans.

His job is simple:

Read messages, interpret requests, and execute tools.

---

# Status

Dumclaw is currently an early prototype focused on proving the architecture.

The goal of the MVP is to demonstrate that a minimal autonomous agent can:

* receive instructions through Nostr
* interpret requests locally
* execute real actions through tools
* publish results back to the network

---

# Contributing

The system is intentionally modular.

Future contributors can expand Dumclaw by adding new tools, skills, and execution environments.

---

# License

Open source.

