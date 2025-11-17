# Test Design: REQ-F-A2-Profile-Access-1

## Test Cases

### Test 1: Happy Path - 닉네임 표시
**Given**: nickname="태호", isLoading=false
**When**: Header 컴포넌트 렌더링
**Then**: 
- 헤더 오른쪽 상단에 "태호" 텍스트가 표시된다
- "회원가입" 버튼은 표시되지 않는다
- 닉네임 영역에 적절한 aria-label이 있다

### Test 2: 닉네임 null - 회원가입 버튼 표시
**Given**: nickname=null, isLoading=false
**When**: Header 컴포넌트 렌더링
**Then**: 
- "회원가입" 버튼이 표시된다
- 닉네임 텍스트는 표시되지 않는다

### Test 3: 상호 배타성 - 닉네임과 회원가입 버튼
**Given**: nickname="민준", isLoading=false
**When**: Header 컴포넌트 렌더링
**Then**: 
- 닉네임 "민준"이 표시된다
- "회원가입" 버튼은 표시되지 않는다
- 두 요소가 동시에 표시되지 않는다

### Test 4: Loading 중 - 아무것도 표시하지 않음
**Given**: nickname=null, isLoading=true
**When**: Header 컴포넌트 렌더링
**Then**: 
- "회원가입" 버튼이 표시되지 않는다
- 닉네임 텍스트도 표시되지 않는다

### Test 5: 닉네임 변경 - 동적 업데이트
**Given**: 초기 nickname="유진"
**When**: nickname prop이 "유진쓰"로 변경
**Then**: 
- 헤더에 "유진쓰"가 표시된다
- 이전 닉네임 "유진"은 표시되지 않는다

### Test 6: Accessibility - Screen Reader 지원
**Given**: nickname="태호"
**When**: 스크린 리더가 헤더를 읽음
**Then**: 
- "현재 로그인: 태호" 또는 유사한 텍스트가 aria-label로 제공된다
- role 속성이 적절히 설정된다

### Test 7: Edge Case - 특수문자 포함 닉네임
**Given**: nickname="테스터_123"
**When**: Header 컴포넌트 렌더링
**Then**: 
- 특수문자를 포함한 닉네임이 정상적으로 표시된다
- XSS 공격 방어 (React의 기본 escape 동작 검증)

### Test 8: Edge Case - 긴 닉네임
**Given**: nickname="아주긴닉네임테스트1234567890"
**When**: Header 컴포넌트 렌더링
**Then**: 
- 닉네임이 잘리거나 오버플로우 없이 표시된다
- 모바일 화면에서도 정상 표시된다
