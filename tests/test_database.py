import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session


@pytest.mark.asyncio
async def test_get_session_yields_and_closes_an_async_session():
    session_generator = get_session()
    session = await anext(session_generator)

    assert isinstance(session, AsyncSession)
    assert session.is_active

    with pytest.raises(StopAsyncIteration):
        await anext(session_generator)
