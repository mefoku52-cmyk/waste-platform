'use client';

import { useMutation } from '@tanstack/react-query';
import { RegisterInput } from '../schemas';

async function registerUser(data: RegisterInput) {
  const res = await fetch('http://localhost:8001/api/v1/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || err.detail || 'Registrácia zlyhala');
  }

  return res.json();
}

export function useRegister() {
  return useMutation({
    mutationFn: registerUser,
  });
}
