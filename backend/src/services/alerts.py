from typing import TYPE_CHECKING

from src.models import Alert

if TYPE_CHECKING:
    from src.repositories.alerts import AlertRepository


class AlertService:
    def __init__(self, *, alerts: "AlertRepository") -> None:
        self._alerts = alerts

    async def list_recent(self) -> list[Alert]:
        return await self._alerts.list_recent()
