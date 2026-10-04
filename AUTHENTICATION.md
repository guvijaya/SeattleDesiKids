# Authentication setup and migration

The site uses Firebase Authentication for Google sign-in and keeps Supabase for
`reading_progress`, `essay_comments`, and `essay_views`. The Firebase ID token is
sent to Supabase with the supported third-party-auth `accessToken` callback. The
browser never receives a service-role key and does not use `supabase.auth`.

This change does not configure Firebase or Supabase, apply SQL to a live project,
or migrate production data. Complete the setup below before deploying the site.

## 1. Configure Firebase Google sign-in

1. Create or select the Firebase project that will own these users.
2. In **Project settings → General**, register a Web app and copy its web config.
   The site needs the API key, auth domain, project ID, and app ID only.
3. In **Authentication → Sign-in method**, enable **Google** and select a
   support email.
4. In **Authentication → Settings → Authorized domains**, add
   `guvijaya.github.io` and `localhost`. Domains are hostnames: do not include
   `https://`, a port, or `/SeattleDesiKids`. If local development uses
   `127.0.0.1`, authorize that hostname too. Newer Firebase projects may not
   authorize localhost automatically.
5. The app uses `signInWithPopup` rather than redirect sign-in, which avoids
   redirect storage restrictions on GitHub Pages. Users must allow popups for
   the site. Popup closure, blocking, missing config, and unauthorized-domain
   errors are shown in the UI.

## 2. Configure environment and Actions

Copy `.env.example` to the ignored `.env` file and set these exact values:

| Variable | Source |
| --- | --- |
| `PUBLIC_FIREBASE_API_KEY` | Firebase Web app config `apiKey` |
| `PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase Web app config `authDomain` |
| `PUBLIC_FIREBASE_PROJECT_ID` | Firebase project ID |
| `PUBLIC_FIREBASE_APP_ID` | Firebase Web app config `appId` |
| `PUBLIC_SUPABASE_URL` | Existing Supabase project URL |
| `PUBLIC_SUPABASE_ANON_KEY` | Existing Supabase anon/publishable key |

These Firebase values and the Supabase anon key are public client configuration,
not server credentials. Set the same names under repository **Settings →
Secrets and variables → Actions → Secrets** for the existing deployment build.
The deploy workflow still runs only on pushes to `main` and manual dispatch;
the pull-request workflow uses placeholder test values and never deploys.

Do not set a Supabase service-role key or Firebase service-account credential in
the site environment. `PUBLIC_ADMIN_USER_ID` is no longer used: admin rights
come from a signed Firebase custom claim and are independently enforced by RLS.

## What changed

- `src/lib/firebase.ts`, `src/lib/auth.ts`, and `src/lib/auth-service.mjs`
  initialize browser Firebase Auth once, restore/observe users and ID-token
  changes, and provide popup sign-in/sign-out with clear errors.
- `src/lib/supabase.ts` retains Supabase data access and supplies the current
  Firebase ID token; the auth-gated components and
  `src/pages/admin/comments.astro` now use Firebase UIDs/profile fields.
- `supabase-schema.sql` describes fresh installs and
  `supabase-firebase-migration.sql` upgrades existing UUID-backed data without
  dropping rows. `.env.example`, `src/env.d.ts`, and the Pages build workflow
  declare the public Firebase configuration.
- `tests/auth-service.test.mjs` covers mocked auth/token/data-identity rules;
  `.github/workflows/ci.yml` runs tests and a placeholder-config build without
  deploying.

## 3. Connect Firebase to Supabase

In the Supabase dashboard, open **Authentication → Third-Party Auth**, add
Firebase, and enter the exact Firebase project ID from step 1. This is required
for Supabase to validate Firebase-signed ID tokens. Supabase's supported
JavaScript integration uses `createClient(..., { accessToken })`; this project
returns the current user's `getIdToken()` value or `null`. No Supabase Auth
methods are used with that client.

The Firebase token must contain the custom claim `role: "authenticated"` for
Supabase to treat the request as authenticated. Firebase does not add that
claim by default. Without it, requests run as `anon`; public approved comments
and view counts remain readable, but progress, comment submission, and
moderation will be denied by RLS. The client shows an account-setup notice and
does not issue user-specific progress reads until the claim is present.

### Trusted custom-claim provisioning

Only a trusted environment using Firebase Admin SDK may assign claims. Never
accept a UID or role from the browser and never use a Firebase client SDK to
grant a role. Use one controlled claim-writer process, preserve claims already
assigned to each user, and keep its credentials outside this repository.

For accounts created in the future, a Cloud Functions Auth `onCreate` handler
can set the baseline role while retaining existing claims:

```js
const functions = require('firebase-functions/v1');
const { initializeApp } = require('firebase-admin/app');
const { getAuth } = require('firebase-admin/auth');

