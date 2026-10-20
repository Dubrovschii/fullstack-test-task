export function getProcessingVariant(status: string): string {
  if (status === 'failed') {
    return 'danger';
  }

  if (status === 'processing') {
    return 'warning';
  }

  if (status === 'processed') {
    return 'success';
  }

  return 'secondary';
}
