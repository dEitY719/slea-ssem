// Test mock mode persistence across page navigation
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { getTransport } from '../index'
import { mockTransport } from '../mockTransport'
import { realTransport } from '../realTransport'

describe('Mock Mode Persistence', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    // Clear URL parameters
    window.history.replaceState({}, '', window.location.pathname)
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('should use realTransport by default', () => {
    const transport = getTransport()
    // Compare constructor names since instances are different
    expect(transport.constructor.name).toBe(realTransport.constructor.name)
  })

  it('should switch to mockTransport when api_mock flag is set in localStorage', () => {
    localStorage.setItem('slea_ssem_api_mock', 'true')
    const transport = getTransport()
    expect(transport.constructor.name).toBe(mockTransport.constructor.name)
  })

  it('should persist mock mode after URL parameter is removed', () => {
    // Simulate URL parameter
    window.history.replaceState({}, '', '?api_mock=true')
    const transport1 = getTransport()
    expect(transport1.constructor.name).toBe(mockTransport.constructor.name)

    // Simulate navigation to new page (URL parameter removed)
    window.history.replaceState({}, '', '/home')
    const transport2 = getTransport()
    // Should still use mockTransport because flag is in localStorage
    expect(transport2.constructor.name).toBe(mockTransport.constructor.name)
  })

  it('should support legacy mock=true parameter', () => {
    window.history.replaceState({}, '', '?mock=true')
    const transport = getTransport()
    expect(transport.constructor.name).toBe(mockTransport.constructor.name)
  })

  it('should prioritize URL parameter over localStorage', () => {
    localStorage.setItem('slea_ssem_api_mock', 'false')
    window.history.replaceState({}, '', '?api_mock=true')
    const transport = getTransport()
    expect(transport.constructor.name).toBe(mockTransport.constructor.name)
  })
})
