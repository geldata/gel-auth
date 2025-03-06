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
from typing import Optional, TypeVar, Union

import uuid

import gel
from fastapi import security


class PKCEVerifier(security.APIKeyCookie):
    def __init__(self, name: str = "gel_verifier"):
        super().__init__(
            name=name,
            description="The cookie as the PKCE verifier",
            auto_error=False,
        )


class AuthToken(security.APIKeyCookie):
    def __init__(
        self, name: str = "gel_auth_token", *, auto_error: bool = False
    ):
        super().__init__(
            name=name,
            description="The cookie as the authentication token",
            auto_error=auto_error,
        )


C = TypeVar("C", bound=Union[gel.AsyncIOClient, gel.Client])


def get_client_with_auth_token(client: C, *, auth_token: Optional[str]) -> C:
    if auth_token:
        return client.with_globals({"ext::auth::client_token": auth_token})
    else:
        return client


async def get_identity_async(client: gel.AsyncIOClient) -> Optional[uuid.UUID]:
    return await client.query_single("select ext::auth::ClientTokenIdentity.id")


def get_identity(client: gel.Client) -> Optional[uuid.UUID]:
    return client.query_single("select ext::auth::ClientTokenIdentity.id")
