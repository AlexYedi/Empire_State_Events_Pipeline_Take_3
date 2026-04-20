import { getAgentConfig } from '../../utils/agent-config'

/**
 * GET /api/agent-config
 * Get the active agent configuration (admin only)
 */
export default defineEventHandler(async (event) => {
  await requireAdmin(event)
  return await getAgentConfig()
})
