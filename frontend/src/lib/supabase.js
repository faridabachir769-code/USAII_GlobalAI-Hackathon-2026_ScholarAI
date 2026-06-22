import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

let supabase;

if (supabaseUrl && supabaseAnonKey) {
  supabase = createClient(supabaseUrl, supabaseAnonKey);
} else {
  supabase = {
    auth: {
      getSession: async () => ({ data: { session: null }, error: null }),
      onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
      signUp: async () => ({ error: new Error("Supabase not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.") }),
      signInWithPassword: async () => ({ error: new Error("Supabase not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.") }),
      signOut: async () => {},
      signInWithOAuth: async () => { throw new Error("Supabase OAuth not configured."); },
    },
  };
}

export { supabase };
