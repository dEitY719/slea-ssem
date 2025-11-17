// REQ: REQ-F-B4-1
import React from 'react'
import { ChartBarIcon, TrophyIcon, SparklesIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { formatDecimal } from '../../utils/gradeHelpers'

interface BaseMetricCardProps {
  title: string
}

interface ScoreCardProps extends BaseMetricCardProps {
  type: 'score'
  score: number
}

interface RankCardProps extends BaseMetricCardProps {
  type: 'rank'
  rank: number
  totalCohortSize: number
  showConfidenceWarning?: boolean
}

interface PercentileCardProps extends BaseMetricCardProps {
  type: 'percentile'
  percentileDescription: string
  percentile: number
}

type MetricCardProps = ScoreCardProps | RankCardProps | PercentileCardProps

/**
 * Metric Card Component
 * Displays score, rank, or percentile information
 */
export const MetricCard: React.FC<MetricCardProps> = (props) => {
  const { title, type } = props

  // Select icon based on type
  const IconComponent = type === 'score' ? ChartBarIcon : type === 'rank' ? TrophyIcon : SparklesIcon

  return (
    <div className="metric-card">
      <div className="metric-header">
        <IconComponent className="metric-icon" />
        <h2 className="metric-title">{title}</h2>
      </div>

      {type === 'score' && (
        <>
          <p className="metric-value">
            {formatDecimal(props.score)} <span className="metric-unit">/ 100</span>
          </p>
          <div className="progress-bar-container">
            <div
              className="progress-bar"
              role="progressbar"
              aria-valuenow={props.score}
              aria-valuemin={0}
              aria-valuemax={100}
              style={{ width: `${props.score}%` }}
            />
          </div>
        </>
      )}

      {type === 'rank' && (
        <>
          <p className="metric-value">
            {props.rank} <span className="metric-separator">/</span> {props.totalCohortSize}
          </p>
          <p className="metric-description">전체 응시자 중</p>
          {props.showConfidenceWarning && (
            <p className="confidence-warning">
              <ExclamationTriangleIcon className="warning-icon" />
              분포 신뢰도 낮음 (참고용)
            </p>
          )}
        </>
      )}

      {type === 'percentile' && (
        <>
          <p className="metric-value">{props.percentileDescription}</p>
          <p className="metric-description">
            상위 {formatDecimal(100 - props.percentile)}% 내
          </p>
        </>
      )}
    </div>
  )
}
