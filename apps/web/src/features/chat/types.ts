export interface ChatThread {
  id: string;
  listingId: string | null;
  initiatorUserId: string;
  initiatorCompanyId: string | null;
  recipientUserId: string;
  recipientCompanyId: string | null;
  subject: string;
  status: string;
  lastMessageAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessage {
  id: string;
  threadId: string;
  senderUserId: string;
  senderCompanyId: string | null;
  body: string;
  readAt: string | null;
  createdAt: string;
}
