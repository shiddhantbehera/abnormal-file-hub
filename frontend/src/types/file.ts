export interface File {
  id: string;
  original_filename: string;
  file_type: string;
  size: number;
  uploaded_at: string;
  file: string;
  is_duplicate?: boolean;
}

export interface UploadResponse extends File {
  storage_saved?: number;
}

export interface FilterCriteria {
  search?: string;
  fileTypes?: string[];
  minSize?: number;
  maxSize?: number;
  startDate?: string;
  endDate?: string;
  page?: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface StorageStats {
  total_files: number;
  unique_files: number;
  duplicate_references: number;
  storage_saved_bytes: number;
  storage_saved_readable: string;
} 

export interface ErrorResponse {
  error?: string;
  detail?: string;
}