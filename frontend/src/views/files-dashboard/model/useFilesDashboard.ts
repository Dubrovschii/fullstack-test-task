import { useCallback, useEffect, useRef, useState } from 'react';
import { getErrorMessage } from '@/shared/api';
import { AlertItem, fetchAlerts } from '@/entities/alert';
import { FileItem, fetchFiles } from '@/entities/file';

const POLL_INTERVAL_MS = 2000;
const IN_PROGRESS = new Set(['uploaded', 'processing']);

export function useFilesDashboard() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const isFetching = useRef(false);

  // silent=true: фоновое обновление без спиннера и без сброса ошибки
  const reload = useCallback(async (silent = false) => {
    if (silent && isFetching.current) {
      return;
    }
    isFetching.current = true;

    if (!silent) {
      setIsLoading(true);
      setErrorMessage(null);
    }

    try {
      const [filesData, alertsData] = await Promise.all([
        fetchFiles(),
        fetchAlerts(),
      ]);

      setFiles(filesData);
      setAlerts(alertsData);
    } catch (error) {
      if (!silent) {
        setErrorMessage(getErrorMessage(error));
      }
    } finally {
      isFetching.current = false;
      if (!silent) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  // Пока есть необработанные файлы, опрашиваем бэкенд; когда все готовы, опрос останавливается.
  const hasPending = files.some((file) =>
    IN_PROGRESS.has(file.processing_status),
  );

  useEffect(() => {
    if (!hasPending) {
      return;
    }
    const timer = setInterval(() => void reload(true), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [hasPending, reload]);

  return { files, alerts, isLoading, errorMessage, setErrorMessage, reload };
}
