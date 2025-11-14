// REQ: REQ-F-A1-2
import React from 'react'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import './ErrorMessage.css'

interface ErrorMessageProps {
  title?: string
  message: string
  helpLinks?: Array<{
    text: string
    href: string
  }>
}

/**
 * Error message component with optional help links
 *
 * @param title - Error title (default: "오류 발생")
 * @param message - Error message to display
 * @param helpLinks - Optional array of help links
 */
export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = '오류 발생',
  message,
  helpLinks,
}) => {
  return (
    <div className="error-container">
      <div className="error-header">
        <ExclamationTriangleIcon className="error-icon" />
        <h2 className="error-title">{title}</h2>
      </div>
      <p className="error-message">{message}</p>
      {helpLinks && helpLinks.length > 0 && (
        <div className="error-links">
          {helpLinks.map((link, index) => (
            <a
              key={index}
              href={link.href}
              className="help-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              {link.text}
            </a>
          ))}
        </div>
      )}
    </div>
  )
}
