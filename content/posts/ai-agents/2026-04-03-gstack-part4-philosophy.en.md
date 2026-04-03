---
title: "gstack Complete Guide Part 4: Development Philosophy for the AI Age"
date: 2026-04-03T12:00:00+09:00
lastmod: 2026-04-03T12:00:00+09:00
description: "Explore gstack's three core principles (Boil the Lake, Search Before Building, User Sovereignty) and how developers must evolve in the AI era. Discover how Garry Tan wrote 600K lines in 60 days and what the future holds for solo builders."
slug: "gstack-part4-philosophy"
categories: ["ai-agents"]
tags: ["gstack", "AI development philosophy", "solo builder", "Garry Tan", "Boil the Lake", "User Sovereignty", "AI age"]
series: ["gstack Complete Guide"]
series_order: 4
draft: false
---

## "600K Lines in 60 Days" — Garry Tan's Challenge

In early 2026, Y Combinator president Garry Tan shared something remarkable: while running YC full-time, he wrote over 600,000 lines of production code in just 60 days. This wasn't a boast. It was a testimony to what gstack — the tool and the philosophy behind it — makes possible.

10,000 to 20,000 lines per day. Part-time. Solo.

Those numbers are hard to believe at first. In a traditional development environment, they border on impossible. But once you understand gstack's philosophy, the numbers make complete sense.

This is Part 4 and the final installment of the series. Here we examine why gstack functions not just as a tool but as a **development philosophy** — covering its three core principles, error philosophy, intentional simplicity, testing strategy, and the future of the solo builder.

---

## Principle 1: Boil the Lake — Completeness is Cheap in the AI Era

{{< figure src="/images/posts/gstack-part4-philosophy/svg-1-en.svg" alt="gstack three core principles diagram" >}}

The first principle in gstack's ETHOS is **Boil the Lake**. The idea: always choose the complete implementation.

Traditional development culture is dominated by "good enough for now" thinking. Handle edge cases later. Write tests when there's time. Fix error handling after a bug surfaces. This approach had a rationale — complete implementations used to be expensive.

In the AI era, that premise collapses.

### Lakes vs. Oceans

gstack distinguishes two categories:

- **Lakes**: Things where complete implementation is realistically achievable. 100% test coverage, all edge cases handled, full error handling — possible at the cost of a few extra minutes.
- **Oceans**: Things where complete implementation is genuinely unreasonable. Perfect security, infinite scalability, support for every browser.

When AI agents are in the loop, the cost of "Lakes" drops dramatically. If AI can write 100% test coverage in a few additional minutes, why stop at 50%?

### Rejecting Deferral

The core attitude of Boil the Lake is **refusing "later"**:

```bash
# Bad pattern: deferring work
# "TODO: add error handling later"
# "will write tests later"
# "handle edge cases post-MVP"

# gstack approach: complete it now
/skill add-tests --coverage 100
/skill handle-errors --complete
```

In an age where AI agents write tests, saying "I'll write tests later" is functionally equivalent to "I'll never write tests." gstack starts from this recognition and sets complete implementation as the default.

---

## Principle 2: Search Before Building — 3 Knowledge Layers and the Eureka Moment

The second principle is **Search Before Building**. It sounds like simple advice against reinventing the wheel, but gstack systematizes it into something far more precise.

### Three Knowledge Layers

Every technical decision involves three layers of knowledge:

**Layer 1 — Tried & True**

Patterns battle-tested over years. REST APIs, SQL databases, HTTP cache headers. These are proven and well-documented. In the AI era, it's still worth occasionally asking "why is this the best approach?" — AI agents may face entirely different tradeoffs.

**Layer 2 — New & Popular**

Approaches that have risen in the last 6-18 months. GraphQL, Edge Functions, WebAssembly. Their popularity signals value, but their validation period is short. Skeptical evaluation is warranted.

**Layer 3 — First Principles**

This is the most valuable layer. Original observations about **your specific problem**. It emerges when you discover constraints or opportunities that no existing approach has accounted for.

### The Eureka Moment

What gstack values most is the **Eureka Moment**. It unfolds in three steps:

1. Understand existing approaches thoroughly (explore Layer 1 + 2)
2. Apply reasoning to your specific situation
3. Discover why those approaches are suboptimal for your context

gstack's browser automation is a perfect example. CSS selector-based approaches existed (Layer 1). Playwright's test recorder existed (Layer 2). But the gstack team discovered that for AI agents, the **ARIA accessibility tree** was far more stable and framework-agnostic — a Layer 3 insight.

---

