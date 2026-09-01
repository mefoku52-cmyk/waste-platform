import { useQuery } from '@tanstack/react-query';
import { inquiriesApi } from '../api';

export const useReceivedInquiries = () =>
  useQuery({
    queryKey: ['inquiries', 'received'],
    queryFn: () => inquiriesApi.getReceived(),
  });

export const useSentInquiries = () =>
  useQuery({
    queryKey: ['inquiries', 'sent'],
    queryFn: () => inquiriesApi.getSent(),
  });
