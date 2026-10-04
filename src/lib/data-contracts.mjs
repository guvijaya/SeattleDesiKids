export function progressRecord(user, slug, lang, rating, readAt) {
  return { user_id: user.uid, slug, lang, rating, read_at: readAt };
}

export function commentRecord(user, slug, body) {
  return {
    user_id: user.uid,
    slug,
    display_name: user.displayName || user.email || 'Reader',
    body,
  };
}

export function hasAuthenticatedRole(claims) {
  return claims?.role === 'authenticated';
}

export function hasAdminClaim(claims) {
  return hasAuthenticatedRole(claims) && claims?.admin === true;
}
