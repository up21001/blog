---
title: "gstack Complete Guide Part 1: What Is Garry Tan's AI Software Factory?"
date: 2026-04-03T09:00:00+09:00
lastmod: 2026-04-03T09:00:00+09:00
description: "Introducing gstack, the open-source AI development framework built by Y Combinator President Garry Tan. Learn how 23 specialized agent skills transform Claude Code into a virtual engineering team, enabling solo builders to ship at enterprise velocity."
slug: "gstack-part1-introduction"
categories: ["ai-agents"]
tags: ["gstack", "Claude Code", "AI agents", "Garry Tan", "Y Combinator", "software development", "AI automation"]
series: ["gstack Complete Guide"]
series_order: 1
draft: false
---

In early 2026, a quiet but powerful wave swept through Silicon Valley. Garry Tan, President and CEO of Y Combinator, released an open-source project that crossed 62,600 GitHub stars within weeks. It's called **gstack**. When word got out that he had personally used it to write 600,000 lines of code in 60 days — alone — the developer community was stunned.

This four-part series dives deep into what gstack is, how it works, and how you can apply it to your own development workflow. Part 1 focuses on understanding gstack's origins and core architecture.

---

## What Is gstack?

gstack is, in a single sentence, **an open-source toolkit that transforms Claude Code into a virtual engineering team**. It is not merely a tool that "has AI write code for you." It is a system of 23 specialized agent-based slash commands that covers the entire software development lifecycle — from ideation through deployment.

The core philosophy is clear: **a single developer should be able to build software at team-level speed and quality.** Garry Tan proved this himself, achieving a documented record of 10,000–20,000 lines of code per day using gstack.

