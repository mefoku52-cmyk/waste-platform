import { BaseEntity } from '../../lib/types/common';

export interface Company extends BaseEntity {
  name: string;
  registration_number: string;
  tax_number?: string;
  address: string;
  city: string;
  zip_code: string;
  country: string;
  is_verified: boolean;
  subscriptionTier?: 'free' | 'pro' | 'ai' | string | null;
}
