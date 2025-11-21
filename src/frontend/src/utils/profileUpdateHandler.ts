/**
 * Profile Update Handler
 *
 * Provides a handler map pattern for processing profile update operations
 */

import { profileService } from '../services/profileService'
import { levelToBackend } from './levelMapping'
import type { ProfileFormData } from './profileChangeDetector'

export interface UpdateHandlerContext {
  current: ProfileFormData
  original: ProfileFormData
}

export interface UpdateHandler {
  shouldExecute: (ctx: UpdateHandlerContext) => boolean
  execute: (ctx: UpdateHandlerContext) => Promise<void>
  description: string
}

/**
 * Handler for nickname updates
 */
export const nicknameUpdateHandler: UpdateHandler = {
  description: 'Update nickname',
  shouldExecute: (ctx) => ctx.current.nickname !== ctx.original.nickname,
  execute: async (ctx) => {
    await profileService.registerNickname(ctx.current.nickname)
  },
}

/**
 * Handler for survey data updates
 */
export const surveyDataUpdateHandler: UpdateHandler = {
  description: 'Update survey data',
  shouldExecute: (ctx) => {
    return (
      ctx.current.level !== ctx.original.level ||
      ctx.current.career !== ctx.original.career ||
      ctx.current.jobRole !== ctx.original.jobRole ||
      ctx.current.duty !== ctx.original.duty ||
      ctx.current.interests !== ctx.original.interests
    )
  },
  execute: async (ctx) => {
    if (ctx.current.level === null) {
      throw new Error('Level is required for survey update')
    }

    await profileService.updateSurvey({
      level: levelToBackend(ctx.current.level),
      career: ctx.current.career,
      job_role: ctx.current.jobRole,
      duty: ctx.current.duty,
      interests: ctx.current.interests ? [ctx.current.interests] : [],
    })
  },
}

/**
 * Default handler map for profile updates
 * Handlers are executed in order
 */
export const defaultUpdateHandlers: UpdateHandler[] = [
  nicknameUpdateHandler,
  surveyDataUpdateHandler,
]

/**
 * Execute profile update handlers
 * @param ctx - Update context with current and original data
 * @param handlers - Array of handlers to execute (defaults to defaultUpdateHandlers)
 * @returns Array of executed handler descriptions
 */
export async function executeProfileUpdate(
  ctx: UpdateHandlerContext,
  handlers: UpdateHandler[] = defaultUpdateHandlers
): Promise<string[]> {
  const executedHandlers: string[] = []

  for (const handler of handlers) {
    if (handler.shouldExecute(ctx)) {
      await handler.execute(ctx)
      executedHandlers.push(handler.description)
    }
  }

  return executedHandlers
}

/**
 * Check if any handlers need to be executed
 * @param ctx - Update context
 * @param handlers - Array of handlers to check
 * @returns Whether any handlers need to be executed
 */
export function hasUpdates(
  ctx: UpdateHandlerContext,
  handlers: UpdateHandler[] = defaultUpdateHandlers
): boolean {
  return handlers.some((handler) => handler.shouldExecute(ctx))
}
