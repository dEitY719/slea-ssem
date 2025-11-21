/**
 * PageLayout Component
 *
 * Provides consistent page structure with Header and Main content areas.
 *
 * Usage:
 * ```tsx
 * // With header
 * <PageLayout showHeader nickname="user123">
 *   <h1>Page Content</h1>
 * </PageLayout>
 *
 * // Without header
 * <PageLayout>
 *   <h1>Page Content</h1>
 * </PageLayout>
 *
 * // Custom className for main
 * <PageLayout mainClassName="custom-spacing">
 *   <h1>Page Content</h1>
 * </PageLayout>
 * ```
 *
 * Layout Structure:
 * - Header: Uses Container component (max-w-6xl, responsive padding)
 * - Main: py-10 lg:py-14 space-y-10 lg:space-y-14
 * - Container: Applied automatically to main content
 */

import React from 'react'
import { Header } from './Header'
import { Container } from './Container'

interface PageLayoutProps {
  children: React.ReactNode

  /**
   * Show header at top of page
   * @default false
   */
  showHeader?: boolean

  /**
   * User's nickname for Header component
   * Required if showHeader is true
   */
  nickname?: string | null

  /**
   * Loading state for nickname (passed to Header)
   */
  isNicknameLoading?: boolean

  /**
   * Additional className for main element
   * Base classes: "py-10 lg:py-14"
   */
  mainClassName?: string

  /**
   * Additional className for container
   * Base classes: "space-y-10 lg:space-y-14"
   */
  containerClassName?: string
}

export const PageLayout: React.FC<PageLayoutProps> = ({
  children,
  showHeader = false,
  nickname,
  isNicknameLoading = false,
  mainClassName = '',
  containerClassName = '',
}) => {
  return (
    <>
      {showHeader && (
        <Header nickname={nickname || null} isLoading={isNicknameLoading} />
      )}

      <main className={`py-10 lg:py-14 ${mainClassName}`}>
        <Container className={`space-y-10 lg:space-y-14 ${containerClassName}`}>
          {children}
        </Container>
      </main>
    </>
  )
}