## Principle 3: User Sovereignty — AI Recommends, Humans Decide

{{< figure src="/images/posts/gstack-part4-philosophy/svg-2-en.svg" alt="Developer role evolution diagram in the AI age" >}}

The third principle is the most philosophical and the most practical. **User Sovereignty**.

The core proposition: "AI models recommend. Users decide."

### Two Models Agreeing ≠ A Mandate

There's a common misconception: "Claude said it, GPT said it, so it must be right." gstack explicitly rejects this logic.

Two models agreeing only means that view was common in their training data. Your **specific context** — team size, technical debt, business constraints, legacy systems — is information no model can fully grasp.

### Generation-Verification Loops

gstack's actual workflow encodes this principle:

```bash
# AI generates recommendation
/skill suggest-architecture

# Presented with reasoning (not just conclusion)
# "Recommended approach because:"
# "1. Aligns with current codebase patterns"
# "2. Leverages existing dependencies"
# "3. Appropriate for team size"
# "Alternative: X (with pros/cons)"

# User reviews and decides
/skill implement-architecture --approach chosen-option
```

AI presents recommendations **with reasoning**, and the user evaluates that reasoning before making the final call. This is the "ask rather than act" principle.

### The Iron Man Suit Philosophy

gstack frequently invokes one analogy: AI is an **Iron Man Suit**.

When Tony Stark wears the suit, it grants extraordinary capabilities — but Tony is still the decision-maker. The suit might flag "there's a target at those coordinates," but the final call belongs to Tony. The suit augments Tony; it doesn't replace him.

gstack's AI agents work the same way. They generate code at incredible speed, write tests, automate browsers — but architecture direction, business priorities, and technical tradeoffs remain in human hands.

---

## Error Philosophy: Error Messages Are for Agents, Not Humans

{{< figure src="/images/posts/gstack-part4-philosophy/svg-3-en.svg" alt="gstack impact statistics infographic" >}}

gstack's approach to error handling is radical: **error messages are written for AI agents, not for humans.**

### Bad Error vs. Good Error

A traditional error message:
```
Error: Element not found
  at findElement (browser.js:142)
  at navigate (browser.js:89)
  at main (index.js:23)
```

This stack trace is useful when a human developer is debugging. But to an AI agent, it's useless. The agent has no idea what to do next.

A gstack error message:
```
Error: Element not found — ref 'btn-submit' is no longer in the DOM
Action: Run /browse snapshot -i to see currently available elements
Available refs in last snapshot: [ref-1, ref-2, ref-3]
```

**Every error must be actionable.** When an error occurs, the next action should be immediately clear.

### Crash Recovery: Restart, Not Reconnect

Another distinctive gstack choice: instead of complex reconnection logic, **restart** is the default recovery strategy.

When a WebSocket connection drops, rather than implementing complex reconnection state machines, gstack restarts the browser daemon. This is simpler, eliminates state-mismatch bugs, and is far easier for AI agents to reason about.

---

## Intentionally Not Implemented — The Value of Simplicity

Some of the most interesting design decisions in gstack are about **what was deliberately not built**.

### WebSocket Streaming — Not Needed

Many AI tools use WebSockets for real-time streaming. gstack concluded that HTTP polling is sufficient. Why:

- AI agents don't need real-time streaming UI the way humans do
- HTTP is simpler, cacheable, and easier to debug
- Receiving results and observing progress are different problems

### MCP Protocol — JSON Schema Overhead

Model Context Protocol is a great standard, but gstack chose its own skill system. The JSON schema serialization/deserialization overhead of MCP cost more than it benefited for gstack's usage patterns.

### Multi-user Support — Out of Scope

gstack is a local development tool for a single developer or single team. It does not aim to be multi-user SaaS. This scope constraint keeps the codebase dramatically simpler.

### Linux/Windows Cookie Decryption — Not Supported

macOS Keychain cookie decryption is supported, but Linux's gnome-keyring and Windows DPAPI are not. The complexity-to-value ratio was deemed too low. Some users disagree with this call, but the gstack team made this tradeoff explicitly.

**Simplicity is a feature.** What was not built is what keeps gstack understandable, maintainable, and trustworthy.

---

## Testing Philosophy: Tier 1/2/3 Cost-Effectiveness

gstack's testing strategy optimizes for both cost and coverage simultaneously. It operates across three tiers.

### Tier 1: Static Validation (Free, Under 5 Seconds)

```bash
# Command parsing validation
# Skill registry integrity checks
# Type checking
# Linting
```

