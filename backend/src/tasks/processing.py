"""Celery glue for file processing: a thin task that assembles dependencies and runs the pipeline."""

from src.core.async_runner import run_async
from src.core.celery_app import celery_app
from src.core.database import get_session_factory
from src.file_storage import get_storage
from src.repositories.alerts import AlertRepository
from src.repositories.files import FileRepository
from src.services.processing.pipeline import ProcessingPipeline


async def _process(file_id: str) -> None:
    async with get_session_factory()() as session:
        pipeline = ProcessingPipeline(
            session=session,
            files=FileRepository(session),
            alerts=AlertRepository(session),
            storage=get_storage(),
        )
        await pipeline.run(file_id)


@celery_app.task(name="files.process")
def process_file(file_id: str) -> None:
    run_async(_process(file_id))


def enqueue_file_processing(file_id: str) -> None:
    process_file.delay(file_id)
