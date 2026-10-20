import { Badge, Button } from 'react-bootstrap';
import { formatDate, formatSize } from '@/shared/lib';
import { getFileDownloadUrl, deleteFile } from '../api/fileApi';
import { getProcessingVariant } from '../lib/variants';
import type { FileItem } from '../model/types';

type FileRowProps = {
  file: FileItem;
  onDelete: (id: string) => void;
};
export function FileRow({ file, onDelete }: FileRowProps) {
  return (
    <tr>
      <td>
        <div className="fw-semibold">{file.title}</div>
        <div className="small text-secondary">{file.id}</div>
      </td>
      <td>{file.original_name}</td>
      <td>{file.mime_type}</td>
      <td>{formatSize(file.size)}</td>
      <td>
        <Badge bg={getProcessingVariant(file.processing_status)}>
          {file.processing_status}
        </Badge>
      </td>
      <td>
        <div className="d-flex flex-column gap-1">
          <Badge bg={file.requires_attention ? 'warning' : 'success'}>
            {file.scan_status ?? 'pending'}
          </Badge>
          <span className="small text-secondary">
            {file?.scan_details ?? 'Ожидает обработки'}
          </span>
        </div>
      </td>
      <td>{formatDate(file.created_at)}</td>
      <td className="text-nowrap">
        <Button
          as="a"
          href={getFileDownloadUrl(file.id)}
          variant="outline-primary"
          size="sm"
        >
          Скачать
        </Button>
      </td>
      <td className="text-nowrap">
        <Button
          type="button"
          variant="outline-danger"
          size="sm"
          onClick={() => onDelete(file.id)}
        >
          Удалить
        </Button>
      </td>
    </tr>
  );
}
