import { request } from '@/shared/api';
import type { AlertItem } from '../model/types';

export function fetchAlerts(): Promise<AlertItem[]> {
  return request<AlertItem[]>('/alerts', {
    cache: 'no-store',
    errorMessage: 'Не удалось загрузить данные',
  });
}
