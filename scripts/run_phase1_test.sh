#!/bin/bash

################################################################################
# REQ-AGENT-0-1 Phase 1: Production Error Debugging
# 사내 마이그레이션 에러 원인 파악을 위한 디버그 로깅 테스트
#
# 사용법:
#   ./scripts/run_phase1_test.sh <MODEL>
#
# 예시:
#   ./scripts/run_phase1_test.sh gemini-2.0-flash
#   ./scripts/run_phase1_test.sh deepseek-v3-0324
#   ./scripts/run_phase1_test.sh gpt-oss-120b
#
# 참고: CLI와 로깅이 분리되어 있습니다.
# - CLI 실행: ./tools/dev.sh cli (별도 터미널)
# - 로깅 수집: tail -f ~/.local/share/slea-ssem/logs/*.log | grep '[Phase-1-Debug'
################################################################################

set -e  # Exit on error

# ============================================================================
# 함수 정의
# ============================================================================

print_header() {
    echo ""
    echo "================================================================================"
    echo "  REQ-AGENT-0-1 Phase 1: Production Error Debugging"
    echo "================================================================================"
    echo ""
}

print_step() {
    echo "📌 $1"
}

print_success() {
    echo "✅ $1"
}

print_warning() {
    echo "⚠️  $1"
}

print_error() {
    echo "❌ $1"
}

# ============================================================================
# 타임스탐프 미리 설정 (로그 파일명 생성용)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MODEL_SHORT=$(echo "$1" | tr '/' '_' | tr '-' '_')
LOG_FILE="logs/phase1_debug/${MODEL_SHORT}_${TIMESTAMP}.log"

# 입력 검증
# ============================================================================

if [ $# -eq 0 ]; then
    print_header
    print_error "모델 이름이 필요합니다"
    echo ""
    echo "사용법:"
    echo "  ./scripts/run_phase1_test.sh <MODEL>"
    echo ""
    echo "예시:"
    echo "  ./scripts/run_phase1_test.sh gemini-2.0-flash"
    echo "  ./scripts/run_phase1_test.sh deepseek-v3-0324"
    echo "  ./scripts/run_phase1_test.sh gpt-oss-120b"
    echo ""
    exit 1
fi

MODEL="$1"

# ============================================================================
# 권한 확인 및 수정
# ============================================================================

fix_permissions() {
    local logs_dir="logs"
    local phase1_dir="logs/phase1_debug"

    # logs 디렉토리 확인
    if [ ! -d "$logs_dir" ]; then
        mkdir -p "$logs_dir"
    fi

    # phase1_debug 디렉토리 확인
    if [ ! -d "$phase1_dir" ]; then
        mkdir -p "$phase1_dir"
    fi

    # 권한 확인 (root 소유인지 체크)
    if [ -d "$phase1_dir" ]; then
        local dir_owner=$(stat -c %U "$phase1_dir" 2>/dev/null || stat -f %Su "$phase1_dir" 2>/dev/null)
        local current_user=$(whoami)

        if [ "$dir_owner" = "root" ] && [ "$current_user" != "root" ]; then
            print_warning "logs/phase1_debug 디렉토리 권한 수정 필요 (root 소유)"
            echo ""
            echo "권한 수정 중... (sudo 필요할 수 있음)"

            # 권한 수정 시도
            if sudo rm -rf "$phase1_dir" 2>/dev/null && \
               sudo mkdir -p "$phase1_dir" 2>/dev/null && \
               sudo chown -R "$current_user:$current_user" "$logs_dir" 2>/dev/null; then
                print_success "권한 수정 완료"
                echo ""
            else
                # sudo 비밀번호 없이 실패한 경우
                print_warning "sudo를 사용하여 권한 수정 중..."
                echo ""
                sudo bash -c "rm -rf '$phase1_dir' && mkdir -p '$phase1_dir' && chown -R $current_user:$current_user '$logs_dir'" || {
                    print_error "권한 수정 실패. 다음 명령을 수동으로 실행해주세요:"
                    echo "  sudo bash -c 'rm -rf logs/phase1_debug && mkdir -p logs/phase1_debug && chown -R $(whoami):$(whoami) logs/'"
                    echo ""
                    exit 1
                }
                print_success "권한 수정 완료"
                echo ""
            fi
        fi
    fi
}

# 권한 수정 실행
fix_permissions

# ============================================================================
# 실행 시작
# ============================================================================

print_header

print_step "환경 설정"
print_step "모델: $MODEL"

# 로그 디렉토리 생성
mkdir -p logs/phase1_debug

# 환경 변수 설정
export LOG_LEVEL=DEBUG
export LITELLM_MODEL="$MODEL"

print_success "환경 설정 완료"
echo "  - LOG_LEVEL: $LOG_LEVEL"
echo "  - LITELLM_MODEL: $MODEL"
echo "  - 로그 파일: $LOG_FILE"
echo ""

# ============================================================================
# 다른 터미널에서 CLI를 실행하도록 안내
# ============================================================================

print_step "준비 완료! 다른 터미널에서 CLI를 실행하세요"
echo ""
echo "[터미널 2] 새로운 터미널 창을 열어서 다음 명령어를 순서대로 입력하세요:"
echo ""
echo "  export LOG_LEVEL=DEBUG"
echo "  export LITELLM_MODEL=$MODEL"
echo "  ./tools/dev.sh cli"
echo ""
echo "  그 후 CLI 프롬프트에서:"
echo "  > auth login <username>"
echo "  > questions generate --domain AI --round 1"
echo "  > exit"
echo ""
echo "───────────────────────────────────────────────────────────────────────────────"
echo ""

read -p "✓ CLI 실행 완료 후 Enter를 누르세요... "

echo ""

# ============================================================================
# 로그 수집 및 결과 표시
# ============================================================================

print_step "로그 수집 중..."

# CLI 로그 파일에서 [Phase-1-Debug]를 grep하여 저장
CLI_LOG_FILE="$HOME/.local/share/slea-ssem/logs/cli.log"
grep '\[Phase-1-Debug' "$CLI_LOG_FILE" 2>/dev/null > "$LOG_FILE" || true

if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
    echo ""
    print_success "테스트 완료! 🎉"
    echo ""
    echo "📊 수집된 [Phase-1-Debug] 로그:"
    echo ""
    cat "$LOG_FILE"
    echo ""
    echo "  총 라인: $(wc -l < "$LOG_FILE")"
    echo "  저장 위치: $LOG_FILE"
else
    echo ""
    print_error "로그가 수집되지 않았습니다"
    echo ""
    echo "확인할 사항:"
    echo "  1. LOG_LEVEL=DEBUG가 설정되었나? → 위의 '✅ 환경 설정 완료' 확인"
    echo "  2. CLI에서 questions generate을 실행했나?"
    echo "  3. ~/.local/share/slea-ssem/logs/cli.log 파일이 생성되었나?"
    echo ""
    echo "수동 확인:"
    echo "  grep '\\[Phase-1-Debug' ~/.local/share/slea-ssem/logs/cli.log"
fi

echo ""
