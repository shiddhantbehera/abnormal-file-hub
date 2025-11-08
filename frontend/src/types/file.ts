/**
 * Type definitions for file management system.
 */

/**
 * File model representing an uploaded file or duplicate reference.
 */
export interface File {
  id: string;
  original_filename: string;
  file_type: string;
  size: number;
  uploaded_at: string;
  file: string | null;
  file_hash: string;
  is_duplicate: boolean;
  storage_saved: number;
}

/**
 * Generic paginated response wrapper.
 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Response from file upload endpoint.
 */
export interface UploadResponse extends File {
  is_duplicate: boolean;
  storage_saved: number;
}

/**
 * Storage statistics from deduplication.
 */
export interface StorageStats {
  total_files: number;
  unique_files: number;
  duplicate_references: number;
  storage_saved_bytes: number;
  storage_saved_readable: string;
}

/**
 * Standard error response format.
 */
export interface ErrorResponse {
  error: string;
  detail?: string;
}

/**
 * File search and filter parameters.
 */
export interface FileFilters {
  search?: string;
  file_types?: string;
  min_size?: number;
  max_size?: number;
  start_date?: string;
  end_date?: string;
}
