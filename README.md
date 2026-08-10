# LinkedIn Profile for AI

> An AI-powered personal branding and LinkedIn content development project focused on building a professional AI/LLMOps presence on LinkedIn.

---

## 1. Project Overview

**Project Name:** LinkedIn Profile for AI

**Repository:** `AI-BrandPilot`

**Primary Goal:**
Build and continuously improve a professional LinkedIn presence focused on:

* AI for Business
* LLMOps
* Prompt Engineering
* AI-Powered Workflows
* AI Agents
* AI-powered business solutions
* Practical implementation of AI

The project is not intended to be only a LinkedIn profile generator. The long-term goal is to create a reusable AI-powered system that can help develop a professional personal brand, generate relevant content, maintain context and persona, and eventually automate parts of the LinkedIn content workflow.

---

# 2. Personal Brand Positioning

The current professional positioning is:

> **AI for Business | LLMOps Learner | Prompt Engineering | AI-Powered Workflows | WordPress & AI Websites**

The content strategy should emphasize practical knowledge rather than generic AI news.

Primary areas of interest:

1. AI for Business
2. LLMOps
3. AI Agents
4. Prompt Engineering
5. AI-powered workflows
6. Practical AI implementation
7. AI automation
8. AI-assisted business processes
9. Lessons learned from building real AI projects

The LinkedIn presence should gradually establish credibility through **building, experimenting, documenting, and sharing practical results**.

---

# 3. Long-Term Project Vision

The long-term vision is to build an AI-powered personal branding system that can:

1. Understand the user's professional persona.
2. Maintain persistent context and memory.
3. Generate LinkedIn content aligned with the persona.
4. Analyze content ideas and trends.
5. Generate multiple content formats.
6. Maintain consistency across posts.
7. Assist with content planning.
8. Eventually support semi-automated LinkedIn workflows.

The project should remain modular so that new AI capabilities can be added without rewriting the entire system.

---

# 4. Development Philosophy

The project follows these principles:

### 4.1 Modular Architecture

Responsibilities should be separated into:

* Agents
* Services
* Models
* Memory
* Tools
* Workflows
* Configuration
* API layer

### 4.2 Provider Independence

The architecture should avoid unnecessary coupling to a single LLM provider.

The LLM layer should make it possible to change providers later, for example:

* Ollama
* OpenAI-compatible APIs
* Other local LLMs
* Cloud LLM providers

The application should ideally interact with an abstract LLM service rather than directly depending on one model throughout the codebase.

### 4.3 Local-First Development

Where practical, the project should support local/offline development.

Ollama has been used as a local LLM option. The user's laptop can run Ollama, while the company computer does not have a suitable GPU.

Therefore, do not assume that Ollama is available on every development machine.

### 4.4 Incremental Development

The project is being developed through incremental Sprints.

Each Sprint should:

* solve one clearly defined problem;
* avoid unnecessary complexity;
* preserve existing functionality;
* be testable;
* produce a meaningful Git commit.

---

# 5. Current Technology Stack

The project currently uses:

* Python
* Git / GitHub
* Ollama for local LLM experimentation
* YAML for persona configuration
* Markdown for prompts
* Python services and classes
* Local conversation memory
* Tool routing
* Automated tests where applicable

The project is intentionally kept relatively lightweight.

Avoid introducing large frameworks or dependencies unless they are genuinely necessary.

---

# 6. Current Project Structure

The project root is:

```text
AI-BrandPilot/
│
├── app/
│   ├── main.py
│   │
│   ├── agent/
│   │   └── base_agent.py
│   │
│   ├── api/
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   ├── memory/
│   │   ├── conversation_memory.py
│   │   └── persona.yaml
│   │
│   ├── models/
│   │   ├── message.py
│   │   └── response.py
│   │
│   ├── prompts/
│   │   └── system_prompt.md
│   │
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── persona_service.py
│   │   └── prompt_service.py
│   │
│   ├── tools/
│   │   ├── calculator_tool.py
│   │   ├── datetime_tool.py
│   │   └── tool_router.py
│   │
│   ├── utils/
│   │
│   └── workflows/
│
├── tests/
│   └── test_conversation_memory.py
│
├── docs/
│
├── CLAUDE.md
│
├── README.md
│
└── .gitignore
```

> The actual repository may contain additional files as development continues. Always inspect the current repository before making architectural decisions.

