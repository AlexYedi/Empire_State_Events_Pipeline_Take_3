import { defineClientAuth } from '@onmax/nuxt-better-auth/config'
import { adminClient } from 'better-auth/client/plugins'
import { apiKeyClient } from '@better-auth/api-key/client'

export default defineClientAuth({
  plugins: [adminClient(), apiKeyClient()],
})
