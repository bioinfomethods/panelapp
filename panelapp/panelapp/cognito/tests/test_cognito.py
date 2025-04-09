##
## Copyright (c) 2016-2019 Genomics England Ltd.
##
## This file is part of PanelApp
## (see https://panelapp.genomicsengland.co.uk).
##
## Licensed to the Apache Software Foundation (ASF) under one
## or more contributor license agreements.  See the NOTICE file
## distributed with this work for additional information
## regarding copyright ownership.  The ASF licenses this file
## to you under the Apache License, Version 2.0 (the
## "License"); you may not use this file except in compliance
## with the License.  You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing,
## software distributed under the License is distributed on an
## "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
## KIND, either express or implied.  See the License for the
## specific language governing permissions and limitations
## under the License.
##
from string import (
    ascii_letters,
    ascii_lowercase,
    digits,
)
from textwrap import dedent

import faker
from django.http import SimpleCookie
from django.test import (
    SimpleTestCase,
    override_settings,
)
from jose import jwt

from panelapp.cognito.middleware import ALBAuthMiddleware

fake = faker.Faker()

MOCK_ENCODED_JWT_DATA = (
    "eyJ0eXAiOiJKV1QiLCJraWQiOiIzZTgxOTlkZC1lNjVkLTQzY2UtODAxMS01ZmQ3N2RjYWIxZTMiLCJhbGciOiJFUzI1NiIsImlzcyI6Imh0dH"
    "BzOi8vY29nbml0by1pZHAudXMtZWFzdC0xLmFtYXpvbmF3cy5jb20vdXMtZWFzdC0xXzFDM3Y3NFZGayIsImNsaWVudCI6IjJwdGlma282NHA5"
    "YmpyZXJyN3U0MmhubjF0Iiwic2lnbmVyIjoiYXJuOmF3czplbGFzdGljbG9hZGJhbGFuY2luZzp1cy1lYXN0LTE6MDI3MTk1NzEyMjM2OmxvYW"
    "RiYWxhbmNlci9hcHAvcGFuZWxhcHAtZGV2LWFsYi9iNjBiOWQxYzdlNDA5YzljIiwiZXhwIjoxNTYwNTI3MzUzfQ=="
    "."
    "eyJzdWIiOiI2ZDAxNjU1MS01M2FiLTRlMTgtODkxZC1hOTI0YmUyNDE0NDkiLCJpZGVudGl0aWVzIjoiW3tcInVzZXJJZFwiOlwiMTAwMzk5OT"
    "E0MDM3MTE5Mzk4OTkzXCIsXCJwcm92aWRlck5hbWVcIjpcIkdvb2dsZVwiLFwicHJvdmlkZXJUeXBlXCI6XCJHb29nbGVcIixcImlzc3Vlclwi"
    "Om51bGwsXCJwcmltYXJ5XCI6dHJ1ZSxcImRhdGVDcmVhdGVkXCI6MTU2MDUyMDUxMTg4Mn1dIiwiZW1haWxfdmVyaWZpZWQiOiJ0cnVlIiwibm"
    "FtZSI6Iktob2xpeCBUZWNoIiwiZ2l2ZW5fbmFtZSI6Iktob2xpeCIsImZhbWlseV9uYW1lIjoiVGVjaCIsImVtYWlsIjoia2hvbGl4LnRlY2hA"
    "Z21haWwuY29tIiwidXNlcm5hbWUiOiJHb29nbGVfMTAwMzk5OTE0MDM3MTE5Mzk4OTkzIiwiZXhwIjoxNTYwNTI3MzUzLCJpc3MiOiJodHRwcz"
    "ovL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tL3VzLWVhc3QtMV8xQzN2NzRWRmsifQ=="
    "."
    "ZzTZ2iBFs2RK2VQAEi_piExDtVGNh627ofRiUX-RAn8VZhWB-F_qIOv5sNzvhTTS4L_cu1ObmbZtKbHHptr3Bg=="
)
MOCK_PUBLIC_KEY = dedent(
    """\
    -----BEGIN PUBLIC KEY-----
    MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEL7UTKxPfCJ2joAN47z1NoYQlt8JP
    6Rw4OrJstuGGoBDrYOeEsMdSEwFgXfNav/m9O7E1FRLPpOdC7UnlnUXbmA==
    -----END PUBLIC KEY-----
    """
)
MOCK_META = {
    "HTTP_X_AMZN_OIDC_ACCESSTOKEN": fake.lexify(text="?" * 120),
    "HTTP_X_AMZN_OIDC_IDENTITY": f"${fake.uuid4()}",
    "HTTP_X_AMZN_OIDC_DATA": fake.lexify(text="?" * 120),
}
MOCK_META_HTTP_COOKIE = (
    f"csrftoken={fake.lexify(text='?' * 64, letters=ascii_letters+digits)}; "
    f"AWSELBAuthSessionCookie-0={fake.lexify(text='?' * 120, letters=ascii_letters + digits)}; "
    f"AWSELBAuthSessionCookie-0={fake.lexify(text='?' * 85, letters=ascii_letters + digits)}; "
    f"sessionid={fake.lexify(text='?' * 32, letters=ascii_lowercase + digits)}"
)


@override_settings(
    AWS_ELB_SESSION_COOKIE_PREFIX="AWSELBAuthSessionCookie",
    AWS_ELB_PUBLIC_KEY_ENDPOINT="https://public-keys.auth.elb.us-east-1.amazonaws.com/",
    AWS_JWT_SECTIONS=3,
    AWS_JWT_SIGNATURE_ALGORITHM="ES256",
    AWS_AMZN_OIDC_ACCESS_TOKEN="HTTP_X_AMZN_OIDC_ACCESSTOKEN",
    AWS_AMZN_OIDC_IDENTITY="HTTP_X_AMZN_OIDC_IDENTITY",
    AWS_AMZN_OIDC_DATA="HTTP_X_AMZN_OIDC_DATA",
)
class CognitoTestCase(SimpleTestCase):
    def test_has_amzn_oidc_headers(self):
        self.assertTrue(ALBAuthMiddleware.has_amzn_oidc_headers(MOCK_META))

    def test_verify_amzn_jwt_structure(self):
        self.assertTrue(
            ALBAuthMiddleware.verify_amzn_jwt_structure(MOCK_ENCODED_JWT_DATA)
        )

    def test_get_verified_jwt_claims(self):
        with self.assertRaisesMessage(Exception, "Signature has expired."):
            claims = ALBAuthMiddleware.get_verified_jwt_claims(
                MOCK_ENCODED_JWT_DATA, MOCK_PUBLIC_KEY
            )
            self.assertIsNone(claims)

    def test_get_alb_session_cookies(self):
        alb_session_cookies = ALBAuthMiddleware.get_alb_session_cookies(
            MOCK_META_HTTP_COOKIE
        )
        self.assertTrue(alb_session_cookies)

        cook = SimpleCookie()
        cook.load(MOCK_META_HTTP_COOKIE)
        morsel_keys = cook.get(alb_session_cookies[0]).keys()
        self.assertTrue("expires" in morsel_keys)

    def test_get_public_key(self):
        this = ALBAuthMiddleware(None)
        kid = jwt.get_unverified_headers(MOCK_ENCODED_JWT_DATA).get("kid")
        this.cache_holder[kid] = MOCK_PUBLIC_KEY
        self.assertEqual(this.get_public_key(MOCK_ENCODED_JWT_DATA), MOCK_PUBLIC_KEY)
