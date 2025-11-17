import React, { ReactNode } from 'react'
import './InfoBox.css'

interface InfoBoxProps {
  title: string
  icon?: ReactNode
  children: ReactNode
  className?: string
}

/**
 * InfoBox - Reusable information display component
 * 
 * @param title - Box title text
 * @param icon - Optional custom icon (defaults to info icon)
 * @param children - Content (typically <ul className="info-list">)
 * @param className - Additional CSS classes
 * 
 * @example
 * <InfoBox title="닉네임 규칙">
 *   <ul className="info-list">
 *     <li>3-30자 사이로 입력해주세요</li>
 *     <li>영문자, 숫자, 언더스코어(_)만 사용 가능합니다</li>
 *   </ul>
 * </InfoBox>
 * 
 * @example With custom icon
 * <InfoBox title="수준 선택 가이드" icon={InfoBoxIcons.check}>
 *   <ul className="info-list">
 *     <li>본인의 현재 기술 수준을 솔직하게 평가해주세요</li>
 *   </ul>
 * </InfoBox>
 */
export const InfoBox: React.FC<InfoBoxProps> = ({ 
  title, 
  icon, 
  children, 
  className = '' 
}) => {
  // Default info icon
  const defaultIcon = (
    <svg className="info-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        strokeWidth={2} 
        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
      />
    </svg>
  )

  return (
    <div className={`info-box ${className}`}>
      <div className="info-title">
        {icon || defaultIcon}
        {title}
      </div>
      {children}
    </div>
  )
}

// Predefined icon variants for common use cases
export const InfoBoxIcons = {
  info: (
    <svg className="info-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  check: (
    <svg className="info-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  clock: (
    <svg className="info-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  arrowRight: (
    <svg className="info-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
}

export default InfoBox
