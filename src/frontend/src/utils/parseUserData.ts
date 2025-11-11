// REQ: REQ-F-A1-2
/**
 * Parse user data from URL search parameters
 */

export interface UserData {
  knox_id: string
  name: string
  dept: string
  business_unit: string
  email: string
}

/**
 * Parse and validate user data from URL search parameters
 *
 * @param searchParams - URLSearchParams from callback URL
 * @returns UserData object or null if required parameters are missing
 */
export function parseUserData(searchParams: URLSearchParams): UserData | null {
  const knox_id = searchParams.get('knox_id')
  const name = searchParams.get('name')
  const dept = searchParams.get('dept')
  const business_unit = searchParams.get('business_unit')
  const email = searchParams.get('email')

  // Validate required parameters
  if (!knox_id || !name || !dept || !business_unit || !email) {
    return null
  }

  return {
    knox_id,
    name,
    dept,
    business_unit,
    email,
  }
}
