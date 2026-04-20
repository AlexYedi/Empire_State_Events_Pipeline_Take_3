<script setup lang="ts">
import type { PatchChatShareBody, PatchChatShareResponse } from '#shared/types/chat'

const props = defineProps<{
  chatId: string
  isPublic: boolean
  shareToken: string | null
}>()

const emit = defineEmits<{
  close: [boolean]
}>()

const toast = useToast()
const isToggling = ref(false)
const localIsPublic = ref(props.isPublic)
const localShareToken = ref(props.shareToken)

watch(() => props.isPublic, (val) => {
  localIsPublic.value = val
})

watch(() => props.shareToken, (val) => {
  localShareToken.value = val
})

const shareUrl = computed(() => {
  if (!localShareToken.value) return ''
  return `${window.location.origin}/shared/${localShareToken.value}`
})

async function togglePublic(value: boolean) {
  isToggling.value = true
  try {
    const updated = await $fetch<PatchChatShareResponse>(`/api/chats/${props.chatId}/share`, {
      method: 'PATCH',
      body: { isPublic: value } satisfies PatchChatShareBody
    })
    localIsPublic.value = updated.isPublic
    localShareToken.value = updated.shareToken
    refreshNuxtData('chats')
  } finally {
    isToggling.value = false
  }
}

async function copyLink() {
  if (shareUrl.value) {
    await navigator.clipboard.writeText(shareUrl.value)
    toast.add({
      title: 'Link copied',
      icon: 'i-lucide-check'
    })
  }
}
</script>

<template>
  <UModal
    title="Share Chat"
    description="Make this chat public to share it with others"
    :ui="{
      footer: 'flex-row-reverse justify-start'
    }"
    :close="false"
  >
    <template #body>
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="font-medium">
              Public access
            </p>
            <p class="text-sm text-muted">
              {{ localIsPublic ? 'Anyone with the link can view' : 'Only you can access this chat' }}
            </p>
          </div>
          <USwitch
            :model-value="localIsPublic"
            :loading="isToggling"
            @update:model-value="togglePublic"
          />
        </div>

        <div v-if="localIsPublic && shareUrl" class="flex flex-col gap-2">
          <label class="text-sm font-medium">Share link</label>
          <div class="flex gap-2">
            <UInput
              :model-value="shareUrl"
              readonly
              class="flex-1 font-mono text-sm"
            />
            <UButton
              icon="i-lucide-copy"
              color="neutral"
              @click="copyLink"
            />
          </div>
          <p class="text-xs text-muted">
            Making this chat private will invalidate this link
          </p>
        </div>
      </div>
    </template>

    <template #footer>
      <UButton label="Done" @click="emit('close', true)" />
    </template>
  </UModal>
</template>