- **GitHub**: [github.com/garrytan/gstack](https://github.com/garrytan/gstack)
- **License**: MIT (free, open source forever)
- **GitHub Stars**: 62,600+
- **Requirement**: Claude Code (Anthropic)

gstack defines the next stage of AI-assisted coding. If GitHub Copilot is autocomplete, and ChatGPT is conversational code generation, then gstack is an **autonomously operating software factory**.

---

## The Sprint Framework: Think → Plan → Build → Review → Test → Ship → Reflect

The most groundbreaking aspect of gstack is its integration of the entire software development process into a single, structured sprint framework.

![gstack Sprint Framework — 7-stage workflow from Think to Ship](/images/posts/gstack-part1-introduction/svg-1-en.svg)

Let's walk through each stage.

### Stage 1: Think

Before any code is written, the AI deeply analyzes the requirements. What needs to be built? What constraints exist? What trade-offs must be considered? The `/think` command enforces a deliberate thinking phase before implementation begins. This mirrors the habit of a senior engineer spending 30 minutes at a whiteboard before touching a keyboard — now embedded in the AI workflow.

### Stage 2: Plan

Once thinking is complete, `/plan` decomposes the entire task into small, atomic units. Each sub-task is independently executable and verifiable. A complex feature becomes a clear, actionable checklist.

### Stage 3: Build

With a confirmed plan, the system generates actual code. At this stage, gstack doesn't just write code in isolation — it learns the patterns of your existing codebase and implements features with consistent style. The `/build` and `/implement` commands handle this.

### Stage 4: Review

Here one of gstack's core innovations appears: **Cross-Model Review** — a different AI model than the one that wrote the code independently reviews it. This applies the software engineering principle of "separating author from reviewer" to the AI workflow. It structurally solves the limitation of a single model that cannot catch its own errors.

### Stage 5: Test

Another gstack innovation is **real browser testing**. Rather than mock environments, the `/e2e` command runs automated Playwright-based tests in a real Chromium browser. This eliminates the classic "works on my machine" problem at the development stage.

### Stage 6: Ship

Code that passes tests is automatically deployed via the `/ship` command. Release notes, version tagging, and changelog updates are all automated.

### Stage 7: Reflect

After the sprint completes, gstack analyzes what went well and what could be improved. This creates a feedback loop for continuous quality improvement.

---

## 23 Specialized Skills: Members of the Virtual Engineering Team

gstack's 23 slash commands each correspond to a role in a traditional software team.

![gstack 23 Specialized Skill Categories](/images/posts/gstack-part1-introduction/svg-2-en.svg)

### Planning Category (5 skills)

Agents that handle the planning phase.

- `/think` — Deep requirements analysis and approach exploration
- `/plan` — Break the full task into executable sub-tasks
- `/architect` — System architecture design and technical decisions
- `/roadmap` — Long-term development roadmap creation
- `/breakdown` — Detailed decomposition of complex features

### Design Category (4 skills)

Handles UI/UX and visual design.

- `/design` — Component and page UI design
- `/wireframe` — Wireframe and layout sketching
- `/prototype` — Rapid prototype generation
- `/style` — Design system and style guide application

### Development Category (6 skills)

The core of actual code generation and quality improvement.

- `/build` — Full feature implementation
- `/implement` — Specific module implementation
- `/refactor` — Code quality improvement
- `/debug` — Bug tracking and fixing
- `/optimize` — Performance optimization
- `/document` — Automated code documentation generation

### Testing Category (4 skills)

Handles quality assurance.

- `/test` — Automated unit test generation
- `/e2e` — Playwright E2E test execution
- `/coverage` — Test coverage analysis
- `/benchmark` — Performance benchmarking

### Release Category (5 skills)

Handles deployment automation.

- `/ship` — Execute the full deployment pipeline
- `/deploy` — Deploy to a specific environment
- `/changelog` — Automated changelog generation
- `/tag` — Version tagging
- `/rollback` — Rollback to previous version

### Utilities Category (4 skills)

General-purpose utility agents.

- `/search` — Intelligent codebase search
- `/summarize` — Code and document summarization
- `/review` — Code quality review
- `/explain` — Code explanation and education

---

## Three Core Innovations

gstack differs fundamentally from existing AI coding tools in three innovations.

### Innovation 1: Real Browser Automation

Most AI coding tools generate code and then leave testing to the human developer. gstack is different. The `/e2e` command launches a real Chromium browser and automatically verifies that generated code behaves correctly in an actual environment.

Why does this matter? The gap between test environments and production is the source of every "works on my machine" failure. gstack eliminates this gap at the development stage.

### Innovation 2: Cross-Model Review

One of the most important principles in software development is separating code authors from reviewers. This principle is obvious in human teams but almost never implemented in AI coding tools. When the same model generates and reviews code, the same errors repeat.

gstack's cross-model review has a different AI model than the one that wrote the code perform an independent review. Like a senior developer reviewing a junior's PR, it catches errors, security vulnerabilities, and performance issues from a fresh perspective.

### Innovation 3: Smart Routing

Using the most powerful model for every task causes costs to explode. gstack's smart routing analyzes task complexity and automatically selects the optimal model.

- Fast lookups, simple questions → **Haiku** (low cost, high speed)
- Standard development tasks, code generation → **Sonnet** (balanced)
- Architecture design, deep analysis → **Opus** (highest quality)

This optimization allows gstack to achieve enterprise-grade quality at a reasonable cost.

---

## Traditional AI Coding vs gstack: What's Different?

Let's compare gstack directly with existing tools.

![Traditional AI Coding vs gstack Comparison](/images/posts/gstack-part1-introduction/svg-3-en.svg)

### The Scope Difference

GitHub Copilot predicts the next line in the function you're editing. ChatGPT generates the code block you request. Both tools are **fragmented** — when context breaks, consistency disappears.

gstack understands the **entire project** and manages the full development cycle. From a single page of requirements to deployable, test-passing software — treated as one continuous process.

### The Quality Assurance Difference

In existing AI tools, quality assurance is the developer's responsibility. Generated code must be reviewed manually, test code written by hand, and bugs found and fixed by the developer.

In gstack, review (`/review`), testing (`/test`, `/e2e`), and documentation (`/document`) are all parts of an automated workflow. The developer acts as supervisor and final decision-maker.

### The Productivity Difference

Garry Tan's 60-day, 600,000-line experiment is the strongest evidence. This is not a marketing number. He set this record while writing actual production code for YC portfolio startups.

What does 10,000–20,000 lines per day mean in context? The average productivity of a skilled senior developer is around 200–500 lines per day. gstack enables a 20–100x speed increase.

---

## Why Did Garry Tan Build This Himself?

An interesting question arises: why would the president of Y Combinator personally build an open-source developer tool?

Garry Tan is an engineer by training, graduating from Stanford's computer science program. As a software developer himself, he felt that the true potential of AI coding tools remained unrealized. Existing tools automated parts of coding but not software development as a whole.

As YC's president, he has watched thousands of startups struggle with talent shortages, development speed problems, and difficulty maintaining quality. gstack is his direct answer to those problems.

The vision that drove him to build gstack: "A single talented developer, with AI assistance, should be able to produce the output of an entire team."

Releasing it under the MIT license is also significant. It signals that he wants every developer in the world — not just YC-backed startups — to benefit from this tool.

---

## The gstack Ecosystem Today

As of early 2026, the gstack ecosystem is growing rapidly.

**Community**: Thousands of active users engage daily on Discord, sharing new use cases, tips, and custom workflows.

**Extensibility**: Community contributors are developing additional skills beyond the 23 defaults. gstack's skill system was designed to be extensible from the start.

**Enterprise adoption**: Several YC startups have already integrated gstack into their production development workflows. A new paradigm is forming where small teams can compete with large ones.

**Claude Code ecosystem**: gstack is built on top of Anthropic's Claude Code. As Claude Code itself continues to evolve, gstack's capabilities advance in parallel.

---

## What's Coming in This Series

This series spans four parts.

**Part 2 — Installation and Your First Sprint**: A hands-on tutorial from installing gstack through executing your first real project end-to-end. The complete journey from `npm install` to `/ship`.

**Part 3 — Deep Dive into the 23 Skills**: Practical usage, parameters, and best practices for each slash command. A pragmatic guide to which command to use in which situation.

**Part 4 — Advanced Patterns and Real-World Strategies**: Cross-model review optimization, smart routing cost management, and strategies for operating gstack on large-scale projects. Analysis of real user success stories.

---

## Conclusion: The Next Chapter of AI Development Tools

gstack is not just a tool. It is a new vision for how software development should work.

If existing AI coding tools improve developer productivity by 10–20%, gstack changes the **scale of what a developer can accomplish**. Being able to do the work of a team alone is a game-changer for startup founders, freelance developers, and anyone dreaming of a side project.

Garry Tan writing 600,000 lines in 60 days is not a stunt. It is a demonstration that this could become the new standard for software development.

In the next post, we'll walk through a hands-on guide to installing gstack and running your first sprint. You'll be able to follow the entire process step by step, from setting up your development environment to shipping a real feature.

---

*Next in this series: [gstack Complete Guide Part 2: Installation and Your First Sprint](#)*
