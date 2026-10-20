import { API_URL } from '../config/env';

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

type RequestOptions = RequestInit & { errorMessage: string };

export async function request<T>(
  path: string,
  { errorMessage, ...init }: RequestOptions,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);

  if (!response.ok) {
    throw new ApiError(errorMessage, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function buildUrl(path: string): string {
  return `${API_URL}${path}`;
}

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Произошла ошибка';
}
