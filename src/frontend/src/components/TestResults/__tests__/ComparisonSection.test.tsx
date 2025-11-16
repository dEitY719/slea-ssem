// REQ: REQ-F-B5-1
import { render, screen } from '@testing-library/react'
import { describe, test, expect } from 'vitest'
import { ComparisonSection } from '../ComparisonSection'
import { Grade, PreviousResult } from '../../../services/resultService'

describe('ComparisonSection - REQ-F-B5-1', () => {
  test('점수/등급 상승 시 개선 표시', () => {
    const previousResult: PreviousResult = {
      grade: 'Beginner' as Grade,
      score: 65,
      test_date: '2025-01-10T10:00:00Z',
    }

    render(
      <ComparisonSection
        currentGrade={'Intermediate' as Grade}
        currentScore={75}
        previousResult={previousResult}
      />
    )

    // 등급 변화 확인
    expect(screen.getByText('Beginner')).toBeInTheDocument()
    expect(screen.getByText('Intermediate')).toBeInTheDocument()
    // SVG 아이콘 확인 (arrow-up class)
    const upArrows = document.querySelectorAll('.arrow-up')
    expect(upArrows.length).toBe(2) // 등급, 점수 각각

    // 점수 변화 확인
    expect(screen.getByText('65점')).toBeInTheDocument()
    expect(screen.getByText('75점')).toBeInTheDocument()
    expect(screen.getByText('(+10점)')).toBeInTheDocument()

    // 개선 메시지 확인
    expect(screen.getByText(/10점 향상되었습니다!/i)).toBeInTheDocument()
  })

  test('점수/등급 하락 시 하락 표시', () => {
    const previousResult: PreviousResult = {
      grade: 'Intermediate' as Grade,
      score: 75,
      test_date: '2025-01-10T10:00:00Z',
    }

    render(
      <ComparisonSection
        currentGrade={'Beginner' as Grade}
        currentScore={65}
        previousResult={previousResult}
      />
    )

    // 등급 하락 확인 (SVG 아이콘)
    const downArrows = document.querySelectorAll('.arrow-down')
    expect(downArrows.length).toBe(2) // 등급, 점수 각각

    // 점수 하락 확인
    expect(screen.getByText('(-10점)')).toBeInTheDocument()

    // 하락 메시지 확인
    expect(screen.getByText(/10점 낮아졌습니다/i)).toBeInTheDocument()
  })

  test('변동 없음', () => {
    const previousResult: PreviousResult = {
      grade: 'Intermediate' as Grade,
      score: 75,
      test_date: '2025-01-10T10:00:00Z',
    }

    render(
      <ComparisonSection
        currentGrade={'Intermediate' as Grade}
        currentScore={75}
        previousResult={previousResult}
      />
    )

    // 변동 없음 표시 확인 (SVG 아이콘)
    expect(document.querySelectorAll('.arrow-right').length).toBeGreaterThan(0)
    expect(screen.getAllByText('(변동 없음)').length).toBe(2) // 등급, 점수 각각

    // 변동 없음 메시지 확인
    expect(screen.getByText(/이전과 동일한 성적입니다/i)).toBeInTheDocument()
  })

  test('이전 결과 없음 (첫 응시)', () => {
    render(
      <ComparisonSection
        currentGrade={'Intermediate' as Grade}
        currentScore={75}
        previousResult={null}
      />
    )

    // 첫 응시 메시지 확인
    expect(screen.getByText(/첫 응시입니다/i)).toBeInTheDocument()

    // 현재 결과만 표시 확인
    expect(screen.getByText('현재 등급:')).toBeInTheDocument()
    expect(screen.getByText('Intermediate')).toBeInTheDocument()
    expect(screen.getByText('현재 점수:')).toBeInTheDocument()
    expect(screen.getByText('75점')).toBeInTheDocument()

    // 비교 정보는 없어야 함 (SVG 아이콘 없음)
    expect(document.querySelectorAll('.arrow-right').length).toBe(0)
    expect(document.querySelectorAll('.arrow-up').length).toBe(0)
    expect(document.querySelectorAll('.arrow-down').length).toBe(0)
  })

  test('이전 테스트 날짜 표시', () => {
    const previousResult: PreviousResult = {
      grade: 'Beginner' as Grade,
      score: 65,
      test_date: '2025-01-10T10:00:00Z',
    }

    render(
      <ComparisonSection
        currentGrade={'Intermediate' as Grade}
        currentScore={75}
        previousResult={previousResult}
      />
    )

    // 날짜 표시 확인 (한국어 형식)
    expect(screen.getByText(/이전 테스트:/i)).toBeInTheDocument()
    expect(screen.getByText(/2025년/i)).toBeInTheDocument()
    expect(screen.getByText(/1월/i)).toBeInTheDocument()
  })

  test('등급은 같지만 점수만 상승', () => {
    const previousResult: PreviousResult = {
      grade: 'Intermediate' as Grade,
      score: 70,
      test_date: '2025-01-10T10:00:00Z',
    }

    render(
      <ComparisonSection
        currentGrade={'Intermediate' as Grade}
        currentScore={75}
        previousResult={previousResult}
      />
    )

    // 등급은 변동 없음
    const unchangedText = screen.getAllByText('(변동 없음)')
    expect(unchangedText.length).toBe(1) // 등급만 변동 없음

    // 점수는 상승
    expect(screen.getByText('70점')).toBeInTheDocument()
    expect(screen.getByText('75점')).toBeInTheDocument()
    expect(screen.getByText('(+5점)')).toBeInTheDocument()

    // 점수 상승 아이콘 (등급은 →, 점수만 ↑) - SVG 아이콘
    const upArrows = document.querySelectorAll('.arrow-up')
    expect(upArrows.length).toBe(1) // 점수만 상승

    // 개선 메시지
    expect(screen.getByText(/5점 향상되었습니다!/i)).toBeInTheDocument()
  })
})
