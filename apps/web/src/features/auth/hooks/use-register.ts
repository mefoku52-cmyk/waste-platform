'use client';

import { useMutation } from '@tanstack/react-query';
import { http } from '@/lib/api/http';

type RegisterBody = {
  email: string;
  password: string;
  name?: string;
  firstName?: string;
  lastName?: string;
};

function splitName(data: RegisterBody) {
  const raw = (data.name || '').trim();
  const parts = raw.split(/\s+/).filter(Boolean);
  const firstName = data.firstName || parts[0] || 'User';
  const lastName = data.lastName || (parts.slice(1).join(' ') || firstName);
  return {
    email: data.email,
    password: data.password,
    firstName,
    lastName,
  };
}

async function registerUser(data: RegisterBody) {
  return http.post('/users', splitName(data));
}

export function useRegister() {
  return useMutation({
    mutationFn: registerUser,
  });
}
