#!/bin/bash

################################################################################
# REQ-AGENT-0-1 Phase 1: Production Error Debugging
# 사내 마이그레이션 에러 원인 파악을 위한 디버그 로깅 테스트 실행기
#
# 사용법:
#   ./scripts/run_phase1_test.sh <MODEL>
#
# 예시:
#   ./scripts/run_phase1_test.sh gemini-2.0-flash
#   ./scripts/run_phase1_test.sh deepseek-v3-0324
#   ./scripts/run_phase1_test.sh gpt-oss-120b
#
# 동작:
#   - LOG_LEVEL=DEBUG, LITELLM_MODEL=<MODEL>을 설정하고 CLI를 실행합니다.
#   - 전체 CLI 세션을 raw 로그로 저장하고, 평문 로그(ANSI 제거)를 함께 생성합니다.
#   - 평문 로그에서 [Phase-1-Debug] 라인을 요약합니다.
################################################################################

set -euo pipefail

# ============================================================================
# 함수
# ============================================================================

print_step() { echo "📌 $1"; }
print_success() { echo "✅ $1"; }
print_warning() { echo "⚠️  $1"; }
print_error() { echo "❌ $1"; }

sanitize_log() {
    local src="$1"
    local dest="$2"
    # ANSI/OSC/CR/BS 제거, script header/footer 제거
    perl -ne '
        next if /^Script started on/ || /^Script done on/;
        s/\e\]0;.*?\a//g;          # OSC title
        s/\e\[[0-9;?]*[A-Za-z]//g; # CSI (colors, cursor moves)
        s/\r//g;                   # CR
        s/[\x0f\x0e]//g;           # shift in/out
        s/.\x08//g;                # backspace + prev char
        print;
    ' "$src" > "$dest"
}

# ============================================================================
# 입력 검증
# ============================================================================

if [ $# -eq 0 ]; then
    print_error "모델 이름이 필요합니다. 예: ./scripts/run_phase1_test.sh gpt-oss-120b"
    exit 1
fi

MODEL="$1"

# ============================================================================
# 로그 경로/타임스탬프
# ============================================================================

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MODEL_SAFE=$(echo "$MODEL" | tr '/' '_' | tr '-' '_')
LOG_DIR="logs/phase1_debug"
RAW_LOG="${LOG_DIR}/${MODEL_SAFE}_${TIMESTAMP}.raw.log"
PLAIN_LOG="${LOG_DIR}/${MODEL_SAFE}_${TIMESTAMP}.log"

mkdir -p "$LOG_DIR"

# ============================================================================
# 권한 확인
# ============================================================================

fix_permissions() {
    local target_dir="$1"
    if [ -d "$target_dir" ]; then
        local owner
        owner=$(stat -c %U "$target_dir" 2>/dev/null || stat -f %Su "$target_dir" 2>/dev/null || echo "")
        local current_user
        current_user=$(whoami)
        if [ "$owner" = "root" ] && [ "$current_user" != "root" ]; then
            print_warning "$target_dir 디렉터리 소유자가 root입니다. 권한을 수정합니다."
            sudo chown -R "$current_user:$current_user" "$target_dir"
        fi
    fi
}

fix_permissions "$LOG_DIR"

# ============================================================================
# 실행 정보 출력
# ============================================================================

echo ""
echo "================================================================================"
echo "  REQ-AGENT-0-1 Phase 1: Production Error Debugging"
echo "================================================================================"
echo ""
print_step "환경 설정"
print_success "LOG_LEVEL=DEBUG"
print_success "LITELLM_MODEL=$MODEL"
print_success "RAW 로그:   $RAW_LOG"
print_success "평문 로그:  $PLAIN_LOG"
echo ""
echo "CLI가 시작되면 아래 순서로 입력하세요:"
echo "  > auth login <username>"
echo "  > questions generate --domain AI --round 1"
echo "  > exit"
echo ""

# ============================================================================
# 환경 변수 설정
# ============================================================================

export LOG_LEVEL=DEBUG
export LITELLM_MODEL="$MODEL"

# ============================================================================
# CLI 실행 및 로그 수집
# ============================================================================

if command -v script >/dev/null 2>&1; then
    print_step "CLI 실행 중... (종료하려면 'exit')"
    script -q -c "./tools/dev.sh cli" "$RAW_LOG"
else
    print_warning "'script' 명령이 없어 tee로 대체합니다. 일부 ANSI 코드가 남을 수 있습니다."
    ./tools/dev.sh cli 2>&1 | tee "$RAW_LOG"
fi

print_step "로그 정제 중..."
sanitize_log "$RAW_LOG" "$PLAIN_LOG"
print_success "정제 완료: $PLAIN_LOG"

# ============================================================================
# Phase-1-Debug 요약
# ============================================================================

if grep -q "\[Phase-1-Debug" "$PLAIN_LOG"; then
    echo ""
    print_success "[Phase-1-Debug] 로그가 수집되었습니다. 상위 10줄:"
    echo ""
    grep "\[Phase-1-Debug" "$PLAIN_LOG" | head -n 10
else
    echo ""
    print_warning "[Phase-1-Debug] 패턴이 로그에 없습니다. LOG_LEVEL=DEBUG 설정 및 코드 경로를 확인하세요."
fi

echo ""
print_success "완료"
echo ""
