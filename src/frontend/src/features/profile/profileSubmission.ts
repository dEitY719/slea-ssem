import { LEVEL_MAPPING } from '../../constants/profileLevels'
import { profileService } from '../../services'
import { setCachedNickname } from '../../utils/nicknameCache'

const LAST_SURVEY_ID_KEY = 'lastSurveyId'
const LAST_SURVEY_LEVEL_KEY = 'lastSurveyLevel'

type BaseProfileInput = {
  level: number
  career?: number
  jobRole?: string
  duty?: string
  interests?: string
}

type CompleteSignupInput = BaseProfileInput & {
  nickname: string
}

const persistSurveyProgress = (level: number, surveyId: string) => {
  if (typeof window === 'undefined') {
    return
  }
  localStorage.setItem(LAST_SURVEY_ID_KEY, surveyId)
  localStorage.setItem(LAST_SURVEY_LEVEL_KEY, String(level))
}

export async function submitProfileSurvey(input: BaseProfileInput) {
  const payload = {
    level: LEVEL_MAPPING[input.level],
    career: input.career ?? 0,
    job_role: input.jobRole ?? '',
    duty: input.duty ?? '',
    interests: input.interests ? [input.interests] : [],
  }

  const response = await profileService.updateSurvey(payload)
  persistSurveyProgress(input.level, response.survey_id)

  return {
    surveyId: response.survey_id,
    level: payload.level,
  }
}

export async function completeProfileSignup(input: CompleteSignupInput) {
  await profileService.registerNickname(input.nickname)
  const surveyResult = await submitProfileSurvey(input)
  setCachedNickname(input.nickname)

  return {
    nickname: input.nickname,
    surveyId: surveyResult.surveyId,
  }
}
