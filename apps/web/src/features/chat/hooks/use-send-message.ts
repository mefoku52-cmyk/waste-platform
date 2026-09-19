'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { http } from '@/lib/api/http';

export function useSendMessage(threadId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      http.post(`/chat/threads/${threadId}/messages`, { body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chat-messages', threadId] });
      qc.invalidateQueries({ queryKey: ['chat-threads'] });
      qc.invalidateQueries({ queryKey: ['chat-unread'] });
    },
  });
}
