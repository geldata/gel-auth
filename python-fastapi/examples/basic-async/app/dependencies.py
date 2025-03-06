from __future__ import annotations
from typing import Annotated

import fastapi
import gel
from gel.auth import email_password as core
from gel_auth_fastapi import email_password as ext, session


AUTH_COOKIE_NAME = "fastjelly-auth"
auth_token = session.AuthToken(AUTH_COOKIE_NAME)
AuthToken = Annotated[str | None, fastapi.Depends(auth_token)]
required_auth_token = session.AuthToken(AUTH_COOKIE_NAME, auto_error=True)
RequiredAuthToken = Annotated[str, fastapi.Depends(auth_token)]

VERIFIER_COOKIE_NAME = "fastjelly-verifier"
pkce_verifier = session.PKCEVerifier(VERIFIER_COOKIE_NAME)
PKCEVerifier = Annotated[str | None, fastapi.Depends(pkce_verifier)]


def gel_client(request: fastapi.Request) -> gel.AsyncIOClient:
    return request.app.state.client


CleanGelClient = Annotated[gel.AsyncIOClient, fastapi.Depends(gel_client)]


def gel_client_with_auth(
    client: CleanGelClient, token: AuthToken
) -> gel.AsyncIOClient:
    return session.get_client_with_auth_token(client, auth_token=token)


GelClient = Annotated[gel.AsyncIOClient, fastapi.Depends(gel_client_with_auth)]


async def email_password(
    request: fastapi.Request, client: CleanGelClient
) -> ext.EmailPassword:
    return ext.EmailPassword(
        await core.make_async(client),
        secure_cookie=request.base_url.is_secure,
        verifier_cookie_name=VERIFIER_COOKIE_NAME,
        auth_cookie_name=AUTH_COOKIE_NAME,
    )


EmailPassword = Annotated[ext.EmailPassword, fastapi.Depends(email_password)]
