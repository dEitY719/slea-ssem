// REQ: REQ-F-B4-2
import { render, screen } from '@testing-library/react'
import { describe, test, expect } from 'vitest'
import { GradeBadge } from '../GradeBadge'

describe('GradeBadge - REQ-F-B4-2 (등급 배지 + 특수 배지)', () => {
  // Test 1: Elite 등급일 때 특수 배지 표시
  test('displays special badge for Elite grade', () => {
    // REQ: REQ-F-B4-2 - Elite 등급인 경우 특수 배지 표시
    render(<GradeBadge grade="Elite" />)

    // 기본 등급 배지 확인
    expect(screen.getByText('엘리트')).toBeInTheDocument()
    expect(screen.getByText('Elite')).toBeInTheDocument()

    // 특수 배지 확인
    expect(screen.getByText('Agent Specialist')).toBeInTheDocument()
  })

  // Test 2: Advanced 등급일 때 특수 배지 미표시
  test('does not display special badge for Advanced grade', () => {
    // REQ: REQ-F-B4-2 - Non-Elite 등급은 특수 배지 없음
    render(<GradeBadge grade="Advanced" />)

    // 기본 등급 배지 확인
    expect(screen.getByText('고급자')).toBeInTheDocument()
    expect(screen.getByText('Advanced')).toBeInTheDocument()

    // 특수 배지 미표시 확인
    expect(screen.queryByText('Agent Specialist')).not.toBeInTheDocument()
  })

  // Test 3: Intermediate 등급일 때 특수 배지 미표시
  test('does not display special badge for Intermediate grade', () => {
    // REQ: REQ-F-B4-2 - Non-Elite 등급은 특수 배지 없음
    render(<GradeBadge grade="Intermediate" />)

    // 기본 등급 배지 확인
    expect(screen.getByText('중급자')).toBeInTheDocument()
    expect(screen.getByText('Intermediate')).toBeInTheDocument()

    // 특수 배지 미표시 확인
    expect(screen.queryByText('Agent Specialist')).not.toBeInTheDocument()
  })

  // Test 4: Beginner 등급일 때 특수 배지 미표시
  test('does not display special badge for Beginner grade', () => {
    // REQ: REQ-F-B4-2 - Non-Elite 등급은 특수 배지 없음
    render(<GradeBadge grade="Beginner" />)

    // 기본 등급 배지 확인
    expect(screen.getByText('시작자')).toBeInTheDocument()
    expect(screen.getByText('Beginner')).toBeInTheDocument()

    // 특수 배지 미표시 확인
    expect(screen.queryByText('Agent Specialist')).not.toBeInTheDocument()
  })

  // Test 5: Intermediate-Advanced 등급일 때 특수 배지 미표시
  test('does not display special badge for Intermediate-Advanced grade', () => {
    // REQ: REQ-F-B4-2 - Non-Elite 등급은 특수 배지 없음
    render(<GradeBadge grade="Intermediate-Advanced" />)

    // 기본 등급 배지 확인
    expect(screen.getByText('중상급자')).toBeInTheDocument()
    expect(screen.getByText('Intermediate-Advanced')).toBeInTheDocument()

    // 특수 배지 미표시 확인
    expect(screen.queryByText('Agent Specialist')).not.toBeInTheDocument()
  })

  // Test 6: 등급 배지에 올바른 CSS 클래스 적용
  test('applies correct CSS class for grade', () => {
    // REQ: REQ-F-B4-2 - 시각적 표시 확인
    const { container, rerender } = render(<GradeBadge grade="Elite" />)

    // Elite 배지 클래스 확인
    expect(container.querySelector('.grade-elite')).toBeInTheDocument()

    // Advanced 배지로 재렌더링
    rerender(<GradeBadge grade="Advanced" />)
    expect(container.querySelector('.grade-advanced')).toBeInTheDocument()
  })
})
