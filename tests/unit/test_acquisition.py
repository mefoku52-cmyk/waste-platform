from datetime import datetime
from uuid import UUID

import pytest

from app.modules.analytics.application.acquisition import (
    AcquisitionEventInput,
    AcquisitionTrackingService,
)


class FakeAnalyticsRepository:
    def __init__(self):
        self.created = []

    async def create(self, entity):
        self.created.append(entity)
        return entity


@pytest.mark.asyncio
async def test_record_creates_acquisition_event_with_metadata():
    repository = FakeAnalyticsRepository()
    service = AcquisitionTrackingService(repository)

    event = await service.record(
        AcquisitionEventInput(
            event_type="landing_view",
            utm_source=" google ",
            utm_medium=" cpc ",
            utm_campaign=" autumn ",
            anonymous_id=" visitor-123 ",
            landing_page=" https://trc-cmep.sk/ ",
            referrer=" https://google.com/ ",
        )
    )

    assert len(repository.created) == 1
    assert repository.created[0] is event

    assert event.event_type == "landing_view"
    assert event.entity_type == "acquisition"
    assert isinstance(event.id, UUID)

    assert event.recorded_at.tzinfo is None
    assert isinstance(event.recorded_at, datetime)

    assert event.event_metadata == (
        '{"source":"acquisition","schema_version":1,'
        '"utm_source":"google","utm_medium":"cpc",'
        '"utm_campaign":"autumn","anonymous_id":"visitor-123",'
        '"landing_page":"https://trc-cmep.sk/",'
        '"referrer":"https://google.com/"}'
    )


@pytest.mark.asyncio
async def test_record_rejects_unsupported_event():
    repository = FakeAnalyticsRepository()
    service = AcquisitionTrackingService(repository)

    with pytest.raises(
        ValueError,
        match="Unsupported acquisition event: something_else",
    ):
        await service.record(
            AcquisitionEventInput(
                event_type="something_else",
            )
        )

    assert repository.created == []
