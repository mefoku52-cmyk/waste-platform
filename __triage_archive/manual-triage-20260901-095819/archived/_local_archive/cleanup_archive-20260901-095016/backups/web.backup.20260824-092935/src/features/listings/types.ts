import { BaseEntity } from '../../lib/types/common';

export interface Listing extends BaseEntity {
  title: string;
  description: string;
  amount: number;
  unit: string;
  price?: number;
  status: 'active' | 'completed' | 'cancelled';
  category_id: string;
  company_id: string;
}