---

# 7. Main Components

## 7.1 `app/main.py`

Application entry point.

The intended execution pattern is:

```bash
python -m app.main
```

This should remain the primary simple way to run the application during development unless the architecture is intentionally changed.

---

# 8. Agent Layer

## `app/agent/base_agent.py`

`BaseAgent` is the central orchestration component.

Its responsibility is to combine:

1. Persona
2. System prompt
3. Conversation history
4. User input
5. Tools
6. LLM service

The Agent should not contain unnecessary provider-specific implementation details.

Conceptually:

```text
User Input
    │
    ▼
BaseAgent
    │
    ├── Persona
    │
    ├── System Prompt
    │
    ├── Conversation Memory
    │
    ├── Tool Router
    │
    └── LLM Service
             │
             ▼
           LLM
             │
             ▼
          Response
```

The current `base_agent.py` is the active implementation and should be treated as the source of truth when making changes.

---

# 9. Persona System

## `app/memory/persona.yaml`

Stores the persistent persona information.

The persona is important because this project is specifically designed around a professional personal brand.

The system should use the persona to maintain consistency in:

* professional identity
* interests
* communication style
* goals
* content direction
* target audience
* expertise level

Do not hard-code persona information unnecessarily inside Python code.

---

# 10. Conversation Memory

## `app/memory/conversation_memory.py`

Responsible for maintaining conversation history.

The memory system allows the Agent to preserve relevant previous messages rather than treating every user request as completely independent.

Current memory is local and lightweight.

Future improvements may include:

* persistent storage
* semantic memory
* vector database
* RAG
* long-term user memory
* summarized conversation history

However, these should only be added when required.

Do not introduce a vector database merely for the sake of complexity.

---

# 11. Models

## `app/models/message.py`

Defines the internal representation of messages.

The model layer should provide structured data objects rather than passing arbitrary dictionaries throughout the application.

---

## `app/models/response.py`

Defines the structured response representation returned by the application.

The goal is to keep response handling predictable and independent from a particular LLM provider.

---

# 12. Services

## `app/services/llm_service.py`

Responsible for communication with the LLM.

This is one of the most important abstraction boundaries in the project.

The Agent should use this service instead of embedding direct LLM calls throughout the application.

This makes it easier to change the underlying provider.

Potential future providers:

```text
Ollama
OpenAI-compatible API
Other cloud providers
Other local models
```

---

## `app/services/persona_service.py`

Responsible for loading and providing persona information to the rest of the application.

Persona management should remain separate from the Agent implementation.

---

## `app/services/prompt_service.py`

Responsible for loading and managing prompts.

System prompts should not be unnecessarily hard-coded inside Python source files.

---

# 13. Prompt System

## `app/prompts/system_prompt.md`

Contains the main system-level instructions for the Agent.

The prompt system should remain:

* readable
* versionable
* editable without changing Python code
* separated from business logic

Prompt engineering is considered a first-class part of this project.

---

# 14. Tools

The project includes a lightweight tool system.

## `app/tools/calculator_tool.py`

Provides calculator functionality.

## `app/tools/datetime_tool.py`

Provides date/time functionality.

## `app/tools/tool_router.py`

Responsible for determining which tool should handle a tool-related request.

Conceptually:

```text
User Request
     │
     ▼
Tool Router
     │
 ┌───┴────┐
 ▼        ▼
Calculator  DateTime
```

The architecture should make it possible to add additional tools later without modifying the entire Agent.

---

# 15. Workflows

## `app/workflows/`

Reserved for higher-level business workflows.

Future workflows may include:

* LinkedIn post generation
* Content idea generation
* Content research
* Post rewriting
* Content evaluation
* LinkedIn content calendar
* Personal brand analysis
* Audience analysis
* Content repurposing

Workflows should orchestrate existing services and agents rather than duplicating their logic.

---

# 16. API Layer

## `app/api/`

Reserved for exposing application functionality through an API.

The API layer should remain separate from core business logic.

The Agent and Services should be usable without requiring the API layer.

---

# 17. Testing

Tests are located under:

```text
tests/
```

Current testing includes:

```text
tests/test_conversation_memory.py
```

When modifying existing functionality:

1. Preserve existing tests.
2. Add tests for important new behavior.
3. Do not modify tests simply to make failing code pass.
4. Identify whether the problem is in implementation or in the test.

