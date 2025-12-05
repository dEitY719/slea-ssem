// Handle leveltest intent
// Purpose: Level test flow - check consent → nickname → start test

import { profileService } from '../../services/profileService'
import type { ContinueContext } from './types'

/**
 * Handle leveltest intent
 *
 * Flow:
 * 1. Check consent status
 * 2. If not consented → navigate to /consent
 * 3. Check nickname status
 * 4. If no nickname → navigate to /signup
 * 5. If all checks pass → navigate to /test/start
 *
 * @param ctx - Continue context with navigate function
 * @throws Error on API failures
 */
export async function handleLeveltest(ctx: ContinueContext): Promise<void> {
  console.log('[Continue] Handling leveltest intent')

  try {
    // Step 1: Check consent (Private-Auth API)
    const consentData = await profileService.getConsentStatus()

    if (!consentData.consented) {
      console.log('[Continue] User has not consented, navigating to /consent')
      ctx.navigate('/consent', { replace: true })
      return
    }

    // Step 2: Check nickname (Private-Auth API)
    const nicknameData = await profileService.getNickname()

    if (!nicknameData.nickname) {
      console.log('[Continue] User has no nickname, navigating to /signup')
      ctx.navigate('/signup', { replace: true })
      return
    }

    // All checks passed - start level test
    console.log('[Continue] All checks passed, navigating to /test/start')
    ctx.navigate('/test/start', { replace: true })
  } catch (err) {
    console.error('[Continue] Leveltest flow failed:', err)
    throw err
  }
}
