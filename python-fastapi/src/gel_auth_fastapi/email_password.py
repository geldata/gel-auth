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
from typing import Optional

import datetime

import jwt
import pydantic
import fastapi
from gel.auth import email_password


class SignUpBody(pydantic.BaseModel):
    email: str
    password: str


class SignInBody(pydantic.BaseModel):
    email: str
    password: str


class VerifyBody(pydantic.BaseModel):
    verification_token: str


class SendPasswordResetBody(pydantic.BaseModel):
    email: str


class PasswordResetBody(pydantic.BaseModel):
    reset_token: str
    password: str


class EmailPassword:
    def __init__(
        self,
        client: email_password.AsyncEmailPassword,
        *,
        secure_cookie: bool = True,
        verifier_cookie_name: str = "gel_verifier",
        auth_cookie_name: str = "gel_auth_token",
    ):
        self._client = client
        self._secure_cookie = secure_cookie
        self._verifier_cookie_name = verifier_cookie_name
        self._auth_cookie_name = auth_cookie_name

    async def handle_sign_up(
        self,
        sign_up_body: SignUpBody,
        *,
        verify_url: str,
        response: fastapi.Response,
    ) -> email_password.SignUpResponse:
        sign_up_response = await self._client.sign_up(
            sign_up_body.email, sign_up_body.password, verify_url=verify_url
        )

        if isinstance(sign_up_response, email_password.SignUpCompleteResponse):
            self._set_auth_cookie(
                sign_up_response.token_data.auth_token, response
            )
        else:
            self._set_verifier_cookie(sign_up_response.verifier, response)

        return sign_up_response

    async def handle_sign_in(
        self,
        sign_in_body: SignInBody,
        *,
        response: fastapi.Response,
    ) -> email_password.SignInResponse:
        sign_in_response = await self._client.sign_in(
            sign_in_body.email, sign_in_body.password
        )

        if isinstance(sign_in_response, email_password.SignInCompleteResponse):
            self._set_auth_cookie(
                sign_in_response.token_data.auth_token, response
            )
        else:
            self._set_verifier_cookie(sign_in_response.verifier, response)

        return sign_in_response

    async def handle_verify_email(
        self,
        verify_body: VerifyBody,
        *,
        verifier: Optional[str] = None,
    ) -> email_password.EmailVerificationResponse:
        return await self._client.verify_email(
            verify_body.verification_token, verifier
        )

    async def handle_send_password_reset(
        self,
        send_password_reset_body: SendPasswordResetBody,
        *,
        reset_url: str,
        response: fastapi.Response,
    ) -> email_password.SendPasswordResetEmailResponse:
        send_password_reset_response = (
            await self._client.send_password_reset_email(
                send_password_reset_body.email, reset_url=reset_url
            )
        )

        self._set_verifier_cookie(
            send_password_reset_response.verifier, response
        )
        return send_password_reset_response

    async def handle_reset_password(
        self,
        password_reset_body: PasswordResetBody,
        *,
        verifier: Optional[str] = None,
    ) -> email_password.PasswordResetResponse:
        return await self._client.reset_password(
            reset_token=password_reset_body.reset_token,
            verifier=verifier,
            password=password_reset_body.password,
        )

    def _get_unchecked_exp(self, token: str) -> Optional[datetime.datetime]:
        jwt_payload = jwt.decode(token, options={"verify_signature": False})
        if "exp" not in jwt_payload:
            return None
        return datetime.datetime.fromtimestamp(
            jwt_payload["exp"], tz=datetime.timezone.utc
        )

    def _set_auth_cookie(self, token: str, response: fastapi.Response) -> None:
        exp = self._get_unchecked_exp(token)
        response.set_cookie(
            key=self._auth_cookie_name,
            value=token,
            httponly=True,
            secure=self._secure_cookie,
            samesite="lax",
            expires=exp,
        )

    def _set_verifier_cookie(
        self, verifier: str, response: fastapi.Response
    ) -> None:
        response.set_cookie(
            key=self._verifier_cookie_name,
            value=verifier,
            httponly=True,
            secure=self._secure_cookie,
            samesite="lax",
            expires=int(datetime.timedelta(days=7).total_seconds()),
        )
