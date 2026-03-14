
# DumClaw Tool Implementation: Complete Analysis

## Summary

Your Nostr communication layer is solid — Gerald handles NIP-04, NIP-17 gift wraps, pubkey whitelisting, deduplication, command queuing, and reconnection. The bridge relays from public relays to local strfry. That's stable ground.

## The Gap

The tool system is ad-hoc and the CVMI layer is empty. Here's exactly what needs building, in priority order.

## Current State (What You Have)

```
┌─────────────────────────────────────────────┐
│ WORKING                                      │
├─────────────────────────────────────────────┤
│ ✅ NIP-04 + NIP-17 DM receive/decrypt       │
│ ✅ NIP-17 gift wrap send (publisher.py)      │
│ ✅ Pubkey whitelist (ALLOWED_PUBKEYS)        │
│ ✅ SQLite dedup + prune                      │
│ ✅ Command queue (decoupled from WS)         │
│ ✅ Bridge (nos.lol → strfry → listener)      │
│ ✅ LLM action routing (decide_action)        │
│ ✅ Gerald persona generation                 │
├─────────────────────────────────────────────┤
│ INCOMPLETE / MISSING                         │
├─────────────────────────────────────────────┤
│ ❌ nostr/tools/cvmi.py — empty file          │
│ ❌ No tool schema / manifest format          │
│ ❌ No skill registry                         │
│ ❌ No tool validation / safeguards           │
│ ❌ No structured tool results                │
│ ❌ Tools hardcoded in llm.py + listener.py   │
│ ❌ No rate limiting on tool execution        │
│ ❌ No audit logging of tool calls            │
└─────────────────────────────────────────────┘
```

## Tool Schema (OpenClaw + CVMI Compatible)

The key insight from your [`docs/tool implementation`](docs/tool%20implementation:39) doc is correct: **tool = executable, skill = instructions**. But for Granite-1B you need the schema to be minimal JSON, not markdown.

### Recommended Schema Format

Each tool gets a `manifest.json` that is compatible with three ecosystems:

```json
{
  "name": "weather",
  "version": "1.0.0",
  "description": "Fetch current weather conditions",
  "capability_level": "S0",
  "actions": {
    "current": {
      "description": "Get current weather for a location",
      "parameters": {
        "city": { "type": "string", "required": false, "default": "auto" }
      },
      "returns": { "type": "string" },
      "side_effects": false
    }
  }
}
```

**Why this format works across ecosystems:**

| Field | OpenClaw | CVMI | NIP-90 DVM |
|-------|----------|------|------------|
| `name` | skill name | tool identifier | `kind:31990` d-tag |
| `description` | skill.md content | tool description | `kind:31990` content |
| `actions` | CLI subcommands | CVMI actions | job request kinds |
| `capability_level` | N/A (your invention) | model tier filter | N/A |
| `parameters` | CLI args | structured input | `i` + `param` tags |
| `side_effects` | N/A | **safeguard flag** | N/A |

The `side_effects` field is critical — it tells the runtime whether a tool **reads** (safe) or **writes** (needs confirmation/validation).

## Safeguards to Implement

These are the guardrails between the LLM's suggestions and actual execution:

### A. Tool Permission Tiers

```
┌──────────────┬────────────────────────────────────┐
│ Tier         │ Behavior                           │
├──────────────┼────────────────────────────────────┤
│ READ-ONLY    │ Execute immediately (weather, etc) │
│ WRITE-LOCAL  │ Execute with audit log (notes)     │
│ WRITE-REMOTE │ Require sender confirmation         │
│ DANGEROUS    │ Admin-only + double confirmation    │
└──────────────┴────────────────────────────────────┘
```

Map these to your existing tools:

- `get_weather()` → **READ-ONLY** (no side effects)
- `send_note()` → **WRITE-REMOTE** (publishes to Nostr — permanent, public)
- `send_dm()` → **WRITE-REMOTE** (sends to another person)
- `publish()` in [`nostr/tools/publish.py`](nostr/tools/publish.py:3) → **WRITE-REMOTE**

### B. Rate Limiting

Your [`command_worker()`](listener.py:97) processes commands sequentially from the queue, which is good. But there's no rate limit. A whitelisted user could spam Gerald with 100 DMs and queue 100 LLM calls + 100 Nostr publishes.

Add per-sender rate limiting:

```
sender_cooldowns = {}
COOLDOWN_SECONDS = 10
MAX_QUEUE_DEPTH = 20
```

### C. Output Sanitization

Right now [`gerald_reply()`](llm.py:113) feeds raw LLM output directly to [`send_note()`](nostr/publisher.py:142) and [`send_dm()`](nostr/publisher.py:170). A 1B model can hallucinate anything — including content that looks like nsec keys, URLs, or offensive text.

Safeguards needed:
- **Max length cap** on published content (e.g. 500 chars for notes)
- **nsec/private key leak detection** (regex scan for `nsec1...` patterns)
- **URL filtering** (strip or flag URLs the model hallucinates)

