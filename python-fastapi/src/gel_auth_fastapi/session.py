#
# This source file is part of the Gel open source project.
#
# Copyright 2025-present Gel Data Inc. and the Gel authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import annotations
from typing import Annotated, Optional, Union

import gel
from fastapi import Cookie, Depends

ClientDep = Annotated[gel.AsyncIOClient, Depends(gel.create_async_client)]


class BaseSession:
    client: gel.AsyncIOClient

    def __init__(self, *, client: gel.AsyncIOClient):
        self.client = client

    async def is_authenticated(self) -> bool:
        return await self.client.query_required_single(  # type: ignore
            "select exists ext::auth::ClientTokenIdentity"
        )


class AuthenticatedSession(BaseSession):
    auth_token: str

    def __init__(self, *, client: gel.AsyncIOClient, auth_token: str):
        self.auth_token = auth_token
        self.client = client.with_globals(  # type: ignore
            {"ext::auth::ClientTokenIdentity": auth_token}
        )


class AnonymousSession(BaseSession):
    pass


Session = Union[AuthenticatedSession, AnonymousSession]


def extract_session(
    auth_token: Annotated[Optional[str], Cookie(alias="gel_auth_token")],
    client: ClientDep,
) -> Session:
    if auth_token:
        return AuthenticatedSession(client=client, auth_token=auth_token)
    else:
        return AnonymousSession(client=client)


SessionDep = Annotated[Session, Depends(extract_session)]
