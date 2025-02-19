from __future__ import annotations

import datetime
from http import HTTPStatus

import gel
from fastapi import APIRouter, HTTPException
from gel_auth_fastapi import SessionDep
from pydantic import BaseModel

from .queries import (
    create_event_async_edgeql as create_event_qry,
)

router = APIRouter()


class RequestData(BaseModel):
    name: str
    address: str
    schedule: datetime.datetime
    host_name: str


@router.post("/events", status_code=HTTPStatus.CREATED)
async def post_event(
    event: RequestData, session: SessionDep
) -> create_event_qry.CreateEventResult:
    client = session.client
    try:
        created_event = await create_event_qry.create_event(
            client,
            name=event.name,
            address=event.address,
            schedule=event.schedule,
            host_name=event.host_name,
        )
    except gel.errors.InvalidValueError as ex:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"error": str(ex)},
        )

    except gel.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"error": "Event '{event.name}' already exists"},
        )

    return created_event