### D. Tool Call Validation

The LLM in [`decide_action()`](llm.py:84) returns a JSON dict, but there's no validation that the action is legitimate or the parameters make sense. The fallback logic on lines 100-110 is a good safety net, but it's keyword-based.

The CVMI layer should validate:
1. Action exists in the registry
2. Required parameters are present
3. Parameter types match schema
4. Sender has permission for this tool tier

## CVMI-Lite Architecture

This fills the empty [`nostr/tools/cvmi.py`](nostr/tools/cvmi.py:1):

```
┌─────────────────────────────────────────────────────┐
│                    CVMI-Lite                          │
│                                                       │
│  LLM intent JSON                                      │
│       │                                               │
│       ▼                                               │
│  ┌─────────────┐                                      │
│  │  validate()  │ ← schema check + permission check   │
│  └──────┬──────┘                                      │
│         │                                             │
│         ▼                                             │
│  ┌─────────────┐                                      │
│  │  execute()   │ ← calls skill module                │
│  └──────┬──────┘                                      │
│         │                                             │
│         ▼                                             │
│  ┌─────────────┐                                      │
│  │  sanitize()  │ ← output checks before publish      │
│  └──────┬──────┘                                      │
│         │                                             │
│         ▼                                             │
│  structured result JSON                               │
└─────────────────────────────────────────────────────┘
```

The flow in [`process_command()`](listener.py:352) currently goes:

```
plaintext → ask_llm() → action routing → send_dm/send_note
```

It should become:

```
plaintext → ask_llm() → cvmi.validate() → cvmi.execute() → cvmi.sanitize() → send_dm/send_note
```

## Skill Registry Design

Directory structure matching your [`docs/tool implementation`](docs/tool%20implementation:138) plan:

```
nostr/tools/
    registry.py          ← discovers + loads skills
    cvmi.py              ← validation + execution gateway
    
    skills/
        weather/
            manifest.json
            execute.py   ← def run(action, args) → result
        
        nostr_note/
            manifest.json
            execute.py
        
        nostr_dm/
            manifest.json
            execute.py
        
        contacts/
            manifest.json
            execute.py
```

The registry auto-discovers skills at startup by scanning `skills/*/manifest.json`, filters by `capability_level` based on the active model, and builds the prompt snippet that gets injected into [`TOOL_PROMPT`](llm.py:13).

## NIP-90 DVM Compatibility (Future)

Your tool schema maps cleanly to NIP-90 Data Vending Machines:

| DumClaw Concept | NIP-90 Equivalent |
|-----------------|-------------------|
| Skill manifest | `kind:31990` handler info |
| Tool action | Job request `kind:5000-5999` |
| Tool result | Job result `kind:6000-6999` |
| Capability level | Custom tag `[s1]'

["capability", "S1"]

This means Gerald could eventually both consume and provide DVM services — acting as a service provider for simple tasks (weather, contacts) while requesting complex tasks from remote DVMs.

Implementation Priority
Phase 1 (Safeguards — do first)
├── Rate limiter in command_worker
├── Output sanitization (length + nsec detection)
├── Audit logging of all tool calls to events.py
└── Permission tier constants

Phase 2 (CVMI-Lite)
├── Fill nostr/tools/cvmi.py with validate/execute/sanitize
├── Create manifest.json schema
├── Refactor ask_llm() to return structured intent
└── Wire process_command() through CVMI

Phase 3 (Skill Registry)
├── Create nostr/tools/skills/ directory structure
├── Migrate weather, note, dm into skill modules
├── Build registry.py auto-discovery
└── Dynamic prompt generation from registry

Phase 4 (Interop)
├── NIP-89 handler announcement for Gerald's skills
├── NIP-90 DVM job request/result support
└── Nostr-based skill discovery from trusted contacts

The critical insight: Phase 1 costs almost nothing to implement but prevents the most damage. A rogue LLM output publishing an nsec or spamming notes is a real risk with a 1B model. The safeguards should go in before the skill system gets more powerful.

Two Key Architectural Points
1. Skill Publishing: MD for Humans, JSON for Machines
Skills should be published as markdown (human-readable, shareable on Nostr as long-form content) but consumed as JSON (machine-executable). The flow is:

Developer writes skill.md
       │
       ▼
"BiggerBrain" API call (ppq/routstr/OpenAI-compatible)
       │
       ▼
Generates manifest.json + schema.json
       │
       ▼
Script validates + installs into skills/
       │
       ▼
Gerald's registry picks it up

This means the local 1B model never parses markdown skill definitions — it only ever sees the compact JSON registry. The markdown is the source of truth for humans and the Nostr network, the JSON is the compiled artifact for agents. The key compatibility requirement: the JSON schema must be identical whether it came from a DumClaw skill.md, an OpenClaw skill, or a CVMI tool definition. Any "claw" agent reading that JSON should behave the same way. The user shouldn't know or care which agent runtime is executing.

2. The Privacy Shield: LLM as Behavioral Proxy
This is a genuinely novel insight from the DumClaw architecture and should be considered one of its core design principles.

The local LLM does not exist only to generate responses. It acts as a **behavioral proxy layer** between the user and the outside world.

### The Problem

When a user sends a query directly to a cloud API, the service provider gains access to far more information than the user intended to reveal.

Typical flow:

```
User
  ↓
