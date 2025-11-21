/**
 * Container Component
 *
 * Provides consistent max-width and responsive padding across the application.
 *
 * Usage:
 * ```tsx
 * <Container>
 *   <h1>Page Content</h1>
 * </Container>
 * ```
 *
 * Styling:
 * - max-width: 1200px (max-w-6xl)
 * - Centered: mx-auto
 * - Responsive padding: px-4 sm:px-6 lg:px-8
 */

import React from 'react'

interface ContainerProps {
  children: React.ReactNode
  className?: string
}

export const Container: React.FC<ContainerProps> = ({ children, className = '' }) => {
  return (
    <div className={`max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 ${className}`}>
      {children}
    </div>
  )
}
