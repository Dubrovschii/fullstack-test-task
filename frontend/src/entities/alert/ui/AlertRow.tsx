import { Badge } from 'react-bootstrap';
import { formatDate } from '@/shared/lib';
import { getLevelVariant } from '../lib/variants';
import type { AlertItem } from '../model/types';

export function AlertRow({ alert }: { alert: AlertItem }) {
  return (
    <tr>
      <td>{alert.id}</td>
      <td className="small">{alert.file_id}</td>
      <td>
        <Badge bg={getLevelVariant(alert.level)}>{alert.level}</Badge>
      </td>
      <td>{alert.message}</td>
      <td>{formatDate(alert.created_at)}</td>
    </tr>
  );
}
