import { createClient } from '@supabase/supabase-js';
import { getFirebaseIdToken } from './auth';

const supabaseUrl = import.meta.env.PUBLIC_SUPABASE_URL ?? '';
const supabaseAnonKey = import.meta.env.PUBLIC_SUPABASE_ANON_KEY ?? '';

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  accessToken: getFirebaseIdToken,
});
