// 임시 Dashboard 페이지
import React from 'react'
import './DashboardPage.css'

const DashboardPage: React.FC = () => {
  return (
    <main className="dashboard-page">
      <div className="dashboard-container">
        <h1 className="dashboard-title">대시보드</h1>
        <p className="dashboard-description">환영합니다! 로그인에 성공했습니다.</p>
        <div className="placeholder-content">
          <p>🚧 이 페이지는 구현 대기 중입니다.</p>
          <p>레벨 테스트, 결과 조회, 재응시 등의 기능이 추가될 예정입니다.</p>
        </div>
      </div>
    </main>
  )
}

export default DashboardPage
