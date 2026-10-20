import { Table } from 'react-bootstrap';
import { FileItem, FileRow } from '@/entities/file';
import { deleteFile } from '@/entities/file/api/fileApi';
import { SectionCard } from '@/shared/ui';

type Props = {
  files: FileItem[];
  isLoading: boolean;
  onRefresh: () => Promise<void>;
};

export function FilesTable({ files, isLoading, onRefresh }: Props) {
  async function handleDeleteFile(id: string): Promise<void> {
    try {
      await deleteFile(id);
      await onRefresh();
    } catch (error) {
      console.error('Ошибка удаления файла:', error);
    }
  }

  return (
    <SectionCard
      title="Файлы"
      count={files.length}
      isLoading={isLoading}
      className="mb-4"
    >
      <Table hover bordered className="align-middle mb-0">
        <thead className="table-light">
          <tr>
            <th>Название</th>
            <th>Файл</th>
            <th>MIME</th>
            <th>Размер</th>
            <th>Статус</th>
            <th>Проверка</th>
            <th>Создан</th>
            <th>Скачать</th>
            <th>Удалить</th>
          </tr>
        </thead>

        <tbody>
          {files.length === 0 ? (
            <tr>
              <td colSpan={9} className="text-center py-4 text-secondary">
                Файлы пока не загружены
              </td>
            </tr>
          ) : (
            files.map((file) => (
              <FileRow key={file.id} file={file} onDelete={handleDeleteFile} />
            ))
          )}
        </tbody>
      </Table>
    </SectionCard>
  );
}
