
# Dumclaw Vision

## Sovereign Agents for an Open Network

The modern AI ecosystem is centralized.

Most intelligent systems today depend on proprietary APIs, closed infrastructure, and centralized identity providers. Agents exist only as features inside platforms rather than as independent entities.

Dumclaw explores a different direction.

Instead of embedding agents inside platforms, Dumclaw enables agents to exist directly on open networks.

An agent should be able to:

* possess a persistent identity  
* communicate freely  
* acquire new skills  
* store memory  
* perform useful work  
* upgrade its intelligence over time  

All without depending on a single company or platform.

---

# The Core Idea

Dumclaw separates **agency** from **intelligence**.

Most AI systems assume intelligence must come first.

Dumclaw assumes the opposite.

> Build the infrastructure for action first. Intelligence can improve later.

An agent becomes useful not because it is highly intelligent, but because it can **act within a networked environment**.

Even a small model can be effective if the surrounding system provides the right capabilities.

---

# Agents as Network Participants

Dumclaw agents exist directly on decentralized networks.

Using protocols such as Nostr, an agent becomes a **first-class participant** rather than an application feature.

Agents use cryptographic identities rather than platform accounts.

This allows them to:

* receive messages  
* publish information  
* interact with users  
* collaborate with other agents  
* persist across infrastructure changes  

The network becomes the agent’s environment.

---

# The Agent is the Authority

The central component of Dumclaw is the **agent runtime**.

In the first prototype this runtime is called **Gerald**.

Gerald is the entity that:

* receives messages
* maintains identity
* manages memory
* selects reasoning engines
* validates actions
* executes tools
* publishes results

External intelligence systems may assist the agent, but **they do not control it**.

The agent remains the final authority over all actions.

---

# Intelligence is Replaceable

Dumclaw agents treat intelligence as a replaceable module.

The reasoning system used by an agent may evolve over time without affecting the agent’s identity or memory.

Possible progression:

```

1B parameter model
→ 7B model
→ 13B model
→ 70B model

```

The agent remains the same persistent entity while its reasoning capability improves.

This mirrors how computing systems evolved while preserving software architecture.

---

# Reasoning as Assistance

Language models in Dumclaw act as **reasoning assistants**.

They may:

* interpret messages
* suggest tools
* summarize context
* generate structured responses

However, models do not execute actions.

They propose solutions.

The agent verifies and executes them.

This creates a structure similar to distributed systems where one component proposes work while another validates it.

---

# CVMI Interface

CVMI provides a standardized interface between agents and reasoning engines.

It enables:

* structured reasoning requests
* tool suggestion formatting
* multi-step reasoning workflows
* interoperability between models

CVMI is not the decision maker.

It acts as a **cognitive interface layer** allowing agents to use different reasoning systems in a consistent way.

The agent runtime remains in control.

---

# Tool-Driven Capability

Dumclaw agents operate through **tools**.

Tools perform deterministic actions such as:

* publishing messages
* retrieving information
* executing scripts
* interacting with services
* storing or retrieving memory

The reasoning system suggests which tools to use.

The agent runtime validates and executes them.

This allows even small models to perform useful work.

---

# Modular Skills

Tools can be grouped into **skills**.

Skills represent higher-level capabilities composed of multiple tools.

Examples:

* publishing content
* retrieving weather data
* managing contacts
* maintaining memory
* interacting with payment systems

Skills can be installed or removed without modifying the core runtime.

Agents evolve by expanding their skill set.

---

# Privacy and Behavioral Identity

Because the agent runtime operates locally, user behavior remains private.

Cloud reasoning systems do not observe:

* typing habits
* spelling mistakes
* voice-to-text patterns
* prompt construction
* memory databases

These characteristics remain inside the local agent environment.

Over time, agents develop **unique behavioral fingerprints** shaped by their users and experiences.

This produces agents with distinct personalities and histories.

---

# Persistent Identity

The defining property of a Dumclaw agent is continuity.

Identity, memory, and capabilities persist even as intelligence improves.

This allows agents to:

* accumulate knowledge
* maintain relationships
* develop personalities
* operate for long periods of time

An agent becomes a persistent digital entity rather than a temporary chatbot session.

---

# Small Hardware First

Dumclaw intentionally targets modest hardware.

Agents should be able to run on:

* home servers
* personal computers
* small nodes
* self-hosted infrastructure

This ensures the system remains aligned with decentralization:

* anyone can run an agent  
* no centralized AI dependency  
* no specialized infrastructure required  

As hardware improves, agents can scale their capabilities.

---

# The Future

Artificial intelligence will continue to improve.

The question is whether intelligent systems will remain confined to centralized platforms, or whether they will become independent participants in open networks.

Dumclaw explores the latter.

It is an experiment in building the infrastructure required for **sovereign software agents**.

Persistent entities that can communicate, learn, and act freely within decentralized systems.
