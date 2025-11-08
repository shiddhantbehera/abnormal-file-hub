/**
 * File service for API interactions.
 * Handles file uploads, downloads, search, and storage statistics.
 */
import axios, { AxiosError } from 'axios';
import {
  File as FileType,
  PaginatedResponse,
  UploadResponse,
  StorageStats,
  ErrorResponse,
  FileFilters,
} from '../types/file';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

/**
 * Extract error message from various error types.
 */
const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ErrorResponse>;
    const data = axiosError.response?.data;

    if (data?.detail) return data.detail;
    if (data?.error) return data.error;
    if (axiosError.message) return axiosError.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'An unexpected error occurred';
};

/**
 * Build URL search params from filters object.
 */
const buildSearchParams = (filters: FileFilters): URLSearchParams => {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, value.toString());
    }
  });

  return params;
};

export const fileService = {
  /**
   * Upload a file to the server.
   */
  async uploadFile(file: File): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post<UploadResponse>(
        `${API_URL}/files/`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );

      return response.data;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error('File upload error:', errorMessage);
      throw new Error(errorMessage);
    }
  },

  /**
   * Search and filter files.
   */
  async searchFiles(
    filters: FileFilters
  ): Promise<PaginatedResponse<FileType>> {
    try {
      const params = buildSearchParams(filters);
      const response = await axios.get<PaginatedResponse<FileType>>(
        `${API_URL}/files/search/`,
        { params }
      );

      return response.data;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error('File search error:', errorMessage);
      throw new Error(errorMessage);
    }
  },

  /**
   * Delete a file by ID.
   */
  async deleteFile(id: string): Promise<void> {
    try {
      await axios.delete(`${API_URL}/files/${id}/`);
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error('File delete error:', errorMessage);
      throw error;
    }
  },

  /**
   * Download a file from URL.
   */
  async downloadFile(fileUrl: string, filename: string): Promise<void> {
    try {
      const response = await axios.get(fileUrl, {
        responseType: 'blob',
      });

      // Create blob URL and trigger download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');

      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      throw new Error('Failed to download file');
    }
  },

  /**
   * Get storage statistics.
   */
  async getStorageStats(): Promise<StorageStats> {
    try {
      const response = await axios.get<StorageStats>(
        `${API_URL}/files/storage_stats/`
      );

      return response.data;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error('Storage stats error:', errorMessage);
      throw new Error(errorMessage);
    }
  },
};
