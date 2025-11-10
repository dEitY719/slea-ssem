// REQ: REQ-F-A2 (임시 페이지)
import React from 'react'
import './SignupPage.css'

const SignupPage: React.FC = () => {
  return (
    <main className="signup-page">
      <div className="signup-container">
        <h1 className="signup-title">회원가입</h1>
        <p className="signup-description">환영합니다! 닉네임을 등록해주세요.</p>
        <div className="placeholder-content">
          <p>🚧 이 페이지는 REQ-F-A2 구현 대기 중입니다.</p>
          <p>닉네임 입력 및 중복 확인 기능이 추가될 예정입니다.</p>
        </div>
      </div>
    </main>
  )
}

export default SignupPage