Cloud AI / SaaS API
  ↓
External services
```

In this architecture, the cloud provider can observe:

* the user's full prompt
* conversational context
* personal data mentioned in the query
* behavioral patterns
* frequency and timing of requests
* potentially sensitive identifiers (contacts, locations, interests)

Even when the user's question appears simple, the full context of the conversation is usually transmitted.

For example:

```
User: "What's the weather in Lisbon?"
```

The service receiving the request may also see:

* previous conversation messages
* references to people or locations
* embedded identifiers
* conversation metadata

Over time this builds a **complete behavioral profile of the user**.

This problem becomes significantly worse in agent systems where the AI is allowed to call tools automatically.

In a typical cloud-agent architecture:

```
User
  ↓
Cloud LLM
  ↓
Tool APIs
  ↓
External services
```

Every tool invocation potentially exposes internal context and user intent to third parties.

---

### The DumClaw Solution

DumClaw inverts this relationship.

Instead of the user interacting directly with external services, the **local LLM mediates all behavior**.

The architecture becomes:

```
User
  ↓
Local LLM (behavioral proxy)
  ↓
Tool selection
  ↓
External services (if required)
```

The LLM functions as a **privacy shield** that decides:

* what information must leave the system
* which tool should be invoked
* how much context is necessary for the task
* whether the request can be handled locally

Most user requests never need to leave the local machine at all.

Examples:

```
User: "Send a note saying hello"
```

Handled entirely locally through the Nostr publishing tool.

```
User: "Show my contacts"
```

Handled entirely locally from the contacts database.

```
User: "What's the weather?"
```

Only the minimal query required for the weather service is sent externally.

The external service does **not** receive the conversation history or user intent, only the minimal parameter required for the task.

---

### Behavioral Compartmentalization

By separating **intent generation** from **tool execution**, DumClaw prevents information leakage across services.

Each tool receives only the inputs required for its specific function.

For example:

Weather service receives:

```
city=Lisbon
```

It does not receive:

* user identity
* conversation context
* contacts
* agent configuration
* previous queries

This creates a form of **behavioral compartmentalization** where external systems see only isolated fragments of activity rather than the full behavioral graph of the user.

---

### The Local Model as a Privacy Firewall

In this architecture the local model behaves similarly to a firewall, but for **behavioral data rather than network packets**.

The model evaluates:

1. user intent
2. required tools
3. necessary parameters
4. privacy impact

Only the minimal safe action is executed.

Because the model runs locally, it has access to:

* the full conversation
* local state
* contact lists
* private keys
* skill registry
* tool permissions

But **none of this information is exposed externally unless explicitly required**.

This creates a strong separation between:

```
private cognitive space (local agent)
```

and

```
public execution surface (tools and services)
```

---

### Why This Matters for Small Models

A common assumption is that powerful agent systems require large cloud-hosted models.

DumClaw takes the opposite approach.

A small local model (such as a 1B parameter model) is sufficient to perform:

* intent recognition
* tool selection
* parameter extraction
* privacy filtering

These tasks require far less capability than open-ended reasoning or knowledge synthesis.

The heavy computation or external knowledge can be delegated to tools when necessary.

This allows the local model to function primarily as a **decision layer**, rather than a knowledge engine.

In this design the LLM becomes:

```
intent router
privacy filter
behavioral proxy
tool orchestrator
```

rather than a monolithic intelligence.

---

### Architectural Consequence

Because the local model mediates all external interaction, the user gains several properties that are difficult to achieve in cloud systems:

**Sovereignty**

The user controls the model, the tools, and the data.

**Privacy**

Sensitive context never leaves the device.

**Auditability**

All tool calls can be logged and inspected locally.

**Deterministic execution**

The LLM suggests actions, but the CVMI layer validates and executes them.

**Decentralization**

External services can be replaced, mirrored, or removed without changing the agent architecture.

---

### The Privacy Boundary

The key architectural boundary in DumClaw is therefore:

```
LOCAL DOMAIN
------------------------------------
User
Local LLM
CVMI runtime
Skill registry
Private keys
Contacts
Conversation history
------------------------------------
PUBLIC DOMAIN
External APIs
Nostr relays
Remote DVM services
Public data sources
```

The local model acts as the **boundary guardian** between these domains.

Everything that crosses this boundary must pass through:

1. intent interpretation
2. tool validation
3. parameter filtering
4. execution safeguards

---

### Implication for Agent Design

This approach reframes the role of the LLM in agent systems.

Instead of being the primary intelligence, the model becomes a **trusted intermediary** between the human and the network.

The network provides capabilities.

The LLM decides **how and when those capabilities are used**.

In this sense the local model is not just an assistant — it is the user's **digital representative**.
