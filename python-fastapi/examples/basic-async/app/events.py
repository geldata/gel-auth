from __future__ import annotations

import datetime
from http import HTTPStatus

import gel
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import dependencies as deps
from .queries import (
    create_event_async_edgeql as create_event_qry,
)

router = APIRouter(tags=["API"])


class RequestData(BaseModel):
    name: str
    address: str
    schedule: datetime.datetime
    host_name: str


@router.post("/events", status_code=HTTPStatus.CREATED)
async def post_event(
    event: RequestData, client: deps.GelClient
) -> create_event_qry.CreateEventResult:
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
