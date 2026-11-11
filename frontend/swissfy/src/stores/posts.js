import { ref } from 'vue'
import { defineStore } from 'pinia'
import { foldersApi, groupsApi } from '@/api/collections.js'

function ownedCollection(collection) {
  const items = ref(null)

  async function load() {
    if (items.value) return items.value
    items.value = await collection.list().catch(() => {
      throw new Error('Laden fehlgeschlagen.')
    })
    return items.value
  }

  function send(request) {
    return request.catch((error) => {
      throw new Error(error.detail ?? 'Speichern fehlgeschlagen.')
    })
  }

  async function create(body) {
    const item = await send(collection.create(body))
    items.value = [...(items.value ?? []), item].sort((a, b) => a.name.localeCompare(b.name))
    return item
  }

  async function update(id, body) {
    const item = await send(collection.update(id, body))
    items.value = items.value.map((existing) => (existing.id === id ? item : existing))
    return item
  }

  async function remove(id) {
    await send(collection.remove(id))
    items.value = items.value.filter((item) => item.id !== id)
  }

  function reset() {
    items.value = null
  }

  return { items, load, create, update, remove, reset }
}

export const useFoldersStore = defineStore('folders', () => ownedCollection(foldersApi))

export const useGroupsStore = defineStore('groups', () => ownedCollection(groupsApi))
