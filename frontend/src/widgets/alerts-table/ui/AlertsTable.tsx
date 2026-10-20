import { Table } from 'react-bootstrap';
import { AlertItem, AlertRow } from '@/entities/alert';
import { SectionCard } from '@/shared/ui';

type Props = {
  alerts: AlertItem[];
  isLoading: boolean;
};

export function AlertsTable({ alerts, isLoading }: Props) {
  return (
    <SectionCard title="Алерты" count={alerts.length} isLoading={isLoading}>
      <Table hover bordered className="align-middle mb-0">
        <thead className="table-light">
          <tr>
            <th>ID</th>
            <th>File ID</th>
            <th>Уровень</th>
            <th>Сообщение</th>
            <th>Создан</th>
          </tr>
        </thead>
        <tbody>
          {alerts.length === 0 ? (
            <tr>
              <td colSpan={5} className="text-center py-4 text-secondary">
                Алертов пока нет
              </td>
            </tr>
          ) : (
            alerts.map((alert) => <AlertRow key={alert.id} alert={alert} />)
          )}
        </tbody>
      </Table>
    </SectionCard>
  );
}
