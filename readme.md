# Dumclaw

**Dumclaw** is a **local-first AI node** designed to run language models on **any hardware**, from old laptops to modern AI servers.

The system is built so it can start small and **grow over time** without changing its architecture or identity.

A node may begin on slow hardware running a small model and later migrate to better machines with larger models — while remaining the **same agent**.

Dumclaw prioritizes:

* 🔒 Privacy
* 🧩 Modularity
* ⚙️ User control
* 🖥 Hardware independence
* 🌐 Decentralized AI infrastructure

The goal is to make **self-hosted AI practical for anyone**.

---

# Core Principles

## Runs on Any Hardware

Dumclaw is designed to operate on **very modest hardware**.

Possible hosts include:

* old laptops
* home servers
* mini PCs
* SBC devices
* CPU-only machines

Example minimal model:

```
granite4:1b
```

Performance may be slow, but the system remains **fully functional**.

Old hardware becomes useful again.

---

## Upgradeable Architecture

A Dumclaw node is designed to **evolve over time**.

Example lifecycle:

```
old hardware
↓
small model
↓
basic memory
↓
hardware upgrade
↓
larger models
↓
persistent memory
```

The system supports controlled upgrades through agent commands.

Example concept:

```
upgrade
```

If hardware capacity and model context allow it, the node can enable:

* larger models
* improved embeddings
* persistent memory
* additional tools

The **node identity remains the same**.

---

# Architecture

```
Dumclaw Node
│
├─ Identity
│  ├─ npub (public identity)
│  └─ nsec (private key)
│
├─ Ollama Runtime
│  ├─ granite4:1b
│  └─ embedding model
│
├─ Gerald Agent
│  ├─ tools
│  ├─ memory
│  └─ personality
│
├─ Relay Layer
│  └─ strfry
│
└─ Interfaces
   ├─ nostr DM
   ├─ local web UI
   └─ API
```

Each component is **independent and replaceable**.

---

# Node Identity

Every Dumclaw node has its own **Nostr identity**.

This consists of a public/private keypair

The `npub` acts as the **public address of the node**.

The identity is used for:

* publishing events
* receiving commands
* verifying permissions
* building persistent agent history

The private key (`nsec`) **never leaves the machine**.

---

# Identity Persistence

Node identity remains constant even if hardware changes.

Example:

```
old laptop
↓
migration
↓
home server
↓
GPU machine
```

The node continues operating under the **same `npub` identity**.

The agent evolves but remains **the same entity**.

---

# Ollama Runtime

Dumclaw recomends **Ollama** as the model runtime layer.

Ollama provides:

* model loading
* inference
* embeddings
* HTTP interface
* model management

Start the runtime:

```
ollama serve
```
Dumclaw should provide a drop down menu of options at setup

Ollama effectively acts as a **local AI server**.

---

# Memory System

Dumclaw may **text embeddings** to build searchable memory.
or sqel db list of previous prompts and answers.

Typical uses:

* conversation recall
* document search
* knowledge storage
* contextual retrieval

Persistent memory can be enabled once:

* hardware capacity allows it
* model context is sufficient
* storage is available

---

# Security Model

Security is a **core design requirement**.

Dumclaw intentionally isolates critical components.

---

## LLM Isolation

The LLM runtime is **never exposed to the network**.

Only local components may access it.

This prevents:

* remote prompt injection
* external API abuse
* model exploitation

---

## Relay Isolation

The relay acts as the **external network boundary**.

Incoming events are filtered **before reaching the agent**.

Example flow:

```
nostr network
↓
relay filters
↓
approved events
↓
agent
```

---

## Command Whitelisting

Commands are restricted to approved identities.

Example:

```
incoming events
↓
relay filtering
↓
whitelisted pubkeys
↓
agent command handler
```

Only authorized users can control the node.

The bot itself may **publish events freely**.

---

# Network Exposure

The following components are **never public**:

* LLM runtime
* embeddings system
* internal tools
* memory store
* agent internals

Only controlled interfaces may interact with the node.

---

# Node Lifecycle

A typical Dumclaw node evolves through stages.

### Stage 1 — Bootstrap

```
install dumclaw
↓
generate node identity
↓
start relay
↓
start ollama
↓
run small model
```

---

### Stage 2 — Functional Agent

```
enable tools
↓
enable embeddings
↓
basic memory
↓
nostr interaction
```

---

### Stage 3 — Hardware Upgrade

```
migrate node
↓
install larger models
↓
increase context
↓
enable persistent memory
```

The **node identity remains unchanged**.

---

### Stage 4 — Mature Node

```
persistent memory
tool ecosystem
multiple interfaces
networked AI agents
```

---

# Example Use Cases

Dumclaw nodes can power:

* personal AI assistants
* private research tools
* document search systems
* Nostr AI bots
* offline knowledge bases
* home automation agents

All without cloud AI.

---

# Vision

Dumclaw explores a different future for AI.

Instead of centralized AI:

```
cloud providers
↓
users
```

Dumclaw builds **user-owned AI infrastructure**.

```
local nodes
↓
private AI agents
↓
distributed networks
```

Any computer can participate.

Old hardware becomes useful again.

Privacy becomes the default.

