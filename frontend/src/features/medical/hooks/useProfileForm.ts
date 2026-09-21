import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { User } from '../../../shared/types'
import { parseOptionalDecimal, parseOptionalInt } from '../../../shared/utils/numberParsing'

/** Limite acceptate pentru obiectivul caloric zilnic (kcal) — aceleași ca în backend (schemas.py). */
export const CALORIC_GOAL_MIN = 500
export const CALORIC_GOAL_MAX = 10000

type ProfileFormData = Pick<
  User,
  'email' | 'name' | 'sex' | 'activity_level' | 'diet_type'
> & { allergies: string; medical_conditions: string }

export type ProfilePayload = Partial<User> & { caloric_goal: number | null }

export type BuildPayloadResult = { payload: ProfilePayload; error?: undefined } | { payload?: undefined; error: string }

const toText = (n: number | null | undefined): string => (n != null && n > 0 ? String(n) : '')

/**
 * Starea formularului de profil, partajată între crearea și editarea profilului:
 * câmpuri text pentru valorile numerice + validare la trimitere.
 */
export function useProfileForm(initial: { user?: User; email?: string }) {
  const { t } = useTranslation()
  const { user } = initial

  const [formData, setFormData] = useState<ProfileFormData>({
    email: user?.email ?? initial.email ?? '',
    name: user?.name ?? '',
    sex: user?.sex ?? 'F',
    activity_level: user?.activity_level ?? 'moderate',
    diet_type: user?.diet_type ?? 'omnivore',
    allergies: user?.allergies ?? '',
    medical_conditions: user?.medical_conditions ?? '',
  })
  const [ageText, setAgeText] = useState(toText(user?.age))
  const [weightText, setWeightText] = useState(toText(user?.weight))
  const [heightText, setHeightText] = useState(toText(user?.height))
  const [caloricGoalText, setCaloricGoalText] = useState(toText(user?.caloric_goal))

  const update = (patch: Partial<ProfileFormData>) => setFormData((prev) => ({ ...prev, ...patch }))

  const buildPayload = (): BuildPayloadResult => {
    const age = parseOptionalInt(ageText)
    const weight = parseOptionalDecimal(weightText)
    const height = parseOptionalDecimal(heightText)

    if (age === undefined || age <= 0) return { error: t('profile.errors.ageRequired') }
    if (weight === undefined || weight <= 0) return { error: t('profile.errors.weightRequired') }
    if (height === undefined || height <= 0) return { error: t('profile.errors.heightRequired') }

    // Obiectivul caloric e opțional: câmp gol => null (șterge valoarea salvată)
    let caloricGoal: number | null = null
    if (caloricGoalText.trim() !== '') {
      const parsed = parseOptionalDecimal(caloricGoalText)
      if (parsed === undefined || parsed < CALORIC_GOAL_MIN || parsed > CALORIC_GOAL_MAX) {
        return {
          error: t('profile.errors.caloricGoalRange', { min: CALORIC_GOAL_MIN, max: CALORIC_GOAL_MAX }),
        }
      }
      caloricGoal = Math.round(parsed)
    }

    return { payload: { ...formData, age, weight, height, caloric_goal: caloricGoal } }
  }

  return {
    formData,
    update,
    ageText,
    setAgeText,
    weightText,
    setWeightText,
    heightText,
    setHeightText,
    caloricGoalText,
    setCaloricGoalText,
    buildPayload,
  }
}

export type ProfileForm = ReturnType<typeof useProfileForm>
