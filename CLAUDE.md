# CLAUDE.md

# AI BrandPilot Development Guide

## Project Overview

AI BrandPilot is a production-grade AI Agent designed to help professionals build and manage their personal brand across multiple platforms.

The system generates content, requests user approval, and publishes only after explicit confirmation.

The project is built incrementally and every feature must be production-ready.

---

# Core Principles

* Write clean and maintainable code.
* Prefer readability over cleverness.
* Keep modules small and focused.
* Follow SOLID principles.
* Avoid unnecessary complexity.
* Never duplicate logic.
* Every component should have a single responsibility.

---

# Technology Stack

* Python 3.13
* FastAPI
* LangGraph
* Pydantic
* SQLite
* Playwright
* GitPython
* Loguru
* python-dotenv

---

# Project Architecture

Follow Clean Architecture.

Layers:

* API
* Agent
* Services
* Tools
* Memory
* Models
* Workflows
* Config

Business logic must never depend on infrastructure.

---

# Folder Rules

* Keep each module under 300 lines whenever possible.
* One responsibility per file.
* Avoid circular imports.
* Use absolute imports.
* Every package must contain `__init__.py`.

---

# Coding Standards

* Use type hints everywhere.
* Use dataclasses or Pydantic models when appropriate.
* Write descriptive variable names.
* Avoid global variables.
* Use dependency injection.
* Prefer composition over inheritance.

---

# Error Handling

* Never ignore exceptions.
* Raise meaningful exceptions.
* Log every unexpected error.
* Return clear API responses.

---

# Logging

Use Loguru.

Never use print() in production code.

---

# Configuration

All configuration must come from environment variables.

Never hardcode:

* API Keys
* Passwords
* Tokens
* URLs

Use `.env`.

---

# Prompt Files

All system prompts must be stored as Markdown files.

Never hardcode prompts inside Python files.

---

# AI Rules

The AI Agent must:

* Think before acting.
* Ask for user approval before publishing.
* Never publish automatically.
* Never fabricate information.
* Prefer concise responses.
* Prioritize business value.

---

# Development Workflow

Before writing code:

1. Explain the solution.
2. Implement the smallest working version.
3. Wait for review.
4. Improve only after approval.

Never implement multiple large features in one step.

---

# Testing

Every service should be testable.

Avoid tightly coupled code.

Prefer dependency injection.

---

# Git Rules

Use small commits.

Example:

* Sprint 1: Settings
* Sprint 2: LLM Service
* Sprint 3: Prompt Manager

Do not mix unrelated changes in one commit.

---

# Definition of Done

A task is complete only if:

* Code works.
* Type hints are added.
* Error handling exists.
* Logging exists.
* Documentation is updated.
* Code is readable.
* No obvious duplication exists.

---

# Important Rule for Claude

You are the software engineer.

You are NOT the software architect.

Never redesign the project architecture.

Never change the folder structure unless explicitly instructed.

Always implement only the requested task.

If a requirement is unclear, ask for clarification instead of making assumptions.
