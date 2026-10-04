import type { User } from '@firebase/auth';

export function createAuthService(dependencies: {
  getAuth: () => unknown;
  onIdTokenChanged: (
    auth: unknown,
    onNext: (user: User | null) => void,
    onError?: (error: Error) => void,
  ) => () => void;
  GoogleAuthProvider: new () => unknown;
  signInWithPopup: (auth: unknown, provider: unknown) => Promise<{ user: User }>;
  signOut: (auth: unknown) => Promise<void>;
}): {
  subscribe: (listener: (user: User | null) => void) => () => boolean;
  currentUser: () => Promise<User | null>;
  signIn: () => Promise<{ user: User }>;
  signOut: () => Promise<void>;
};

export function authErrorMessage(error: unknown): string;
export function getUserIdToken(user: User | null): Promise<string | null>;