---

# 18. Git Workflow

The project is managed with Git.

The main repository is:

```text
AI-BrandPilot
```

The development process has been organized into Sprints.

Examples of previous development stages include:

* Sprint 7 — End-to-end chat with Ollama
* Sprint 8 — Conversation memory and Git ignore rules
* Sprint 11
* Sprint 12
* Sprint 12 Part 1

The exact current Sprint/status must always be verified from the repository and Git history before starting new work.

Useful commands:

```bash
git status
git log --oneline --graph --decorate --all -20
```

Before making significant changes:

```bash
git status
```

After completing a logical task:

```bash
git add .
git commit -m "Short descriptive message"
```

Do not create large unrelated commits.

---

# 19. Important Development History

The project evolved incrementally.

Important milestones include:

### Sprint 7

Implemented end-to-end chat functionality using Ollama.

### Sprint 8

Added:

* conversation memory
* Git ignore rules

### Sprint 11 / 12

The project evolved toward a more complete LLMOps architecture involving:

* structured Agent architecture
* memory
* embeddings
* RAG planning
* local LLM integration
* modular services

The project should continue from the current repository state rather than recreating earlier implementations.

---

# 20. RAG Direction

A local RAG architecture has been considered for the project.

A minimal RAG pipeline may eventually contain:

```text
Documents
    │
    ▼
Loader
    │
    ▼
Chunking
    │
    ▼
Embeddings
    │
    ▼
Vector Store
    │
    ▼
Retriever
    │
    ▼
LLM
```

Ollama's embedding capability is available in the existing environment.

However, RAG should only be implemented when it solves an actual project requirement.

Avoid adding unnecessary infrastructure.

---

# 20.1. Posting Cadence and Approval (Sprint 13)

The project's actual operating goal is: **two LinkedIn posts a week,
each reviewed by a human before it goes live.**

## Schedule

`scheduler.py` is invoked once a day by an external OS-level scheduler
(cron / systemd timer / Task Scheduler). It is a no-op every day except:

* **Tuesday** -- research a fresh topic, draft a full post, save it.
* **Friday** -- research a fresh topic, draft a full post, save it.

Each run produces one complete draft (not just an idea), so two full
drafts land per week.

## Approval by email

After a draft is saved with status `pending_approval`, `LinkedInAgent`
emails the full draft text to `NOTIFY_TO_EMAIL` (see
`app/services/notification_service.py` and the SMTP variables in
`.env.example`). The person reads the email and, if happy with it,
copies the text onto LinkedIn **manually**.

This project does **not** call the LinkedIn API and does **not** post
anything automatically, anywhere. That is intentional (see `CLAUDE.md`:
"Never publish automatically"). Email notifications are purely a
"please review this" nudge, not a publish step, and are entirely
optional -- leave `SMTP_HOST` empty in `.env` to disable them.

## Closing the loop

Once a draft has been posted by hand, run:

```bash
python manage.py list-pending      # see what's waiting for review
python manage.py show <post_id>    # print one draft's full text
python manage.py mark-posted <post_id>
```

`mark-posted` only updates the local business database
(`app/memory/database.py`) so records stay accurate -- it never talks
to LinkedIn.

## If full automatic publishing is wanted later

Actually posting to LinkedIn without a human step would require a
LinkedIn Developer App (the "Share on LinkedIn" product, `w_member_social`
scope) and an OAuth token obtained by the account owner -- LinkedIn does
not allow this to be done on someone else's behalf. That integration is
a deliberate future direction, not current scope.

---

# 21. Current Design Principles

When continuing development, follow these rules.

### Rule 1 — Do not rewrite working components without a reason.

Prefer incremental modifications.

### Rule 2 — Inspect before changing.

Before modifying a component:

1. Read the current implementation.
2. Understand its dependencies.
3. Check tests.
4. Check how it is used elsewhere.

### Rule 3 — Preserve architecture.

Do not move business logic randomly between:

* Agent
* Service
* Tool
* Workflow
* Model

Each component should have a clear responsibility.

### Rule 4 — Keep dependencies minimal.

Do not add a dependency when the standard library or an existing dependency is sufficient.

### Rule 5 — Keep provider-specific code isolated.

LLM provider details belong primarily in the LLM service layer.

### Rule 6 — Prefer simple solutions.

