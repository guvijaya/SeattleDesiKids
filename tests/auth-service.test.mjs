import test from 'node:test';
import assert from 'node:assert/strict';
import { authErrorMessage, createAuthService, getUserIdToken } from '../src/lib/auth-service.mjs';
import {
  commentRecord,
  hasAdminClaim,
  hasAuthenticatedRole,
  isAuthenticated,
  progressRecord,
} from '../src/lib/data-contracts.mjs';

function createFixture(popupFailure = null) {
  let observer;
  const calls = { getAuth: 0, popup: 0, signOut: 0 };
  const auth = { currentUser: null };
  const user = {
    uid: 'firebase-user-123',
    displayName: 'A Reader',
    email: 'reader@example.test',
    getIdToken: async forceRefresh => `token-${forceRefresh ? 'refreshed' : 'cached'}`,
  };
  const service = createAuthService({
    getAuth: () => { calls.getAuth++; return auth; },
    onIdTokenChanged: (_auth, callback) => {
      observer = callback;
      return () => {};
    },
    GoogleAuthProvider: class {},
    signInWithPopup: async (_auth, provider) => {
      calls.popup++;
      calls.provider = provider;
      if (popupFailure) throw popupFailure;
      return { user };
    },
    signOut: async () => { calls.signOut++; },
  });
  return { service, calls, user, emit: nextUser => observer(nextUser) };
}

test('auth restoration waits for Firebase and notifies observers of user changes', async () => {
  const fixture = createFixture();
  const changes = [];
  const unsubscribe = fixture.service.subscribe(user => changes.push(user?.uid ?? null));
  let restored = false;
  const restoredUser = fixture.service.currentUser().then(user => {
    restored = true;
    return user;
  });

  await Promise.resolve();
  assert.equal(restored, false);
  fixture.emit(fixture.user);
  assert.equal((await restoredUser).uid, fixture.user.uid);
  fixture.emit(null);
  assert.deepEqual(changes, ['firebase-user-123', null]);
  unsubscribe();
  assert.equal(fixture.calls.getAuth, 1);
  assert.equal(isAuthenticated(fixture.user), true);
  assert.equal(isAuthenticated(null), false);
});

test('Google sign-in uses a popup and sign-out clears the Firebase session', async () => {
  const fixture = createFixture();
  const result = await fixture.service.signIn();
  assert.equal(result.user.uid, fixture.user.uid);
  assert.equal(fixture.calls.popup, 1);
  assert.ok(fixture.calls.provider);
  await fixture.service.signOut();
  assert.equal(fixture.calls.signOut, 1);
});

test('configuration errors are clear and popup failures distinguish cancellation and blocking', async () => {
  const service = createAuthService({
    getAuth: () => { throw new Error('Firebase Authentication is not configured.'); },
  });
  assert.throws(() => service.subscribe(() => {}), /Firebase Authentication is not configured/);
  assert.match(authErrorMessage({ code: 'auth/popup-closed-by-user' }), /cancelled/);
  assert.match(authErrorMessage({ code: 'auth/popup-blocked' }), /blocked the sign-in popup/);
  assert.match(authErrorMessage({ code: 'auth/unauthorized-domain' }), /hostname/);
  const blocked = createFixture({ code: 'auth/popup-blocked' });
  await assert.rejects(blocked.service.signIn(), error => authErrorMessage(error).includes('blocked the sign-in popup'));
});

test('progress and comments persist the Firebase UID and safe profile fallback', () => {
  const user = { uid: 'firebase-uid', displayName: 'Reader', email: 'reader@example.test' };
  assert.deepEqual(progressRecord(user, 'essay', 'english', 5, '2026-01-01T00:00:00.000Z'), {
    user_id: 'firebase-uid',
    slug: 'essay',
    lang: 'english',
    rating: 5,
    read_at: '2026-01-01T00:00:00.000Z',
  });
  assert.deepEqual(commentRecord(user, 'essay', '<script>'), {
    user_id: 'firebase-uid',
    slug: 'essay',
    display_name: 'Reader',
    body: '<script>',
  });
  assert.equal(commentRecord({ uid: 'other' }, 'essay', 'hi').display_name, 'Reader');
});

test('only an explicit true Firebase admin custom claim grants the moderation UI', () => {
  assert.equal(hasAuthenticatedRole({ role: 'authenticated' }), true);
  assert.equal(hasAuthenticatedRole({}), false);
  assert.equal(hasAdminClaim({ role: 'authenticated', admin: true }), true);
  assert.equal(hasAdminClaim({ role: 'authenticated', admin: 'true' }), false);
  assert.equal(hasAdminClaim({ admin: true }), false);
  assert.equal(hasAdminClaim({}), false);
});

test('the Supabase access-token callback reads refreshed Firebase ID tokens and returns null when signed out', async () => {
  let token = 'initial-token';
  const user = { getIdToken: async () => token };
  assert.equal(await getUserIdToken(user), 'initial-token');
  token = 'refreshed-token';
  assert.equal(await getUserIdToken(user), 'refreshed-token');
  assert.equal(await getUserIdToken(null), null);
});
