// REQ: REQ-F-B4-2
import { render, screen } from '@testing-library/react'
import { describe, test, expect } from 'vitest'
import { SpecialBadge } from '../SpecialBadge'

describe('SpecialBadge - REQ-F-B4-2 (특수 배지 컴포넌트)', () => {
  // Test 1: "Agent Specialist" 배지 렌더링
  test('renders Agent Specialist badge with text', () => {
    // REQ: REQ-F-B4-2 - 특수 배지 시각적 표시
    render(<SpecialBadge badgeType="Agent Specialist" />)

    // 배지명 확인
    expect(screen.getByText('Agent Specialist')).toBeInTheDocument()
  })

  // Test 2: 특수 배지에 올바른 CSS 클래스 적용
  test('applies correct CSS class for special badge', () => {
    // REQ: REQ-F-B4-2 - 시각적 구분
    const { container } = render(<SpecialBadge badgeType="Agent Specialist" />)

    // 특수 배지 클래스 확인
    expect(container.querySelector('.special-badge')).toBeInTheDocument()
  })

  // Test 3: 특수 배지 아이콘 존재 확인
  test('displays icon for special badge', () => {
    // REQ: REQ-F-B4-2 - 아이콘 + 텍스트 구성
    const { container } = render(<SpecialBadge badgeType="Agent Specialist" />)

    // 아이콘이 있는지 확인 (SVG 또는 아이콘 클래스)
    const icon = container.querySelector('.special-badge-icon')
    expect(icon).toBeInTheDocument()
  })
})
