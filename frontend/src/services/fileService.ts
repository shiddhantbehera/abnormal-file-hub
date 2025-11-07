import axios, { AxiosError } from 'axios';
import { File as FileType, StorageStats, UploadResponse, FilterCriteria, PaginatedResponse, ErrorResponse } from '../types/file';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ErrorResponse>;
    if (axiosError.response?.data) {
      const { error: errorMsg, detail } = axiosError.response.data;
      if (detail) {
        return detail;
      }
      if (errorMsg) {
        return errorMsg;
      }
    }
    if (axiosError.message) {
      return axiosError.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export const fileService = {
  async uploadFile(file: File): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_URL}/files/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error('File upload error:', errorMessage);
      throw new Error(errorMessage);
    }
  },

  async getFiles(page: number = 1): Promise<PaginatedResponse<FileType>> {
    const response = await axios.get(`${API_URL}/files/`, {
      params: { page }
    });
    return response.data;
  },

  async searchFiles(filters: FilterCriteria): Promise<PaginatedResponse<FileType>> {
    try {
      const params = new URLSearchParams();
      if (filters.search) {
        params.append('search', filters.search);
      }
      if (filters.fileTypes && filters.fileTypes.length > 0) {
        params.append('file_types', filters.fileTypes.join(','));
      }
      if (filters.minSize !== undefined) {
        params.append('min_size', filters.minSize.toString());
      }
      if (filters.maxSize !== undefined) {
        params.append('max_size', filters.maxSize.toString());
      }
      if (filters.startDate) {
        params.append('start_date', filters.startDate);
      }
      if (filters.endDate) {
        params.append('end_date', filters.endDate);
      }
      if (filters.page) {
        params.append('page', filters.page.toString());
      }
      const response = await axios.get(`${API_URL}/files/search/`, { params });
      return response.data;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error('File search error:', errorMessage);
      throw new Error(errorMessage);
    }
  },

  async deleteFile(id: string): Promise<void> {
    await axios.delete(`${API_URL}/files/${id}/`);
  },

  async downloadFile(fileUrl: string, filename: string): Promise<void> {
    try {
      const response = await axios.get(fileUrl, {
        responseType: 'blob',
      });
      
      // Create a blob URL and trigger download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      throw new Error('Failed to download file');
    }
  },

  async getStorageStats(): Promise<StorageStats> {
    try {
      const response = await axios.get(`${API_URL}/files/storage_stats/`);
      return response.data;
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error('Storage stats error:', errorMessage);
      throw new Error(errorMessage);
    }
  },
}; 