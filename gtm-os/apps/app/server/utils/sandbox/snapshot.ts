import { kv } from '@nuxthub/kv'
import type { SnapshotMetadata } from './types'
import { KV_KEYS } from './types'

/** Returns current snapshot metadata from KV, null if none exists */
export async function getCurrentSnapshot(): Promise<SnapshotMetadata | null> {
  return await kv.get<SnapshotMetadata>(KV_KEYS.CURRENT_SNAPSHOT)
}

/** Stores snapshot metadata as current snapshot in KV */
export async function setCurrentSnapshot(metadata: SnapshotMetadata): Promise<void> {
  await kv.set(KV_KEYS.CURRENT_SNAPSHOT, metadata)
}
