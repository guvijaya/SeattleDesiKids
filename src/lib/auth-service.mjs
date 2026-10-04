export function createAuthService({ getAuth, onIdTokenChanged, GoogleAuthProvider, signInWithPopup, signOut }) {
  let auth;
  let started = false;
  let user;
  let resolveReady;
  let ready;
  const listeners = new Set();

  function notify(nextUser) {
    for (const listener of listeners) {
      try {
        listener(nextUser);
      } catch (error) {
        queueMicrotask(() => { throw error; });
      }
    }
  }

  function start() {
    if (started) return;
    auth = getAuth();
    started = true;
    ready = new Promise(resolve => { resolveReady = resolve; });
    onIdTokenChanged(auth, nextUser => {
      user = nextUser;
      resolveReady(user);
      notify(user);
    }, () => {
      user = null;
      resolveReady(null);
      notify(null);
    });
  }

  return {
    subscribe(listener) {
      start();
      listeners.add(listener);
      if (user !== undefined) listener(user);
      return () => listeners.delete(listener);
    },

    async currentUser() {
      start();
      return user === undefined ? ready : user;
    },

    signIn() {
      start();
      return signInWithPopup(auth, new GoogleAuthProvider());
    },

    async signOut() {
      start();
      await signOut(auth);
    },
  };
}

export async function getUserIdToken(user) {
  return user ? user.getIdToken() : null;
}

export function authErrorMessage(error) {
  const code = error && typeof error === 'object' && 'code' in error ? error.code : '';
  if (code === 'auth/popup-blocked') return 'Your browser blocked the sign-in popup. Allow popups for this site and try again.';
  if (code === 'auth/popup-closed-by-user' || code === 'auth/cancelled-popup-request') return 'Google sign-in was cancelled. Try again when you are ready.';
  if (code === 'auth/unauthorized-domain') return 'This site is not authorized for Firebase sign-in. Add its hostname in Firebase Authentication settings.';
  if (code === 'auth/operation-not-allowed') return 'Google sign-in is not enabled for this Firebase project.';
  if (error instanceof Error) return error.message;
  return 'Could not sign in with Google. Please try again.';
}
