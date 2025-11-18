"""
CLI command hierarchy configuration.

This module defines the hierarchical structure of CLI commands.
The structure is validated by Pydantic models and used by the command parser in main.py.

Keys:
    - Top-level: First-depth commands (e.g., 'profile')
    - 'description': Description of the command for help messages
    - 'sub_commands': Dictionary containing sub-commands
    - 'target': Module path of the function to execute ('module.function')
"""

COMMAND_LAYOUT = {
    "auth": {
        "description": "인증 및 세션 관리",
        "usage": "auth [subcommand]",
        "target": "src.cli.actions.auth.auth_help",
        "sub_commands": {
            "login": {
                "description": "Samsung AD 로그인 (JWT 토큰 발급)",
                "usage": "auth login [username]",
                "target": "src.cli.actions.auth.login",
            }
        },
    },
    "survey": {
        "description": "자기평가 Survey 관리",
        "usage": "survey [subcommand]",
        "target": "src.cli.actions.survey.survey_help",
        "sub_commands": {
            "schema": {
                "description": "Survey 폼 스키마 조회",
                "usage": "survey schema",
                "target": "src.cli.actions.survey.get_survey_schema",
            },
            "submit": {
                "description": "Survey 데이터 제출 및 저장",
                "usage": "survey submit [level] [career] [interests]",
                "target": "src.cli.actions.survey.submit_survey",
            },
        },
    },
    "profile": {
        "description": "사용자 프로필 및 닉네임 관리",
        "usage": "profile [subcommand]",
        "target": "src.cli.actions.profile.profile_help",
        "sub_commands": {
            "nickname": {
                "description": "닉네임 관련 명령어",
                "usage": "profile nickname [subcommand]",
                "target": "src.cli.actions.profile.profile_help",
                "sub_commands": {
                    "check": {
                        "description": "닉네임 중복 확인",
                        "usage": "profile nickname check [nickname]",
                        "target": "src.cli.actions.profile.check_nickname_availability",
                    },
                    "register": {
                        "description": "닉네임 등록",
                        "usage": "profile nickname register [nickname]",
                        "target": "src.cli.actions.profile.register_nickname",
                    },
                    "view": {
                        "description": "현재 닉네임 조회",
                        "usage": "profile nickname view",
                        "target": "src.cli.actions.profile.view_nickname",
                    },
                    "edit": {
                        "description": "닉네임 수정",
                        "usage": "profile nickname edit [new_nickname]",
                        "target": "src.cli.actions.profile.edit_nickname",
                    },
                },
            },
            "update_survey": {
                "description": "Survey 업데이트 (새 프로필 레코드 생성)",
                "usage": "profile update_survey",
                "target": "src.cli.actions.profile.update_survey",
            },
            "reset_surveys": {
                "description": "모든 Survey 기록 강제 삭제 (FK 무시, DEV용)",
                "usage": "profile reset_surveys",
                "target": "src.cli.actions.profile.reset_surveys",
            },
            "get-consent": {
                "description": "개인정보 동의 여부 확인",
                "usage": "profile get-consent",
                "target": "src.cli.actions.profile.get_consent",
            },
            "set-consent": {
                "description": "개인정보 동의 상태 변경",
                "usage": "profile set-consent [true|false]",
                "target": "src.cli.actions.profile.set_consent",
            },
            "get-ranking": {
                "description": "등급 및 랭킹 조회",
                "usage": "profile get-ranking",
                "target": "src.cli.actions.profile.get_ranking",
            },
        },
    },
    "agent": {
        "description": "Agent-based question generation and scoring",
        "usage": "agent [subcommand]",
        "target": "src.cli.actions.agent.agent_help",
        "sub_commands": {
            "generate-questions": {
                "description": "📝 문항 생성 (Tool 1-5 체인)",
                "usage": "agent generate-questions",
                "target": "src.cli.actions.agent.generate_questions",
            },
            "score-answer": {
                "description": "📋 답변 채점 (Tool 6)",
                "usage": "agent score-answer",
                "target": "src.cli.actions.agent.score_answer",
            },
            "batch-score": {
                "description": "📊 배치 채점 (복수 답변, 병렬)",
                "usage": "agent batch-score",
                "target": "src.cli.actions.agent.batch_score",
            },
            "tools": {
                "description": "🔧 개별 Tool 디버깅",
                "usage": "agent tools [subcommand]",
                "target": "src.cli.actions.agent.tools_help",
                "sub_commands": {
                    "t1": {
                        "description": "🔍 Get User Profile (Tool 1)",
                        "usage": "agent tools t1",
                        "target": "src.cli.actions.agent.t1_get_user_profile",
                    },
                    "t2": {
                        "description": "📚 Search Question Templates (Tool 2)",
                        "usage": "agent tools t2",
                        "target": "src.cli.actions.agent.t2_search_question_templates",
                    },
                    "t3": {
                        "description": "📊 Get Difficulty Keywords (Tool 3)",
                        "usage": "agent tools t3",
                        "target": "src.cli.actions.agent.t3_get_difficulty_keywords",
                    },
                    "t4": {
                        "description": "✅ Validate Question Quality (Tool 4)",
                        "usage": "agent tools t4",
                        "target": "src.cli.actions.agent.t4_validate_question_quality",
                    },
                    "t5": {
                        "description": "💾 Save Generated Question (Tool 5)",
                        "usage": "agent tools t5",
                        "target": "src.cli.actions.agent.t5_save_generated_question",
                    },
                    "t6": {
                        "description": "🎯 Score & Generate Explanation (Tool 6)",
                        "usage": "agent tools t6",
                        "target": "src.cli.actions.agent.t6_score_and_explain",
                    },
                },
            },
        },
    },
    "questions": {
        "description": "테스트 문항 생성, 채점, 저장",
        "usage": "questions [subcommand]",
        "target": "src.cli.actions.questions.questions_help",
        "sub_commands": {
            "session": {
                "description": "테스트 세션 관리",
                "usage": "questions session [subcommand]",
                "target": "src.cli.actions.questions.questions_help",
                "sub_commands": {
                    "resume": {
                        "description": "테스트 세션 재개",
                        "usage": "questions session resume",
                        "target": "src.cli.actions.questions.resume_session",
                    },
                    "status": {
                        "description": "세션 상태 변경 (일시중지/재개)",
                        "usage": "questions session status [pause|resume]",
                        "target": "src.cli.actions.questions.update_session_status",
                    },
                    "time_status": {
                        "description": "세션 시간 제한 확인",
                        "usage": "questions session time_status",
                        "target": "src.cli.actions.questions.check_time_status",
                    },
                },
            },
            "generate": {
                "description": "테스트 문항 생성 (Round 1)",
                "usage": "questions generate",
                "target": "src.cli.actions.questions.generate_questions",
                "sub_commands": {
                    "adaptive": {
                        "description": "적응형 문항 생성 (Round 2+)",
                        "usage": "questions generate adaptive",
                        "target": "src.cli.actions.questions.generate_adaptive_questions",
                    }
                },
            },
            "answer": {
                "description": "답변 처리",
                "usage": "questions answer [subcommand]",
                "target": "src.cli.actions.questions.questions_help",
                "sub_commands": {
                    "autosave": {
                        "description": "답변 자동 저장",
                        "usage": "questions answer autosave [question_id] [answer]",
                        "target": "src.cli.actions.questions.autosave_answer",
                    },
                    "score": {
                        "description": "단일 답변 채점",
                        "usage": "questions answer score [question_id] [answer]",
                        "target": "src.cli.actions.questions.score_answer",
                    },
                },
            },
            "score": {
                "description": "라운드 점수 계산 및 저장",
                "usage": "questions score",
                "target": "src.cli.actions.questions.calculate_round_score",
            },
            "complete": {
                "description": "테스트 세션 완료 처리",
                "usage": "questions complete",
                "target": "src.cli.actions.questions.complete_session",
            },
            "explanation": {
                "description": "해설 생성",
                "usage": "questions explanation [subcommand]",
                "target": "src.cli.actions.questions.questions_help",
                "sub_commands": {
                    "generate": {
                        "description": "해설 생성",
                        "usage": "questions explanation generate [question_id]",
                        "target": "src.cli.actions.questions.generate_explanation",
                    }
                },
            },
        },
    },
    "help": {
        "description": "사용 가능한 명령어 목록을 보여줍니다.",
        "usage": "help",
        "target": "src.cli.actions.system.help",
    },
    "clear": {
        "description": "터미널 화면을 정리합니다.",
        "usage": "clear",
        "target": "src.cli.actions.system.clear",
    },
    "exit": {
        "description": "CLI를 종료합니다.",
        "usage": "exit",
        "target": "src.cli.actions.system.exit_cli",
    },
}
