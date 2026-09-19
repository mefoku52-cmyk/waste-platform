'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { http } from '@/lib/api/http';

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (threadId: string) =>
      http.post(`/chat/threads/${threadId}/read`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chat-threads'] });
      qc.invalidateQueries({ queryKey: ['chat-unread'] });
    },
  });
}