The goal is a functional, maintainable LLMOps project, not an unnecessarily complicated enterprise framework.

---

# 22. Development Environment

The project has been developed on Windows.

Typical project path:

```text
C:\Users\m.mousavi\Desktop\AI-BrandPilot
```

A Python virtual environment is used:

```text
.venv/
```

Do not commit the virtual environment to Git.

---

# 23. Important Environment Constraint

The user works on more than one computer.

The laptop can run Ollama.

The company computer does not have a suitable GPU for running Ollama.

Therefore:

* Do not assume Ollama is available everywhere.
* Keep the application architecture provider-independent.
* Avoid making local GPU execution a hard requirement.
* Prefer configuration-based provider selection.

---

# 24. Future Direction

The project may eventually evolve into a complete AI personal-branding platform.

Potential future capabilities:

```text
                    LinkedIn Profile for AI
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
       Persona           Content             Memory
       Engine            Engine              System
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                         AI Agent
                             │
             ┌───────────────┼───────────────┐
             ▼               ▼               ▼
           Tools           RAG           Workflows
             │               │               │
             └───────────────┼───────────────┘
                             ▼
                       LinkedIn Output
```

Potential advanced features:

* AI-powered content research
* LinkedIn content generation
* Personal brand analytics
* Content scoring
* Audience analysis
* RAG over personal knowledge
* Long-term memory
* Multiple specialized agents
* Content planning
* Automated workflows
* Human-in-the-loop approval
* LinkedIn API integration where appropriate

These are future directions, not necessarily current requirements.

---

# 25. What Gemini Must Do Before Continuing

When this repository is provided to another AI model such as Gemini, **do not immediately start coding.**

First:

### Step 1 — Inspect the repository

Read:

```text
README.md
app/
tests/
docs/
CLAUDE.md
```

and inspect the current Git status/history.

### Step 2 — Identify the actual current state

Determine:

* What has already been implemented?
* What is working?
* What is incomplete?
* What is currently being developed?
* What is the latest Sprint?
* What is the latest Git commit?
* Are there uncommitted changes?

### Step 3 — Do not assume this README is more authoritative than the source code.

If this README and the actual code disagree:

> **The current source code is the source of truth.**

Update the README when necessary.

### Step 4 — Understand before modifying.

Do not rewrite the architecture simply because another architecture is possible.

### Step 5 — Continue from the current state.

The goal is to continue the project, not restart it.

---

# 26. Instructions for the Next AI Assistant

You are continuing an existing software project.

You must:

1. Inspect the repository before proposing changes.
2. Understand the current architecture.
3. Preserve working functionality.
4. Follow the existing project structure.
5. Avoid unnecessary dependencies.
6. Avoid unnecessary refactoring.
7. Explain the reason for architectural changes.
8. Implement changes incrementally.
9. Run relevant tests after changes.
10. Report exactly what was changed.
11. Identify any assumptions.
12. Do not claim something works unless it has been verified.
13. Do not recreate components that already exist.
14. Keep provider-specific logic isolated.
15. Treat the current codebase as the source of truth.

---

# 27. How to Continue the Project

Before starting a new task, use this sequence:

```text
1. Read README.md
        ↓
2. Inspect repository
        ↓
3. Inspect current Git status
        ↓
4. Inspect recent Git commits
        ↓
5. Identify current Sprint
        ↓
6. Understand existing implementation
        ↓
7. Define the smallest appropriate change
        ↓
8. Implement
        ↓
9. Run tests
        ↓
10. Verify behavior
        ↓
11. Update documentation if needed
        ↓
12. Commit the logical change
```

---

# 28. Current Project Status

**Status:** Active development

**Project phase:** Building the foundation of an AI-powered personal branding / LinkedIn assistant.

**Architecture:** Modular Agent + Services + Memory + Tools + Workflows

**Primary language:** Python

**Primary development focus:** LLMOps, Agent architecture, memory, tools, local LLM integration, RAG, and AI-powered LinkedIn workflows.

**Current priority:** Continue development from the latest repository state without breaking existing functionality.

---

# 29. Final Principle

The most important principle of this project is:

> **Build a simple, modular, reusable AI system that can evolve from a personal LinkedIn assistant into a practical AI-powered personal branding platform.**

Do not optimize for complexity.

Optimize for:

**clarity → modularity → testability → reusability → practical value.**
