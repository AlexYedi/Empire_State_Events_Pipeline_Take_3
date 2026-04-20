# API Keys

API keys allow external services to authenticate with Knowledge Agent Template without a browser session. They use [Better Auth](https://www.better-auth.com)'s [API key plugin](https://www.better-auth.com/docs/plugins/api-key) to create a virtual session tied to the key owner.

## Admin Keys

Admin keys have full access to all endpoints, including admin-only routes.

1. Navigate to **Admin > API Keys** (`/admin/api-keys`)
2. Click **Create API Key**
3. Copy the key immediately -- it won't be shown again

## User Keys

Regular users can create keys scoped to their own permissions.

1. Navigate to **Settings > API Keys**
2. Click **Create API Key**
3. Copy the key immediately

## Usage

Include the key in your requests using either header:

```bash
# Authorization header
curl -H "Authorization: Bearer sk_live_..." <your-url>/api/chat

# x-api-key header
curl -H "x-api-key: sk_live_..." <your-url>/api/chat
```

Both headers are equivalent. Use whichever fits your HTTP client best.

API keys are the recommended way to authenticate when using the [SDK](/admin/docs/sdk):

```typescript
import { createSavoir } from '@savoir/sdk'

const savoir = createSavoir({
  apiUrl: process.env.SAVOIR_API_URL!,
  apiKey: process.env.SAVOIR_API_KEY!, // your API key
})
```

## Rotation & Revocation

- To **revoke** a key, click the delete button next to it in the API Keys page
- To **rotate** a key, create a new one, update your services, then revoke the old key
- Revoked keys are immediately invalidated -- in-flight requests using a revoked key will fail
