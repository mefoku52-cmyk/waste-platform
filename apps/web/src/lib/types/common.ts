export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    total: number;
    page: number;
    last_page: number;
    per_page: number;
  };
}

export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at: string;
}
