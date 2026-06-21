import { supabase } from "../lib/supabase";

export const signUp = async ({
  email,
  password,
}) => {
  return await supabase.auth.signUp({
    email,
    password,
  });
};

export const signIn = async ({
  email,
  password,
}) => {
  return await supabase.auth.signInWithPassword({
    email,
    password,
  });
};

export const signOut = async () => {
  return await supabase.auth.signOut();
};

export const signInWithGoogle = async () => {
  return await supabase.auth.signInWithOAuth({
    provider: "google",
  });
};

export const getSession = async () => {
  return await supabase.auth.getSession();
};