initializeApp();

exports.provisionSupabaseRole = functions.auth.user().onCreate(async user => {
  const auth = getAuth();
  const latest = await auth.getUser(user.uid);
  await auth.setCustomUserClaims(user.uid, {
    ...(latest.customClaims || {}),
    role: 'authenticated',
  });
});
```

Deploy this from a trusted backend project, not from the static site. For users
who already exist, run a trusted Admin SDK backfill over every `listUsers`
page, merging `{ role: 'authenticated' }` into each account's current
`customClaims`. Assign `admin: true` only to the specifically verified admin
Firebase UID, in the same trusted process, while preserving all other claims:

```js
const current = await auth.getUser(VERIFIED_ADMIN_UID);
await auth.setCustomUserClaims(VERIFIED_ADMIN_UID, {
  ...(current.customClaims || {}),
  role: 'authenticated',
  admin: true,
});
```

Do not choose the admin by email or grant `admin` to all accounts. Centralize
claim writes to avoid two concurrent trusted writers overwriting each other's
custom claims. Firebase ID tokens do not change retroactively: after the
backfill/trigger confirms completion, users must refresh their token (sign out
and back in is the simplest option). New users may need to do this once after
the on-create function completes; during that interval sign-in works, but
Supabase data writes do not.

Deploying Cloud Functions generally requires linking a billing account and
using the Blaze plan; function usage may incur charges. Google sign-in itself
does not require Identity Platform. Firebase blocking auth functions are a
separate Identity Platform feature and are not needed for this approach. Check
current Firebase pricing and trigger availability before enabling billing.
Alternatively, an operator can securely run the same Admin SDK provisioning
from a controlled backend/job for new users; it must be executed for every new
account and is not a browser operation.

## 4. Review and apply the database migration

Back up the Supabase database and review
[`supabase-firebase-migration.sql`](./supabase-firebase-migration.sql) before
running it in the SQL editor. Apply it before deploying Firebase-authenticated
code. It:

- drops the old foreign keys to `auth.users` and changes `user_id` from UUID to
  text, preserving each current UUID string and all rows;
- retains the existing progress uniqueness constraint and other table data;
  Firebase accounts have no `auth.users` row, so auth-user deletion no longer
  cascades into these tables and any cleanup must be handled by a trusted
  process;
- replaces `auth.uid()` policies with checks against the signed JWT `sub`;
- requires the authenticated role for writes and an explicit Firebase
  `admin: true` claim for pending-comment reads, approvals, and admin deletes;
- keeps public reads of approved comments and public view counts.

The fresh-install schema in `supabase-schema.sql` uses the same Firebase UID
text columns and RLS policies. Re-run neither file as a substitute for reviewing
your live policies: ensure there are no additional broad policies on either
table.

Firebase UIDs are not the old Supabase UUIDs. The migration intentionally does
not match users by email, discard records, or claim account continuity.
Unmapped historical progress remains stored under its original UUID string and
is not visible to a Firebase account. Approved comments remain public; pending
comments remain private to admins. If continuity is required, establish each
old-Supabase-UUID → Firebase-UID mapping through a trusted, verified account
linking process. Then use the optional commented transaction at the end of the
migration file. Check for `(user_id, slug)` collisions first and resolve them
deliberately; the unique constraint will reject colliding updates rather than
silently discard data. Never treat matching email addresses alone as proof of
identity.

## 5. Test and verify

The branch checks run:

```sh
npm ci
npm test
npm run build
```

The tests use mocked Firebase observers and popup calls plus synthetic UID,
claim, and token values. The CI build uses safe placeholder client settings; it
does not log in to Google or connect to a real Supabase project.

Branch checks performed during this change (Node `v22.23.3` locally):

- `npm ci` — passed.
- `npm test` — passed, 6 tests.
- `PUBLIC_FIREBASE_API_KEY=test-firebase-web-api-key PUBLIC_FIREBASE_AUTH_DOMAIN=project-id.firebaseapp.com PUBLIC_FIREBASE_PROJECT_ID=project-id PUBLIC_FIREBASE_APP_ID=1:123456789:web:abcdef PUBLIC_SUPABASE_URL=https://example.supabase.co PUBLIC_SUPABASE_ANON_KEY=test-supabase-anon-key-not-a-secret npm run build` — passed, 147 static pages generated.
- Static preview smoke check: `/SeattleDesiKids/` and `/SeattleDesiKids/essays/an-outing/english/` both returned HTTP 200 and emitted project-base asset links. A live browser/Google sign-in check was not possible without project setup.

