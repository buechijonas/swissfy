import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useEventsStore } from '@/stores/events.js'

class FakeEventSource extends EventTarget {
  static instances = []

  constructor(url) {
    super()
    this.url = url
    this.closed = false
    FakeEventSource.instances.push(this)
  }

  emit(type) {
    this.dispatchEvent(new Event(type))
  }

  close() {
    this.closed = true
  }
}

describe('events store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    FakeEventSource.instances = []
    vi.stubGlobal('EventSource', FakeEventSource)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('opens a single stream', () => {
    const events = useEventsStore()
    events.connect()
    events.connect()
    expect(FakeEventSource.instances).toHaveLength(1)
    expect(FakeEventSource.instances[0].url).toBe('/api/events/')
  })

  it('counts changes per kind', () => {
    const events = useEventsStore()
    events.connect()
    const [source] = FakeEventSource.instances
    source.emit('chat')
    source.emit('chat')
    source.emit('notification')
    expect(events.chat).toBe(2)
    expect(events.notification).toBe(1)
  })

  it('resyncs everything when the stream opens again', () => {
    const events = useEventsStore()
    events.connect()
    const [source] = FakeEventSource.instances
    source.emit('error')
    expect(events.connected).toBe(false)
    source.emit('open')
    expect(events.connected).toBe(true)
    expect(events.chat).toBe(1)
    expect(events.notification).toBe(1)
  })

  it('closes the stream on disconnect', () => {
    const events = useEventsStore()
    events.connect()
    events.disconnect()
    expect(FakeEventSource.instances[0].closed).toBe(true)
    events.connect()
    expect(FakeEventSource.instances).toHaveLength(2)
  })
})
