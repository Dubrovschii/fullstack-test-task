import { buildUrl, request } from '@/shared/api';
import type { FileItem, UploadFilePayload } from '../model/types';

export function fetchFiles(): Promise<FileItem[]> {
  return request<FileItem[]>('/files', {
    cache: 'no-store',
    errorMessage: 'Не удалось загрузить данные',
  });
}

export function uploadFile({
  title,
  file,
}: UploadFilePayload): Promise<FileItem> {
  const formData = new FormData();
  formData.append('title', title);
  formData.append('file', file);

  return request<FileItem>('/files', {
    method: 'POST',
    body: formData,
    errorMessage: 'Не удалось загрузить файл',
  });
}

export function getFileDownloadUrl(id: string): string {
  return buildUrl(`/files/${id}/download`);
}
export function deleteFile(id: string): Promise<void> {
  return request<void>(`/files/${id}`, {
    method: 'DELETE',
    errorMessage: 'Не удалось удалить файл',
  });
}
