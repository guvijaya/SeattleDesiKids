import {
  GoogleAuthProvider,
  onIdTokenChanged,
  signInWithPopup,
  signOut,
} from 'firebase/auth';
import type { User } from 'firebase/auth';
import { createAuthService, authErrorMessage, getUserIdToken } from './auth-service.mjs';
import {
  hasAdminClaim as includesAdminClaim,
  hasAuthenticatedRole as includesAuthenticatedRole,
} from './data-contracts.mjs';
import { getFirebaseAuth } from './firebase';

const service = createAuthService({
  getAuth: getFirebaseAuth,
  onIdTokenChanged,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
});

export const observeAuth = service.subscribe;
export const getCurrentUser = service.currentUser;
export const signInWithGoogle = service.signIn;
export const signOutUser = service.signOut;
export { authErrorMessage };

export async function getFirebaseIdToken(): Promise<string | null> {
  try {
    const user = await getCurrentUser();
    return await getUserIdToken(user);
  } catch {
    return null;
  }
}

export async function hasAuthenticatedRole(user: User | null): Promise<boolean> {
  if (!user) return false;
  try {
    const token = await user.getIdTokenResult();
    return includesAuthenticatedRole(token.claims);
  } catch {
    return false;
  }
}

export async function hasAdminClaim(user: User | null): Promise<boolean> {
  if (!user) return false;
  try {
    const token = await user.getIdTokenResult();
    return includesAdminClaim(token.claims);
  } catch {
    return false;
  }
}
