import type { InferInsertModel, InferSelectModel } from 'drizzle-orm'
import type { agentConfig, apiUsage, chats, messages, sources, usageStats } from '@nuxthub/db/schema'

export type DbChat = InferSelectModel<typeof chats>
export type NewDbChat = InferInsertModel<typeof chats>

export type DbMessage = InferSelectModel<typeof messages>
export type NewDbMessage = InferInsertModel<typeof messages>

export type DbSource = InferSelectModel<typeof sources>
export type NewDbSource = InferInsertModel<typeof sources>

export type DbAgentConfig = InferSelectModel<typeof agentConfig>
export type NewDbAgentConfig = InferInsertModel<typeof agentConfig>

export type DbApiUsage = InferSelectModel<typeof apiUsage>
export type NewDbApiUsage = InferInsertModel<typeof apiUsage>

export type DbUsageStat = InferSelectModel<typeof usageStats>
export type NewDbUsageStat = InferInsertModel<typeof usageStats>
