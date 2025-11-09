# src/cli/config/command_layout.py

"""
CLI 명령어의 계층 구조를 정의하는 설정 파일입니다.
이 구조는 Pydantic 모델에 의해 검증되며, main.py의 커맨드 파서가 사용합니다.

- 최상위 키: 1-depth 명령어 (예: 'profile')
- 'description': 명령어에 대한 설명 (help 메시지로 사용됨)
- 'sub_commands': 하위 명령어들을 포함하는 딕셔너리
- 'target': 명령어가 최종적으로 실행할 함수 경로 ('모듈.함수명')
"""

COMMAND_LAYOUT = {
    "auth": {
        "description": "인증 및 세션 관리",
        "target": "src.cli.actions.auth.auth_help",
        "sub_commands": {
            "login": {
                "description": "Samsung AD 로그인 (JWT 토큰 발급)",
                "target": "src.cli.actions.auth.login",
            }
        },
    },
    "survey": {
        "description": "자기평가 Survey 관리",
        "target": "src.cli.actions.survey.survey_help",
        "sub_commands": {
            "schema": {
                "description": "Survey 폼 스키마 조회",
                "target": "src.cli.actions.survey.get_survey_schema",
            },
            "submit": {
                "description": "Survey 데이터 제출 및 저장",
                "target": "src.cli.actions.survey.submit_survey",
            },
        },
    },
    "profile": {
        "description": "사용자 프로필 및 닉네임 관리",
        "target": "src.cli.actions.profile.profile_help",
        "sub_commands": {
            "nickname": {
                "description": "닉네임 관련 명령어",
                "target": "src.cli.actions.profile.profile_help",
                "sub_commands": {
                    "check": {
                        "description": "닉네임 중복 확인",
                        "target": "src.cli.actions.profile.check_nickname_availability",
                    },
                    "register": {
                        "description": "닉네임 등록",
                        "target": "src.cli.actions.profile.register_nickname",
                    },
                    "edit": {
                        "description": "닉네임 수정",
                        "target": "src.cli.actions.profile.edit_nickname",
                    },
                },
            },
            "update_survey": {
                "description": "Survey 업데이트 (새 프로필 레코드 생성)",
                "target": "src.cli.actions.profile.update_survey",
            },
        },
    },
    "questions": {
        "description": "테스트 문항 생성, 채점, 저장",
        "target": "src.cli.actions.questions.questions_help",
        "sub_commands": {
            "session": {
                "description": "테스트 세션 관리",
                "target": "src.cli.actions.questions.questions_help",
                "sub_commands": {
                    "resume": {
                        "description": "테스트 세션 재개",
                        "target": "src.cli.actions.questions.resume_session",
                    },
                    "status": {
                        "description": "세션 상태 변경 (일시중지/재개)",
                        "target": "src.cli.actions.questions.update_session_status",
                    },
                    "time_status": {
                        "description": "세션 시간 제한 확인",
                        "target": "src.cli.actions.questions.check_time_status",
                    },
                },
            },
            "generate": {
                "description": "테스트 문항 생성 (Round 1)",
                "target": "src.cli.actions.questions.generate_questions",
                "sub_commands": {
                    "adaptive": {
                        "description": "적응형 문항 생성 (Round 2+)",
                        "target": "src.cli.actions.questions.generate_adaptive_questions",
                    }
                },
            },
            "answer": {
                "description": "답변 처리",
                "target": "src.cli.actions.questions.questions_help",
                "sub_commands": {
                    "autosave": {
                        "description": "답변 자동 저장",
                        "target": "src.cli.actions.questions.autosave_answer",
                    },
                    "score": {
                        "description": "단일 답변 채점",
                        "target": "src.cli.actions.questions.score_answer",
                    },
                },
            },
            "score": {
                "description": "라운드 점수 계산 및 저장",
                "target": "src.cli.actions.questions.calculate_round_score",
            },
            "explanation": {
                "description": "해설 생성",
                "target": "src.cli.actions.questions.questions_help",
                "sub_commands": {
                    "generate": {
                        "description": "해설 생성",
                        "target": "src.cli.actions.questions.generate_explanation",
                    }
                },
            },
        },
    },
    "help": {
        "description": "사용 가능한 명령어 목록을 보여줍니다.",
        "target": "src.cli.actions.system.help",
    },
    "exit": {
        "description": "CLI를 종료합니다.",
        "target": "src.cli.actions.system.exit_cli",
    },
}
