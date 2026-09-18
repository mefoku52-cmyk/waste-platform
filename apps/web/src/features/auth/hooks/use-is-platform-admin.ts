import { useCurrentUser } from './use-current-user';

/**
 * Platform-admin signal.
 *
 * Server-authoritative: uses the `isPlatformAdmin` flag returned by `/auth/me`,
 * which the backend derives from `PLATFORM_ADMIN_EMAILS` / the reserved
 * `platform_admin` role.
 *
 * The flag must NOT be inferred from `roleCodes`: those come solely from
 * company memberships, where `admin` is a tenant (company) role. Treating it
 * as a platform role is a privilege escalation, so it is intentionally not
 * considered here.
 */
export const useIsPlatformAdmin = (): boolean => {
  const { data: me } = useCurrentUser();
  return Boolean(me?.isPlatformAdmin);
};