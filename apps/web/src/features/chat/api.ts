import { http } from '../../lib/api/http';
import { ChatThread, ChatMessage } from './types';

export const chatApi = {
  listThreads: (params?: Record<string, any>) =>
    http.get<{ items: ChatThread[]; meta: any }>('/chat/threads', { ...params }),

  getThread: (id: string) =>
    http.get<{ data: ChatThread }>(`/chat/threads/${id}`),

  createThread: (data: {
    recipientUserId: string;
    recipientCompanyId?: string | null;
    initiatorCompanyId?: string | null;
    listingId?: string | null;
    subject: string;
  }) => http.post<{ data: ChatThread }>('/chat/threads', data),

  listMessages: (threadId: string, params?: Record<string, any>) =>
    http.get<{ items: ChatMessage[]; meta: any }>(
      `/chat/threads/${threadId}/messages`,
      { ...params },
    ),

  sendMessage: (threadId: string, body: string) =>
    http.post<{ data: ChatMessage }>(`/chat/threads/${threadId}/messages`, { body }),

  markRead: (threadId: string) =>
    http.post<{ marked: number }>(`/chat/threads/${threadId}/read`, {}),

  unreadCount: () =>
    http.get<{ unread: number }>('/chat/unread-count'),
};
