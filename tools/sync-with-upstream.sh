#!/bin/bash

# ============================================================
# Sync with Upstream Script
# 사외 저장소(Upstream)의 최신 코드를 사내 저장소에 가져오기
# Outside-In 전략 구현
# ============================================================

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수: 에러 메시지 출력
error() {
    echo -e "${RED}❌ 오류: $1${NC}"
    exit 1
}

# 함수: 성공 메시지 출력
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 함수: 정보 메시지 출력
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 함수: 경고 메시지 출력
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ============================================================
# 1. 현재 상태 확인
# ============================================================

info "현재 Git 상태 확인 중..."

# 현재 디렉토리가 Git 저장소인지 확인
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    error "현재 디렉토리가 Git 저장소가 아닙니다"
fi

# 로컬 변경사항 확인
if ! git diff-index --quiet HEAD --; then
    warning "커밋되지 않은 변경사항이 있습니다"
    echo "다음 명령으로 커밋 또는 stash하세요:"
    echo "  git add . && git commit -m 'WIP: ...'"
    echo "  또는"
    echo "  git stash"
    exit 1
fi

success "로컬 저장소 상태 정상"

# ============================================================
# 2. Upstream 확인
# ============================================================

info "Upstream 저장소 확인 중..."

# Upstream이 등록되어 있는지 확인
if ! git remote get-url upstream > /dev/null 2>&1; then
    error "Upstream 저장소가 등록되지 않았습니다"
    echo "다음 명령으로 등록하세요:"
    echo "  git remote add upstream https://github.com/dEitY719/slea-ssem.git"
fi

UPSTREAM_URL=$(git remote get-url upstream)
success "Upstream 등록됨: $UPSTREAM_URL"

# ============================================================
# 3. 최신 코드 가져오기
# ============================================================

info "🔄 Upstream에서 develop 브랜치 가져오는 중..."

if ! git fetch upstream develop; then
    error "Upstream에서 가져오기 실패"
    echo "네트워크 연결을 확인하세요"
    echo "또는 Upstream URL을 확인하세요:"
    echo "  git remote get-url upstream"
fi

success "Upstream에서 가져오기 완료"

# ============================================================
# 4. 현재 브랜치 확인 및 전환
# ============================================================

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
info "현재 브랜치: $CURRENT_BRANCH"

# develop으로 전환
if [ "$CURRENT_BRANCH" != "develop" ]; then
    warning "develop 브랜치로 전환 중..."
    if ! git checkout develop; then
        error "develop 브랜치로 전환 실패"
    fi
fi

success "develop 브랜치에서 작업 중"

# ============================================================
# 5. Merge
# ============================================================

info "🔀 upstream/develop을 merge 중..."

if ! git merge upstream/develop; then
    error "Merge 실패 (충돌 발생)"
    echo ""
    echo "충돌을 해결하세요:"
    echo "  1. git status로 충돌 파일 확인"
    echo "  2. 파일 편집하여 충돌 해결"
    echo "  3. git add ."
    echo "  4. git commit -m 'fix: merge conflict'"
    exit 1
fi

success "Merge 완료"

# ============================================================
# 6. 결과 확인
# ============================================================

info "✨ 동기화 완료!"
echo ""
echo "📊 Commit 로그 (최근 5개):"
git log --oneline -5

echo ""
echo "📌 다음 단계:"
echo "  1. 변경사항 확인: git status"
echo "  2. 테스트 실행: docker-compose exec backend pytest tests/backend/ -v"
echo "  3. 반영사항 확인: git diff origin/develop"
echo "  4. 준비 완료 시: git push origin develop"
echo ""
success "준비 완료!"
