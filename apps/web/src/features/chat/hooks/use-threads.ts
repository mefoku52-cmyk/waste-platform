import { useQuery } from '@tanstack/react-query';
import { chatApi } from '../api';

export const useThreads = () =>
  useQuery({
    queryKey: ['chat-threads'],
    queryFn: () => chatApi.listThreads(),
    refetchInterval: 5000,
  });

export const useThread = (id: string) =>
  useQuery({
    queryKey: ['chat-thread', id],
    queryFn: () => chatApi.getThread(id),
    enabled: !!id,
  });

export const useMessages = (threadId: string) =>
  useQuery({
    queryKey: ['chat-messages', threadId],
    queryFn: () => chatApi.listMessages(threadId),
    enabled: !!threadId,
    refetchInterval: 3000,
  });

export const useUnreadCount = () =>
  useQuery({
    queryKey: ['chat-unread'],
    queryFn: () => chatApi.unreadCount(),
    refetchInterval: 10000,
  });
