'use client';

import { Alert, Col, Container, Row } from 'react-bootstrap';
import { UploadFileModal, useUploadFile } from '@/features/upload-file';
import { AlertsTable } from '@/widgets/alerts-table';
import { DashboardHeader } from '@/widgets/dashboard-header';
import { FilesTable } from '@/widgets/files-table';
import { useFilesDashboard } from '../model/useFilesDashboard';

export function FilesDashboardView() {
  const { files, alerts, isLoading, errorMessage, setErrorMessage, reload } =
    useFilesDashboard();

  const upload = useUploadFile({
    onUploaded: reload,
    onError: setErrorMessage,
  });

  return (
    <Container fluid className="py-4 px-4 bg-light min-vh-100">
      <Row className="justify-content-center">
        <Col xxl={10} xl={11}>
          <DashboardHeader
            onRefresh={() => void reload()}
            onAddFile={upload.open}
          />

          {errorMessage ? (
            <Alert variant="danger" className="shadow-sm">
              {errorMessage}
            </Alert>
          ) : null}

          <FilesTable
            files={files}
            isLoading={isLoading}
            onRefresh={() => reload()}
          />
          <AlertsTable alerts={alerts} isLoading={isLoading} />
        </Col>
      </Row>

      <UploadFileModal
        show={upload.isOpen}
        isSubmitting={upload.isSubmitting}
        title={upload.title}
        onTitleChange={upload.setTitle}
        onFileChange={upload.setSelectedFile}
        onClose={upload.close}
        onSubmit={upload.submit}
      />
    </Container>
  );
}
