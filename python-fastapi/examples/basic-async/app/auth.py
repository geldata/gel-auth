from __future__ import annotations
from typing import Annotated

import json
import logging
import http

import fastapi
from fastapi import responses
from gel.auth import email_password as core
from gel_auth_fastapi import email_password as ext

from . import dependencies as deps
from .queries import create_user_async_edgeql as create_user_qry

logger = logging.getLogger("fast_jelly")
router = fastapi.APIRouter(tags=["Auth"])


@router.post(
    "/register",
    response_class=responses.RedirectResponse,
    status_code=http.HTTPStatus.SEE_OTHER,
)
async def register(
    sign_up_body: Annotated[ext.SignUpBody, fastapi.Form()],
    client: deps.CleanGelClient,
    auth: deps.EmailPassword,
    request: fastapi.Request,
    response: fastapi.Response,
):
    sign_up_response = await auth.handle_sign_up(
        sign_up_body,
        verify_url=str(request.url_for("verify")),
        response=response,
    )
    if not isinstance(sign_up_response, core.SignUpFailedResponse):
        user = await create_user_qry.create_user(
            client,
            name=sign_up_body.email,
            identity_id=sign_up_response.identity_id,
        )
        print(f"Created user: {json.dumps(user, default=str)}")

    match sign_up_response:
        case core.SignUpCompleteResponse():
            return "/"
        case core.SignUpVerificationRequiredResponse():
            return "/signin?incomplete=verification_required"
        case core.SignUpFailedResponse():
            logger.error("sign up failed: %s", sign_up_response)
            return "/signin?error=failure"
        case _:
            raise AssertionError("Invalid sign up response")


@router.post(
    "/authenticate",
    response_class=responses.RedirectResponse,
    status_code=http.HTTPStatus.SEE_OTHER,
)
async def authenticate(
    sign_in_body: Annotated[ext.SignInBody, fastapi.Form()],
    auth: deps.EmailPassword,
    response: fastapi.Response,
):
    sign_in_response = await auth.handle_sign_in(
        sign_in_body, response=response
    )
    match sign_in_response:
        case core.SignInCompleteResponse():
            return "/"
        case core.SignInVerificationRequiredResponse():
            return "/signin?incomplete=verification_required"
        case core.SignInFailedResponse():
            logger.error("sign in failed: %s", sign_in_response)
            return "/signin?error=failure"
        case _:
            raise AssertionError("Invalid sign in response")


@router.get(
    "/verify",
    response_class=responses.RedirectResponse,
    status_code=http.HTTPStatus.SEE_OTHER,
)
async def verify(
    verify_body: Annotated[ext.VerifyBody, fastapi.Query()],
    auth: deps.EmailPassword,
    verifier: deps.PKCEVerifier,
):
    verify_response = await auth.handle_verify_email(
        verify_body, verifier=verifier
    )

    match verify_response:
        case core.EmailVerificationCompleteResponse():
            return "/"
        case core.EmailVerificationMissingProofResponse():
            return "/signin?incomplete=verify"
        case core.EmailVerificationFailedResponse():
            logger.error("verify email failed: %s", verify_response)
            return "/signin?error=failure"
        case _:
            raise AssertionError("Invalid verify email response")


@router.post(
    "/send-password-reset",
    response_class=responses.RedirectResponse,
    status_code=http.HTTPStatus.SEE_OTHER,
)
async def send_password_reset(
    send_password_reset_body: Annotated[
        ext.SendPasswordResetBody, fastapi.Form()
    ],
    auth: deps.EmailPassword,
    request: fastapi.Request,
    response: fastapi.Response,
):
    send_password_reset_response = await auth.handle_send_password_reset(
        send_password_reset_body,
        reset_url=str(request.url_for("reset_password_page")),
        response=response,
    )
    match send_password_reset_response:
        case core.SendPasswordResetEmailCompleteResponse():
            return "/signin?incomplete=password_reset_sent"
        case core.SendPasswordResetEmailFailedResponse():
            logger.error(
                "send password reset failed: %s", send_password_reset_response
            )
            return "/signin?error=failure"
        case _:
            raise Exception("Invalid send password reset response")


@router.post(
    "/reset-password",
    response_class=responses.RedirectResponse,
    status_code=http.HTTPStatus.SEE_OTHER,
)
async def reset_password(
    reset_password_body: Annotated[ext.PasswordResetBody, fastapi.Form()],
    auth: deps.EmailPassword,
    verifier: deps.PKCEVerifier,
):
    reset_password_response = await auth.handle_reset_password(
        reset_password_body, verifier=verifier
    )
    match reset_password_response:
        case core.PasswordResetCompleteResponse():
            return "/"
        case core.PasswordResetMissingProofResponse():
            return "/signin?incomplete=reset_password"
        case core.PasswordResetFailedResponse():
            logger.error("reset password failed: %s", reset_password_response)
            return "/signin?error=failure"
        case _:
            raise Exception("Invalid reset password response")
