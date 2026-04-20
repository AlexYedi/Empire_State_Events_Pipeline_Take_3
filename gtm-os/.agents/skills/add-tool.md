# Add AI Tool

Guide for adding a new AI SDK tool to the `@savoir/agent` package.

## Steps

### 1. Create the Tool

Create `packages/agent/src/tools/my-tool.ts`.

Tools **must use `async function*` (generator)** and yield status updates so the frontend can display loading state and results automatically.

```typescript
import { tool } from 'ai'
import { z } from 'zod'

export const myTool = tool({
  description: 'Clear description of what this tool does — the AI model reads this to decide when to use it',
  inputSchema: z.object({
    query: z.string().describe('What the parameter is for'),
  }),
  execute: async function* ({ query }) {
    // 1. Yield loading state — the frontend shows a spinner
    yield { status: 'loading' as const }
    const start = Date.now()

    try {
      // 2. Your tool logic here
      const result = await doSomething(query)

      // 3. Yield done state with results — the frontend displays the output
      yield {
        status: 'done' as const,
        durationMs: Date.now() - start,
        text: result,
        commands: [
          {
            title: `My tool: "${query}"`,
            command: '',
            stdout: result,
            stderr: '',
            exitCode: 0,
            success: true,
          },
        ],
      }
    } catch (error) {
      // 4. Yield error state
      yield {
        status: 'done' as const,
        durationMs: Date.now() - start,
        text: '',
        commands: [
          {
            title: `My tool: "${query}"`,
            command: '',
            stdout: '',
            stderr: error instanceof Error ? error.message : 'Failed',
            exitCode: 1,
            success: false,
          },
        ],
      }
    }
  },
})
```

### Key Points about Yield

- **`yield { status: 'loading' }`** — Must be yielded first. The frontend uses this to show a loading indicator for the tool call.
- **`yield { status: 'done', ... }`** — Must be yielded last. Contains the results displayed in the chat UI.
- The `commands` array format matches the sandbox bash tool output, so the frontend renders it consistently.
- See `packages/agent/src/tools/web-search.ts` for a complete real-world example.

### 2. Export the Tool

Add the export in `packages/agent/src/index.ts`:

```typescript
export { myTool } from './tools/my-tool'
```

### 3. Register in the Agent

In the agent creation (e.g. `apps/app/server/utils/chat/`), add the tool to the tools object:

```typescript
import { myTool } from '@savoir/agent'

const tools = {
  ...savoir.tools,
  my_tool: myTool,
}
```

### 4. Update Prompts (optional)

If the tool needs specific instructions, update the relevant prompt in `packages/agent/src/prompts/`:

```typescript
// In chat.ts or bot.ts, add to the Available Tools section:
// - **my_tool**: Description of when and how to use this tool
```

## Existing Tools

| Tool | File | Description |
|------|------|-------------|
| `webSearchTool` | `tools/web-search.ts` | Web search for information not in the sandbox |
| `bash` | `@savoir/sdk` | Execute bash commands in the sandbox |
| `bash_batch` | `@savoir/sdk` | Execute multiple bash commands |
