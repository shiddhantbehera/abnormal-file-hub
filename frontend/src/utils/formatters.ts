/**
 * Utility functions for formatting data.
 */

/**
 * Format bytes to human-readable size string.
 *
 * @param bytes - Number of bytes
 * @returns Formatted string (e.g., "1.50 MB")
 */
export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const value = bytes / Math.pow(1024, i);

  return `${value.toFixed(2)} ${sizes[i]}`;
};

/**
 * Format date to locale string.
 *
 * @param dateString - ISO date string
 * @returns Formatted date string
 */
export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString();
};
