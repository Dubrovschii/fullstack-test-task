export function getLevelVariant(level: string): string {
  if (level === 'critical') {
    return 'danger';
  }

  if (level === 'warning') {
    return 'warning';
  }

  return 'success';
}
