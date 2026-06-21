import { useMutation } from "@tanstack/react-query";

import {
  signIn,
  signUp,
  signOut,
} from "../services/auth.service";

export function useLogin() {
  return useMutation({
    mutationFn: signIn,
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: signUp,
  });
}

export function useLogout() {
  return useMutation({
    mutationFn: signOut,
  });
}