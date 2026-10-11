import { ref } from 'vue'
import { defineStore } from 'pinia'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'

function ownedCollection(url) {
  const items = ref(null)

  async function load() {
    if (items.value) return items.value
    const response = await apiFetch(url)
    if (!response.ok) throw new Error('Laden fehlgeschlagen.')
    items.value = await response.json()
    return items.value
  }

  async function send(path, method, body) {
    const response = await apiFetch(`${url}${path}`, { method, body: JSON.stringify(body) })
    const data = await response.json().catch(() => null)
    if (!response.ok) throw new Error(extractErrorMessage(data, 'Speichern fehlgeschlagen.'))
    return data
  }

  async function create(body) {
    const item = await send('', 'POST', body)
    items.value = [...(items.value ?? []), item].sort((a, b) => a.name.localeCompare(b.name))
    return item
  }

  async function update(id, body) {
    const item = await send(`${id}/`, 'PATCH', body)
    items.value = items.value.map((existing) => (existing.id === id ? item : existing))
    return item
  }

  async function remove(id) {
    await send(`${id}/`, 'DELETE')
    items.value = items.value.filter((item) => item.id !== id)
  }

  function reset() {
    items.value = null
  }

  return { items, load, create, update, remove, reset }
}

export const useFoldersStore = defineStore('folders', () => ownedCollection('/api/posts/folders/'))

export const useGroupsStore = defineStore('groups', () => ownedCollection('/api/posts/groups/'))
