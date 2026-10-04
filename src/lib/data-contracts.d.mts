import type { User } from '@firebase/auth';

export function progressRecord(
  user: Pick<User, 'uid'>,
  slug: string,
  lang: string,
  rating: number,
  readAt: string,
): { user_id: string; slug: string; lang: string; rating: number; read_at: string };

export function isAuthenticated(user: User | null | undefined): boolean;

export function commentRecord(
  user: Pick<User, 'uid' | 'displayName' | 'email'>,
  slug: string,
  body: string,
): { user_id: string; slug: string; display_name: string; body: string };

export function hasAdminClaim(claims: Record<string, unknown> | undefined): boolean;
export function hasAuthenticatedRole(claims: Record<string, unknown> | undefined): boolean;
