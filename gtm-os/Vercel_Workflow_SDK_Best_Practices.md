Vercel Workflow SDK Best Practices
A comprehensive guide to building durable, production-ready workflows with the Vercel Workflow SDK.
Quick Reference
Pattern	Use Case	Key Feature
**Step Functions**	Atomic, retriable operations	`'use step'` directive
**Webhooks**	Human-in-the-loop, external triggers	Workflow pauses until response
**Actors**	Long-running, event-driven workflows	Process events sequentially
**Streaming**	Real-time frontend updates	`getWritable()` / `readable`
**In-Memory Map**	Simple state sharing	Shared between steps & routes
**PostgreSQL**	Permanent storage with embeddings	Production persistence
***State Persistence Patterns
1. In-Memory Map (Simple)
Best for: Prototyping, simple state sharing between workflow steps and API routes.
```typescript
// store.ts
export const store = new Map<string, any>();
// workflow.ts
import { store } from './store';
export async function myWorkflow(id: string) {
  'use workflow';
  store.set(id, { status: 'processing' });
  const result = await processData();
  store.set(id, { status: 'complete', result });
  return result;
}
// api/status/route.ts
import { store } from '@/store';
export async function GET(req: Request) {
  const id = new URL(req.url).searchParams.get('id');
  return Response.json(store.get(id) ?? { status: 'not_found' });
}
```
2. PostgreSQL with Drizzle (Production)
Best for: Permanent storage, complex queries, embeddings (RAG patterns).
```typescript
// db/schema.ts
import { pgTable, text, jsonb, timestamp } from 'drizzle-orm/pg-core';
export const workflowRuns = pgTable('workflow_runs', {
  id: text('id').primaryKey(),
  status: text('status').notNull(),
  result: jsonb('result'),
  createdAt: timestamp('created_at').defaultNow(),
});
// workflow.ts
export async function myWorkflow(id: string) {
  'use workflow';
  await db.insert(workflowRuns).values({ id, status: 'processing' });
  const result = await processData();
  await db.update(workflowRuns)
    .set({ status: 'complete', result })
    .where(eq(workflowRuns.id, id));
  return result;
}
```
3. Step Return Values (Automatic)
The workflow runtime automatically persists step return values for replay.
```typescript
export async function myWorkflow() {
  'use workflow';
  // This result is automatically persisted
  const data = await fetchExternalData();
  // On replay, fetchExternalData() is NOT re-executed
  const processed = await processData(data);
  return processed;
}
```
***Step Functions
Critical Rules
Same File Requirement: Steps must be defined in the SAME FILE as the workflow for bundler discovery.
Use the Directive: Mark durable operations with `'use step'`.
Atomic Side-Effects: Each step should contain one atomic operation.
```typescript
// ✅ CORRECT: Steps in same file as workflow
export async function fetchUserData(userId: string) {
  'use step';
  const response = await fetch(`/api/users/${userId}`);
  return response.json();
}
export async function sendNotification(email: string, message: string) {
  'use step';
  await emailService.send({ to: email, body: message });
}
export async function myWorkflow(userId: string) {
  'use workflow';
  const user = await fetchUserData(userId);
  await sendNotification(user.email, 'Welcome!');
  return { success: true };
}
```
Error Types
Error Type	Behavior	Use Case
`Error`	Auto-retried with exponential backoff	Transient failures
`FatalError`	Stops workflow immediately	Unrecoverable errors
`RetryableError`	Custom retry timing	Rate limits, quotas
```typescript
import { FatalError, RetryableError } from 'workflow';
export async function callExternalAPI() {
  'use step';
  const response = await fetch('https://api.example.com/data');
  if (response.status === 401) {
    throw new FatalError('Invalid API credentials');
  }
  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After') ?? '60';
    throw new RetryableError('Rate limited', { delaySeconds: parseInt(retryAfter) });
  }
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}
```
***Webhook Pattern (Human-in-the-Loop)
Perfect for: Approval workflows, email confirmations, external callbacks.
```typescript
import { createWebhook } from 'workflow';
export async function approvalWorkflow(requestId: string, approverEmail: string) {
  'use workflow';
  const webhook = createWebhook();
  await sendApprovalEmail({
    to: approverEmail,
    subject: 'Approval Required',
    body: `Click to approve: ${webhook.url}?action=approve&requestId=${requestId}`,
  });
  // Workflow PAUSES here until webhook is called
  const response = await webhook;
  const url = new URL(response.url);
  const action = url.searchParams.get('action');
  if (action === 'approve') {
    await processApproval(requestId);
    return { status: 'approved' };
  }
  return { status: 'rejected' };
}
```
***AI SDK Integration
The Vercel AI SDK requires a special pattern to work with durable workflows.
```typescript
import { fetch } from 'workflow';
import { generateText, generateObject } from 'ai';
import { openai } from '@ai-sdk/openai';
export async function aiWorkflow(prompt: string) {
  'use workflow';
  // Critical: Override globalThis.fetch with workflow's durable fetch
  globalThis.fetch = fetch;
  const { text } = await generateText({
    model: openai('gpt-4o'),
    prompt,
  });
  return { response: text };
}
```
Structured Output with generateObject
```typescript
import { z } from 'zod';
const AnalysisSchema = z.object({
  sentiment: z.enum(['positive', 'negative', 'neutral']),
  keywords: z.array(z.string()),
  summary: z.string(),
});
export async function analyzeContent(content: string) {
  'use workflow';
  globalThis.fetch = fetch;
  const { object } = await generateObject({
    model: openai('gpt-4o'),
    schema: AnalysisSchema,
    prompt: `Analyze this content: ${content}`,
  });
  return object;
}
```
***API Route Patterns
Starting a Workflow
```typescript
import { start } from 'workflow';
import { myWorkflow } from '@/workflows/myWorkflow';
export async function POST(req: Request) {
  const { input } = await req.json();
  const run = await start(myWorkflow, [input]);
  return Response.json({ runId: run.id, status: 'started' });
}
```
Waiting for Completion (Blocking)
```typescript
export async function POST(req: Request) {
  const { input } = await req.json();
  const run = await start(myWorkflow, [input]);
  // Blocks until workflow completes - use for short workflows only!
  const result = await run.returnValue;
  return Response.json({ result });
}
```
Streaming Responses
```typescript
export async function POST(req: Request) {
  const { input } = await req.json();
  const run = await start(streamingWorkflow, [input]);
  return new Response(run.readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
    },
  });
}
```
Resuming Streams
```typescript
import { getRun } from 'workflow';
export async function GET(req: Request) {
  const url = new URL(req.url);
  const runId = url.searchParams.get('runId');
  const startIndex = parseInt(url.searchParams.get('startIndex') ?? '0');
  const run = getRun(runId);
  const readable = run.getReadable({ startIndex });
  return new Response(readable, {
    headers: { 'Content-Type': 'text/event-stream' },
  });
}
```
***Error Handling
In API Routes
```typescript
import { start, isFatalError } from 'workflow';
export async function POST(req: Request) {
  try {
    const { input } = await req.json();
    const run = await start(myWorkflow, [input]);
    const result = await run.returnValue;
    return Response.json({ result });
  } catch (error) {
    const fatal = isFatalError(error);
    return Response.json(
      { error: error.message, fatal },
      { status: fatal ? 400 : 500 }
    );
  }
}
```
***Actor Pattern (Long-Running Workflows)
Best for: Chat sessions, game loops, persistent agents, event-driven systems.
```typescript
import { defineHook } from 'workflow';
type ChatEvent =
  | { type: 'message'; content: string }
  | { type: 'disconnect' };
export const chatHook = defineHook<ChatEvent>();
export async function chatActor(sessionId: string) {
  'use workflow';
  const receive = chatHook.create({ token: `chat:${sessionId}` });
  const messages: string[] = [];
  for await (const event of receive) {
    if (event.type === 'message') {
      messages.push(event.content);
      await processMessage(event.content);
    } else if (event.type === 'disconnect') {
      return { messages };
    }
  }
}
```
Sending Events to Actors
```typescript
import { chatHook } from '@/workflows/chatActor';
export async function POST(req: Request) {
  const { sessionId, message } = await req.json();
  await chatHook.send({
    token: `chat:${sessionId}`,
    event: { type: 'message', content: message },
  });
  return Response.json({ sent: true });
}
```
***Intermediate Results & Streaming
Using getWritable() for Real-Time Updates
```typescript
import { getWritable } from 'workflow';
export async function progressWorkflow(taskId: string) {
  'use workflow';
  const writable = getWritable();
  const writer = writable.getWriter();
  await writer.write({ step: 1, message: 'Starting...' });
  await step1();
  await writer.write({ step: 2, message: 'Processing...' });
  await step2();
  await writer.write({ step: 3, message: 'Complete!' });
  await writer.close();
  return { success: true };
}
```
Polling Pattern for State Updates
```typescript
export const progressStore = new Map<string, { step: number; message: string }>();
export async function longRunningWorkflow(taskId: string) {
  'use workflow';
  progressStore.set(taskId, { step: 1, message: 'Initializing' });
  await initialize();
  progressStore.set(taskId, { step: 2, message: 'Waiting for approval' });
  const webhook = createWebhook();
  await sendApprovalRequest(webhook.url);
  // Workflow pauses, but frontend can poll progressStore
  await webhook;
  progressStore.set(taskId, { step: 3, message: 'Complete' });
  return { success: true };
}
```
***Summary
Concept	Key Takeaway
**Steps**	Same file, `'use step'`, atomic operations
**Errors**	`Error` retries, `FatalError` stops, `RetryableError` custom timing
**Webhooks**	`createWebhook()` → send URL → `await webhook` pauses
**AI SDK**	Set `globalThis.fetch = fetch` from workflow
**Streaming**	`run.readable` or `getWritable()` for real-time
**Actors**	`defineHook` + `for await` for event-driven
**State**	Map (simple), Postgres (production), step returns (automatic)
***Generated from analysis of the Vercel Workflow Examples repository.
