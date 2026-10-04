import { getApp, getApps, initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: ['PUBLIC_FIREBASE_API_KEY', import.meta.env.PUBLIC_FIREBASE_API_KEY],
  authDomain: ['PUBLIC_FIREBASE_AUTH_DOMAIN', import.meta.env.PUBLIC_FIREBASE_AUTH_DOMAIN],
  projectId: ['PUBLIC_FIREBASE_PROJECT_ID', import.meta.env.PUBLIC_FIREBASE_PROJECT_ID],
  appId: ['PUBLIC_FIREBASE_APP_ID', import.meta.env.PUBLIC_FIREBASE_APP_ID],
};

export function getFirebaseAuth() {
  if (typeof window === 'undefined') {
    throw new Error('Firebase Authentication is available only in the browser.');
  }

  const missing = Object.values(firebaseConfig)
    .filter(([, value]) => !value)
    .map(([name]) => name);
  if (missing.length) {
    throw new Error(`Firebase Authentication is not configured. Set ${missing.join(', ')}.`);
  }

  const app = getApps().length
    ? getApp()
    : initializeApp(Object.fromEntries(Object.entries(firebaseConfig).map(([key, [, value]]) => [key, value])));
  return getAuth(app);
}