- Cost: Free (local execution)
- Time: Under 5 seconds
- Coverage: Every commit
- Purpose: Block obvious errors immediately

This layer always runs. It's the first step in the CI/CD pipeline, and failure here blocks all subsequent steps.

### Tier 2: E2E Tests (~$3.85, ~20 Minutes)

```bash
# Real Claude session per skill
# Real browser automation validation
# Real API calls
```

- Cost: ~$3.85 in Claude API costs
- Time: ~20 minutes total
- Coverage: Before PRs or releases
- Purpose: Verify behavior in real environments

This layer has a cost, but it's acceptable. $3.85 for full E2E coverage of the skill suite is a reasonable investment.

### Tier 3: LLM-as-Judge (~$0.15, ~30 Seconds)

```bash
# Sonnet scores documentation clarity
# AI readability score for skill descriptions
# Error message actionability evaluation
```

- Cost: ~$0.15
- Time: ~30 seconds
- Coverage: Documentation and prompt quality
- Purpose: Verify AI agents understand correctly

The third tier is especially interesting. For AI to use tools correctly, documentation and error messages must be clear to AI. What's easy for humans to read and what's easy for AI to parse can diverge. LLM-as-Judge measures that gap.

---

## The Age of the Solo Builder: How Developer Roles Are Changing

The future gstack envisions is one where the developer's role changes fundamentally.

### From Coder to Orchestrator

The developer of the past wrote code directly. Opening an IDE, typing functions, chasing bugs — that was the daily reality. Writing hundreds of lines a day was excellent productivity.

The developer in the gstack era is an orchestrator. Coordinating 10-15 AI agents simultaneously, making architecture decisions, setting direction, verifying outcomes. Judgment — not typing speed — becomes the bottleneck.

This shift changes which skills matter:

**Declining importance:**
- Memorizing specific languages and frameworks
- Typing speed
- Low-level implementation details

**Growing importance:**
- Systems thinking and architectural intuition
- Ability to direct and evaluate AI agents
- Translating business requirements into technical specs
- Judging quality of generated output

### The Possibility of a One-Person Team

Garry Tan's case is an extreme example, but it shows the direction. Projects that once required 10 people, now completable by one — with the right tools and the right philosophy.

gstack is that philosophy, implemented in code.

---

## Series Recap + How to Get Started

Four posts to cover gstack in full.

**Part 1: Introduction and Overview**
- What gstack is and why it was built
- Core components: Skills, Browser Automation, Conductor
- The 62,600+ star open source ecosystem

**Part 2: Installation and Core Workflow**
- macOS installation (under 5 minutes)
- Claude Desktop integration
- Running built-in skills and writing custom skills
- `.gstack/` project configuration

**Part 3: Browser Automation and Multi-Agent**
- ARIA-based Ref system
- Three-layer browser daemon architecture
- Conductor for 10-15 parallel agent execution
- Real-world usage patterns

**Part 4: Philosophy and the Future (this post)**
- Boil the Lake, Search Before Building, User Sovereignty
- Error philosophy for agents
- Intentional simplicity
- The future of the solo builder

### Getting Started Right Now

```bash
# 1. Install
brew install gstack

# 2. Initialize your project
cd your-project
gstack init

# 3. Grant Claude permission to use gstack
# Claude Desktop Settings → MCP → enable gstack

# 4. Run your first skill
/list-skills
/run-tests
```

gstack on GitHub: [github.com/gstack/gstack](https://github.com/gstack/gstack)

---

## Closing: "The Iron Man Suit of the AI Age"

When you first encounter gstack, it looks like a tool. A utility for running skills, automating browsers, spinning up parallel agents.

Look deeper, and it's **a philosophy implemented in code**.

- Completeness isn't expensive — not in the AI era. (Boil the Lake)
- Search first, build second. (Search Before Building)
- AI is the suit, not the driver. (User Sovereignty)

Garry Tan wrote 600K lines in 60 days not simply because he had a good tool. He had a clear philosophy about how to use AI agents effectively.

The age of the solo builder has already begun. gstack is the Iron Man Suit for that age.

---

*gstack Complete Guide Series*
- [Part 1: Introducing gstack — Development Tools for the AI Agent Era](/posts/ai-agents/gstack-part1-introduction/)
- [Part 2: Installation and Core Workflow](/posts/ai-agents/gstack-part2-installation-workflow/)
- [Part 3: Browser Automation and Multi-Agent Execution](/posts/ai-agents/gstack-part3-browser-multiagent/)
- **Part 4: Development Philosophy for the AI Age** ← current post
