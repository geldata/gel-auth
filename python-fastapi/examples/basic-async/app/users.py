from __future__ import annotations
from typing import Annotated

import dataclasses
import datetime
import uuid
from http import HTTPStatus

import fastapi
import gel
import pydantic

from .queries import (
    get_user_by_name_async_edgeql as get_user_by_name_qry,
    get_users_async_edgeql as get_users_qry,
    create_user_async_edgeql as create_user_qry,
    update_user_async_edgeql as update_user_qry,
    delete_user_async_edgeql as delete_user_qry,
    get_current_user_async_edgeql as get_current_user_qry,
)
from . import dependencies as deps

router = fastapi.APIRouter(tags=["API"])


class RequestData(pydantic.BaseModel):
    name: str


@dataclasses.dataclass(kw_only=True)
class User:
    created_at: datetime.datetime
    id: uuid.UUID
    name: str

    @classmethod
    def from_db(
        cls,
        user: (
            get_users_qry.GetUsersResult
            | get_user_by_name_qry.GetUserByNameResult
            | create_user_qry.CreateUserResult
            | update_user_qry.UpdateUserResult
            | delete_user_qry.DeleteUserResult
            | get_current_user_qry.GetCurrentUserResult
        ),
    ):
        return User(
            id=user.id,
            name=user.name,
            created_at=user.created_at,
        )


async def current_user(client: deps.GelClient) -> User | None:
    user = await get_current_user_qry.get_current_user(client)
    if user:
        return User.from_db(user)


CurrentUser = Annotated[User | None, fastapi.Depends(current_user)]


type UserResponse = list[User] | User


@router.get("/users")
async def get_users(
    client: deps.GelClient,
    name: str = fastapi.Query(default=None, max_length=50),
) -> UserResponse:
    if not name:
        users = await get_users_qry.get_users(client)
        return list(map(User.from_db, users))
    else:
        user = await get_user_by_name_qry.get_user_by_name(client, name=name)
        if not user:
            raise fastapi.HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail={"error": f"Username '{name}' does not exist."},
            )
        return User.from_db(user)


@router.post("/users", status_code=HTTPStatus.CREATED)
async def post_user(user: RequestData, client: deps.CleanGelClient) -> User:
    try:
        created_user = await create_user_qry.create_user(client, name=user.name)
    except gel.errors.ConstraintViolationError:
        raise fastapi.HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"error": f"User '{user.name}' already exists."},
        )

    return User.from_db(created_user)


@router.put("/users")
async def put_user(
    user: RequestData, current_name: str, client: deps.GelClient
) -> User:
    try:
        updated_user = await update_user_qry.update_user(
            client,
            new_name=user.name,
            current_name=current_name,
        )
    except gel.errors.ConstraintViolationError:
        raise fastapi.HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"error": f"User '{user.name}' already exists."},
        )

    if not updated_user:
        raise fastapi.HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail={"error": f"User '{current_name}' does not exist."},
        )

    return User(
        created_at=updated_user.created_at,
        id=updated_user.id,
        name=updated_user.name,
    )


@router.delete("/users", status_code=HTTPStatus.NO_CONTENT)
async def delete_user(name: str, client: deps.GelClient):
    try:
        deleted_user = await delete_user_qry.delete_user(client, name=name)
    except gel.errors.ConstraintViolationError:
        raise fastapi.HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"error": "User attached to an event. Cannot delete."},
        )

    if not deleted_user:
        raise fastapi.HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail={"error": f"User '{name}' does not exist."},
        )

    return fastapi.Response(status_code=HTTPStatus.NO_CONTENT)
