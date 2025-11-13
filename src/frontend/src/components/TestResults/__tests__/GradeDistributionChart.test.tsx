// REQ: REQ-F-B4-3
import { render, screen } from '@testing-library/react'
import { GradeDistributionChart } from '../GradeDistributionChart'
import type { GradeDistribution, Grade } from '../../../services/resultService'

describe('GradeDistributionChart', () => {
  // Test data
  const mockDistribution: GradeDistribution[] = [
    { grade: 'Beginner', count: 102, percentage: 20.2 },
    { grade: 'Intermediate', count: 156, percentage: 30.8 },
    { grade: 'Intermediate-Advanced', count: 98, percentage: 19.4 },
    { grade: 'Advanced', count: 95, percentage: 18.8 },
    { grade: 'Elite', count: 55, percentage: 10.8 },
  ]

  // Test 1: Happy path - 정상 렌더링
  describe('Happy Path', () => {
    it('should render all 5 grade bars', () => {
      render(
        <GradeDistributionChart
          distribution={mockDistribution}
          userGrade="Advanced"
          rank={3}
          totalCohortSize={506}
          percentileDescription="상위 28%"
        />
      )

      // 5개 등급이 모두 표시되는지 확인
      expect(screen.getByText(/시작자/i)).toBeInTheDocument()
      expect(screen.getByText(/중급자/i)).toBeInTheDocument()
      expect(screen.getByText(/중상급자/i)).toBeInTheDocument()
      expect(screen.getByText(/고급자/i)).toBeInTheDocument()
      expect(screen.getByText(/엘리트/i)).toBeInTheDocument()
    })

    it('should display count and percentage for each grade', () => {
      render(
        <GradeDistributionChart
          distribution={mockDistribution}
          userGrade="Advanced"
          rank={3}
          totalCohortSize={506}
          percentileDescription="상위 28%"
        />
      )

      // 첫 번째 등급의 카운트와 퍼센트 확인
      expect(screen.getByText(/102/)).toBeInTheDocument()
      expect(screen.getByText(/20.2%/)).toBeInTheDocument()
    })
  })

  // Test 2: User grade highlight
  describe('User Grade Highlighting', () => {
    it('should highlight the user current grade bar', () => {
      const { container } = render(
        <GradeDistributionChart
          distribution={mockDistribution}
          userGrade="Advanced"
          rank={3}
          totalCohortSize={506}
          percentileDescription="상위 28%"
        />
      )

      // Advanced 등급이 하이라이트되었는지 확인 (CSS 클래스)
      const bars = container.querySelectorAll('.distribution-bar')
      const advancedBar = Array.from(bars).find(bar =>
        bar.textContent?.includes('고급자')
      )
      expect(advancedBar).toHaveClass('user-current-grade')
    })

    it('should show "Your Position" indicator on user grade', () => {
      render(
        <GradeDistributionChart
          distribution={mockDistribution}
          userGrade="Elite"
          rank={5}
          totalCohortSize={506}
          percentileDescription="상위 5%"
        />
      )

      // "현재 위치" 또는 "Your Position" 표시 확인
      expect(screen.getByText(/현재 위치/i)).toBeInTheDocument()
    })
  })

  // Test 3: Text summary
  describe('Text Summary Display', () => {
    it('should display rank summary text', () => {
      render(
        <GradeDistributionChart
          distribution={mockDistribution}
          userGrade="Advanced"
          rank={3}
          totalCohortSize={506}
          percentileDescription="상위 28%"
        />
      )

      // "상위 28% (순위 3/506)" 형식 확인
      const summaryParagraph = screen.getByText(/상위 28%/).closest('.summary-text')
      if (!summaryParagraph) {
        throw new Error('Summary paragraph not found')
      }
      expect(summaryParagraph).toHaveTextContent('상위 28%')
      expect(summaryParagraph).toHaveTextContent('순위 3/506')
    })

    it('should display distribution chart title', () => {
      render(
        <GradeDistributionChart
          distribution={mockDistribution}
          userGrade="Advanced"
          rank={3}
          totalCohortSize={506}
          percentileDescription="상위 28%"
        />
      )

      expect(screen.getByText(/전사 상대 순위 및 분포/i)).toBeInTheDocument()
    })
  })

    // Test 4: Edge cases
    describe('Edge Cases', () => {
      it('should handle empty distribution gracefully', () => {
        render(
          <GradeDistributionChart
            distribution={[]}
            userGrade="Beginner"
            rank={1}
            totalCohortSize={1}
            percentileDescription="상위 100%"
          />
        )

        // 에러 없이 렌더링되어야 함
        expect(screen.getByText(/전사 상대 순위 및 분포/i)).toBeInTheDocument()
      })

      it('should handle large cohort size (1000+)', () => {
        const largeDistribution: GradeDistribution[] = [
          { grade: 'Beginner', count: 250, percentage: 25.0 },
          { grade: 'Intermediate', count: 300, percentage: 30.0 },
          { grade: 'Intermediate-Advanced', count: 200, percentage: 20.0 },
          { grade: 'Advanced', count: 150, percentage: 15.0 },
          { grade: 'Elite', count: 100, percentage: 10.0 },
        ]

        render(
          <GradeDistributionChart
            distribution={largeDistribution}
            userGrade="Elite"
            rank={50}
            totalCohortSize={1000}
            percentileDescription="상위 5%"
          />
        )

        const summaryParagraph = screen.getByText(/상위 5%/).closest('.summary-text')
        if (!summaryParagraph) {
          throw new Error('Summary paragraph not found')
        }
        expect(summaryParagraph).toHaveTextContent('순위 50/1000')
      })

      it('should handle single grade distribution', () => {
        const singleGrade: GradeDistribution[] = [
          { grade: 'Beginner', count: 10, percentage: 100.0 },
        ]

        render(
          <GradeDistributionChart
            distribution={singleGrade}
            userGrade="Beginner"
            rank={1}
            totalCohortSize={10}
            percentileDescription="상위 10%"
          />
        )

        expect(screen.getByText(/시작자/i)).toBeInTheDocument()
        expect(screen.getByText(/100%/)).toBeInTheDocument()
      })

      it('should clamp negative bar heights to zero', () => {
        const invalidDistribution: GradeDistribution[] = [
          { grade: 'Beginner', count: -10, percentage: -5 },
          { grade: 'Intermediate', count: 0, percentage: 0 },
        ]

        const { container } = render(
          <GradeDistributionChart
            distribution={invalidDistribution}
            userGrade="Beginner"
            rank={1}
            totalCohortSize={100}
            percentileDescription="상위 10%"
          />
        )

        const bars = Array.from(container.querySelectorAll('.distribution-bar'))
        expect(bars[0]?.getAttribute('style')).toContain('--bar-height: 0%')
      })

      it('should default NaN bar heights to zero', () => {
        const nanDistribution: GradeDistribution[] = [
          { grade: 'Beginner', count: Number.NaN, percentage: 10 },
          { grade: 'Intermediate', count: 50, percentage: 90 },
        ]

        const { container } = render(
          <GradeDistributionChart
            distribution={nanDistribution}
            userGrade="Intermediate"
            rank={2}
            totalCohortSize={200}
            percentileDescription="상위 20%"
          />
        )

        const bars = Array.from(container.querySelectorAll('.distribution-bar'))
        expect(bars[0]?.getAttribute('style')).toContain('--bar-height: 0%')
        expect(bars[1]?.getAttribute('style')).toContain('--bar-height: 0%')
      })
    })

  // Test 5: Acceptance criteria (REQ-F-B4-3)
  describe('Acceptance Criteria - REQ-F-B4-3', () => {
    it('should display grade distribution chart with all grades', () => {
      render(
        <GradeDistributionChart
          distribution={mockDistribution}
          userGrade="Advanced"
          rank={3}
          totalCohortSize={506}
          percentileDescription="상위 28%"
        />
      )

      // ✅ 등급 분포 막대 차트 표시
      expect(screen.getByRole('img', { name: /grade distribution/i })).toBeInTheDocument()
    })

    it('should highlight user current position in chart', () => {
      const { container } = render(
        <GradeDistributionChart
          distribution={mockDistribution}
          userGrade="Advanced"
          rank={3}
          totalCohortSize={506}
          percentileDescription="상위 28%"
        />
      )

      // ✅ 사용자의 현재 위치가 하이라이트됨
      const highlightedBars = container.querySelectorAll('.user-current-grade')
      expect(highlightedBars.length).toBeGreaterThan(0)
    })

    it('should display text summary with rank and percentile', () => {
      render(
        <GradeDistributionChart
          distribution={mockDistribution}
          userGrade="Advanced"
          rank={3}
          totalCohortSize={506}
          percentileDescription="상위 28%"
        />
      )

      // ✅ 텍스트 요약 표시 ("상위 28% (순위 3/506)")
      const summaryParagraph = screen.getByText(/상위 28%/).closest('.summary-text')
      if (!summaryParagraph) {
        throw new Error('Summary paragraph not found')
      }
      expect(summaryParagraph).toHaveTextContent('상위 28%')
      expect(summaryParagraph).toHaveTextContent('순위 3/506')
    })
  })

  // Test 6: Accessibility
  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(
        <GradeDistributionChart
          distribution={mockDistribution}
          userGrade="Advanced"
          rank={3}
          totalCohortSize={506}
          percentileDescription="상위 28%"
        />
      )

      // ARIA role="img" for chart
      expect(screen.getByRole('img')).toBeInTheDocument()
    })

    it('should have descriptive text for screen readers', () => {
      const { container } = render(
        <GradeDistributionChart
          distribution={mockDistribution}
          userGrade="Advanced"
          rank={3}
          totalCohortSize={506}
          percentileDescription="상위 28%"
        />
      )

      // aria-label 또는 sr-only 텍스트 확인
      const ariaLabels = container.querySelectorAll('[aria-label]')
      expect(ariaLabels.length).toBeGreaterThan(0)
    })
  })
})
