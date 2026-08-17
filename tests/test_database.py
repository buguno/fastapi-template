import pytest
from sqlalchemy.orm import Session

from app.database import get_session


def test_get_session_yields_and_closes_a_session():
    session_generator = get_session()
    session = next(session_generator)

    assert isinstance(session, Session)
    assert session.is_active

    with pytest.raises(StopIteration):
        next(session_generator)
