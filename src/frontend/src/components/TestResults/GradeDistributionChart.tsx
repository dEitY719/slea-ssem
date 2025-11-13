// REQ: REQ-F-B4-3
import React from 'react'
import type { GradeDistribution, Grade } from '../../services/resultService'
import { GradeBar } from './GradeBar'

interface GradeDistributionChartProps {
  distribution: GradeDistribution[]
  userGrade: Grade
  rank: number
  totalCohortSize: number
  percentileDescription: string
}

/**
 * Grade Distribution Chart Component
 *
 * REQ: REQ-F-B4-3 - Display grade distribution bar chart with user position
 *
 * Features:
 * - Bar chart showing grade distribution (Beginner ~ Elite)
 * - Highlight user's current grade
 * - Display count and percentage for each grade
 * - Text summary with rank and percentile
 */
export const GradeDistributionChart: React.FC<GradeDistributionChartProps> = ({
  distribution,
  userGrade,
  rank,
  totalCohortSize,
  percentileDescription,
}) => {
  // Find max count for scaling bars
  const maxCount = Math.max(...distribution.map(d => d.count), 1)

  return (
    <div className="grade-distribution-container">
      <h2 className="distribution-title">전사 상대 순위 및 분포</h2>

      {/* Text Summary */}
      <div className="distribution-summary">
        <p className="summary-text">
          <span className="summary-percentile">{percentileDescription}</span>
          <span className="summary-rank"> (순위 {rank}/{totalCohortSize})</span>
        </p>
        <p className="summary-description">최근 90일 응시자 기준</p>
      </div>

      {/* Bar Chart */}
      <div
        className="distribution-chart"
        role="img"
        aria-label="Grade distribution chart showing user position"
      >
        {distribution.map((item) => (
          <GradeBar
            key={item.grade}
            grade={item.grade}
            count={item.count}
            percentage={item.percentage}
            isUserGrade={item.grade === userGrade}
            barHeightPercentage={(item.count / maxCount) * 100}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="distribution-legend">
        <div className="legend-item">
          <span className="legend-icon legend-icon-normal"></span>
          <span className="legend-text">전체 분포</span>
        </div>
        <div className="legend-item">
          <span className="legend-icon legend-icon-user"></span>
          <span className="legend-text">내 등급</span>
        </div>
      </div>
    </div>
  )
}
