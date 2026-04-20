# @savoir/agent

Framework-agnostic agent core for Knowledge Agent Template. Handles question routing, prompt management, agent creation, and AI tool definitions.

> See also: [Main README](../../README.md), [Architecture](../../docs/ARCHITECTURE.md), [Customization](../../docs/CUSTOMIZATION.md)

## Overview

This package provides the AI agent infrastructure used by the chat interface and bots. It is designed to be consumed by `apps/app` but can also be used independently.

## Components

### Router

The router classifies incoming questions by complexity and selects the appropriate model and step count.

| Complexity | Max Steps | Model |
|-----------|-----------|-------|
| trivial | 4 | gemini-3-flash |
| simple | 8 | gemini-3-flash |
| moderate | 15 | claude-sonnet-4.6 |
| complex | 25 | claude-opus-4.6 |

```typescript
import { routeQuestion } from '@savoir/agent'

const config = await routeQuestion(question)
// { complexity: 'moderate', maxSteps: 15, model: 'claude-sonnet-4.6', reasoning: '...' }
```

### Prompts

System prompts for different contexts:

| File | Function | Purpose |
|------|----------|---------|
| `router.ts` | `ROUTER_SYSTEM_PROMPT` | Question classification |
| `chat.ts` | `buildChatSystemPrompt()` | Chat interface |
| `chat.ts` | `buildAdminSystemPrompt()` | Admin assistant |
| `bot.ts` | `buildBotSystemPrompt()` | Bot responses |
| `shared.ts` | `applyAgentConfig()` | Config overlay (style, language, citations) |

### Agents

Pre-configured agent factories:

- **`createAgent()`** — Base agent for chat and bot responses
- **`createAdminAgent()`** — Admin assistant with stats/management tools
- **`createSourceAgent()`** — Source-specific agent

### Tools

- **`webSearchTool`** — Web search tool for finding information not in the sandbox

### Types

Key types exported:

```typescript
import type {
  AgentConfigData,
  ThreadContext,
  RoutingResult,
  AgentExecutionContext,
  CreateAgentOptions,
  AgentCallOptions,
  AgentConfig,
} from '@savoir/agent'
```

## Customization

To customize AI behavior:

1. **Admin UI** — Change response style, language, temperature, etc. at `/admin/agent`
2. **Prompts** — Edit files in `src/prompts/` for deeper customization
3. **Router** — Modify `src/prompts/router.ts` to adjust complexity classification
4. **Tools** — Add new tools in `src/tools/`

## License

MIT
