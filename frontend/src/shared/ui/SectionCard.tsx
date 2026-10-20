import { Badge, Card, Spinner } from 'react-bootstrap';
import type { ReactNode } from 'react';

type Props = {
  title: string;
  count: number;
  isLoading: boolean;
  children: ReactNode;
  className?: string;
};

export function SectionCard({
  title,
  count,
  isLoading,
  children,
  className = '',
}: Props) {
  return (
    <Card className={`shadow-sm border-0 ${className}`}>
      <Card.Header className="bg-white border-0 pt-4 px-4">
        <div className="d-flex justify-content-between align-items-center">
          <h2 className="h5 mb-0">{title}</h2>
          <Badge bg="secondary">{count}</Badge>
        </div>
      </Card.Header>
      <Card.Body className="px-4 pb-4">
        {isLoading ? (
          <div className="d-flex justify-content-center py-5">
            <Spinner animation="border" />
          </div>
        ) : (
          <div className="table-responsive">{children}</div>
        )}
      </Card.Body>
    </Card>
  );
}
