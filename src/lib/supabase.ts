import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.PUBLIC_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.PUBLIC_SUPABASE_ANON_KEY as string;

// Single shared client instance (module-level singleton)
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