No Firebase Auth emulator or live Supabase RLS integration was run for this
change. Before production rollout, use a staging Firebase project and staging
Supabase database with the migration applied:

1. Open `http://localhost:4321/SeattleDesiKids/` or the hosted
   `https://guvijaya.github.io/SeattleDesiKids/`; sign in with Google, reload,
   and confirm the restored avatar, locked-essay gate, read badge, and sign-out.
2. Confirm Firebase's authorized-domain and popup errors are shown by testing
   an unapproved hostname and a blocked/cancelled popup in a safe test browser.
3. After the trusted `role` claim is provisioned and refreshed, as user A mark
   an essay read, save a rating, and submit a comment. Confirm the stored
   `user_id` is A's Firebase UID. As user B, confirm A's progress is not
   returned and pending comments are not visible. As an anonymous visitor,
   confirm only approved comments and public view counts are readable.
4. As user B (without `admin: true`), use the moderation UI and attempt direct
   Supabase API reads of pending comments, an insert with `approved: true`, an
   update to `approved`, and deletion of another user's comment. All must be
   denied or return no rows. As the trusted admin account, confirm pending
   comments are visible and approval and deletion work.
5. Inspect browser network requests for Firebase ID-token authorization on
   Supabase data calls, and confirm no service-role key or Admin SDK credential
   is present in the built output.

## Rollback

Before applying SQL or deploying the new site, rollback is simply to stop and
revert the branch. If the schema migration has been applied but Firebase users
have not written data, restore the pre-migration database backup before
re-deploying the old Supabase-auth app. Once Firebase UIDs or mapped IDs have
been written, do not cast `user_id` back to UUID or deploy the old app against
the changed schema: some UIDs cannot be represented as UUIDs. Preserve a
backup/export and plan a forward-compatible recovery or carefully reviewed
data migration. No live configuration, SQL migration, or production data was
changed by this branch.

## References

- [Firebase Google sign-in for the web](https://firebase.google.com/docs/auth/web/google-signin)
- [Firebase redirect best practices](https://firebase.google.com/docs/auth/web/redirect-best-practices)
- [Firebase Auth troubleshooting](https://firebase.google.com/docs/auth/faq-and-troubleshooting)
- [Supabase Firebase third-party auth](https://supabase.com/docs/guides/auth/third-party/firebase-auth)
