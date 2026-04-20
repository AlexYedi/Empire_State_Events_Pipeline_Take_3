import { db, schema } from '@nuxthub/db'
import { and, eq } from 'drizzle-orm'
import { z } from 'zod'
import type { PatchChatShareBody, PatchChatShareResponse } from '#shared/types/chat'

const paramsSchema = z.object({
  id: z.string().min(1, 'Missing chat ID'),
})

export default defineEventHandler(async (event) => {
  const requestLog = useLogger(event)
  const { user } = await requireUserSession(event)
  const { id } = await getValidatedRouterParams(event, paramsSchema.parse)

  const { isPublic } = await readValidatedBody<PatchChatShareBody>(event, z.object({
    isPublic: z.boolean()
  }).parse)

  requestLog.set({ chatId: id, isPublic })

  const chat = await db.query.chats.findFirst({
    where: () => and(
      eq(schema.chats.id, id),
      eq(schema.chats.userId, user.id)
    )
  })

  if (!chat) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Chat not found',
      data: { why: 'No chat exists with this ID for your user account', fix: 'Verify the chat ID is correct' },
    })
  }

  const shareToken = isPublic ? crypto.randomUUID() : null

  const [updated] = await db.update(schema.chats)
    .set({ isPublic, shareToken })
    .where(eq(schema.chats.id, id))
    .returning()

  if (!updated) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Failed to update chat sharing settings',
      data: { why: 'The database update did not return the updated chat row', fix: 'Try again or check server logs for database errors' },
    })
  }

  return updated satisfies PatchChatShareResponse
})
