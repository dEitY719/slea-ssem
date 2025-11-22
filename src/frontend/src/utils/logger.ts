const enableDebugLogs = import.meta.env?.VITE_ENABLE_DEBUG_LOGS === 'true'

export const debugLog = (...args: unknown[]) => {
  if (enableDebugLogs) {
    console.log(...args)
  }
}

export const debugWarn = (...args: unknown[]) => {
  if (enableDebugLogs) {
    console.warn(...args)
  }
}
