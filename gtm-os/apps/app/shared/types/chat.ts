import type { UIMessage } from 'ai'
import type { DbChat, DbMessage } from '#shared/types/db'

export type ChatMode = DbChat['mode']

export interface UIChat {
  id: string
  label: string
  generating?: boolean
  icon: string
  mode: ChatMode
  createdAt: string
  to: string
  isPublic: boolean
  shareToken: string | null
}

export type GetChatsResponse = DbChat[]

export interface CreateChatBody {
  id: string
  mode?: ChatMode
  message: UIMessage
}

export type CreateChatResponse = DbChat

export type GetChatResponse = DbChat & {
  messages: DbMessage[]
}

export interface PatchChatShareBody {
  isPublic: boolean
}

export type PatchChatShareResponse = DbChat
