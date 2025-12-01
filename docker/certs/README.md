# Certificate Management

## 📁 폴더 구조

```
certs/
├── README.md         # 이 파일
├── .gitkeep          # Git에 빈 폴더 유지용
└── internal/         # 사내 전용 인증서 (gitignore에 추가)
    ├── McAfee_Certificate.crt
    ├── SECDS-T2IssuingCA.crt
    └── SECDS-T2ROOTCA.crt
```

## 🏠 외부 환경 (집/공개망)

**필요한 작업**: 없음

- `certs/` 폴더는 비어있어도 됩니다.
- Dockerfile이 자동으로 건너뜁니다.

## 🏢 사내 환경 (회사/폐쇄망)

**⚠️ 중요**: 인증서 파일(*.crt)은 **보안팀 정책에 따라 Git에 포함되지 않습니다**.

**필요한 작업**: 인증서 수동 복사 (매번 필요)

```bash
# 1. internal 폴더 생성 (이미 생성됨)
# mkdir -p docker/certs/internal

# 2. 인증서 파일 복사 (기존 assets/ 폴더에서)
cp assets/*.crt docker/certs/internal/

# 또는 직접 다운로드한 인증서 복사
cp ~/Downloads/*.crt docker/certs/internal/
```

## ⚠️ 보안 주의사항

- `certs/internal/` 폴더는 `.gitignore`에 추가됨
- 인증서 파일은 **절대 Git에 커밋하지 마세요**
- 팀원과 공유 시 별도 채널(사내 메일, Confluence 등) 이용

## 🧪 테스트

```bash
# 인증서가 제대로 복사되었는지 확인
ls -la docker/certs/internal/

# 예상 출력:
# McAfee_Certificate.crt
# SECDS-T2IssuingCA.crt
# SECDS-T2ROOTCA.crt
```
