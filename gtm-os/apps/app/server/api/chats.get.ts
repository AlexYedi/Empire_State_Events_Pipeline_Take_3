import { db, schema } from '@nuxthub/db'
import { eq, desc } from 'drizzle-orm'
import type { GetChatsResponse } from '#shared/types/chat'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)

  const chats = await db.query.chats.findMany({
    where: () => eq(schema.chats.userId, user.id),
    orderBy: () => desc(schema.chats.createdAt)
  })

  return chats satisfies GetChatsResponse
})
