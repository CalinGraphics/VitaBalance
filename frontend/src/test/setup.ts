// Mediu de test: localStorage curat (limba implicită RO) și API-uri de browser lipsă în jsdom.
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

const g = globalThis as unknown as { ResizeObserver?: unknown }
g.ResizeObserver = g.ResizeObserver ?? ResizeObserverStub
