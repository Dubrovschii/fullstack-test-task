import { FormEvent, useState } from 'react';
import { getErrorMessage } from '@/shared/api';
import { uploadFile } from '@/entities/file';

type Options = {
  onUploaded: () => Promise<void> | void;
  onError: (message: string | null) => void;
};

export function useUploadFile({ onUploaded, onError }: Options) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [title, setTitle] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const open = () => setIsOpen(true);
  const close = () => setIsOpen(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!title.trim() || !selectedFile) {
      onError('Укажите название и выберите файл');
      return;
    }

    setIsSubmitting(true);
    onError(null);

    try {
      await uploadFile({ title: title.trim(), file: selectedFile });

      setIsOpen(false);
      setTitle('');
      setSelectedFile(null);
      await onUploaded();
    } catch (error) {
      onError(getErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return {
    isOpen,
    isSubmitting,
    title,
    setTitle,
    setSelectedFile,
    open,
    close,
    submit,
  };
}
