'use client';

import { useQuery } from '@tanstack/react-query';
import { http } from '@/lib/api/http';

export const useThreads = () =>
  useQuery({
    queryKey: ['chat-threads'],
    queryFn: () => http.get<any>('/chat/threads'),
    refetchInterval: 5000,
  });

export const useThread = (id: string) =>
  useQuery({
    queryKey: ['chat-thread', id],
    queryFn: () => http.get<any>(`/chat/threads/${id}`),
    enabled: !!id,
  });

export const useMessages = (threadId: string) =>
  useQuery({
    queryKey: ['chat-messages', threadId],
    queryFn: () => http.get<any>(`/chat/threads/${threadId}/messages`),
    enabled: !!threadId,
    refetchInterval: 3000,
  });

export const useUnreadCount = () =>
  useQuery({
    queryKey: ['chat-unread'],
    queryFn: () => http.get<any>('/chat/unread-count'),
    refetchInterval: 10000,
  });
