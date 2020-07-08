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
import ast
import json
import os

from django.http import SimpleCookie
from django.test import (
    SimpleTestCase,
    override_settings,
)
from jose import jwt

from panelapp.cognito.middleware import ALBAuthMiddleware


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
    def setUp(self) -> None:
        file_path = os.path.join(os.path.dirname(__file__), "fixtures.json")
        test_file = os.path.abspath(file_path)

        with open(test_file) as f:
            mock_data = json.load(f)
            self.mock_encoded_jwt_data = mock_data.get("mock_encoded_jwt_data")
            self.mock_public_key = mock_data.get("mock_public_key")
            self.mock_meta = ast.literal_eval(mock_data.get("mock_meta"))
            self.mock_meta_http_cookie = ast.literal_eval(
                mock_data.get("mock_meta_http_cookie")
            )

    def test_has_amzn_oidc_headers(self):
        self.assertTrue(ALBAuthMiddleware.has_amzn_oidc_headers(self.mock_meta))

    def test_verify_amzn_jwt_structure(self):
        self.assertTrue(
            ALBAuthMiddleware.verify_amzn_jwt_structure(self.mock_encoded_jwt_data)
        )

    def test_get_verified_jwt_claims(self):
        with self.assertRaisesMessage(Exception, "Signature has expired."):
            claims = ALBAuthMiddleware.get_verified_jwt_claims(
                self.mock_encoded_jwt_data, self.mock_public_key
            )
            self.assertIsNone(claims)

    def test_get_alb_session_cookies(self):
        http_cookie = self.mock_meta_http_cookie.get("HTTP_COOKIE")
        self.assertIsNotNone(http_cookie)
        alb_session_cookies = ALBAuthMiddleware.get_alb_session_cookies(http_cookie)
        self.assertTrue(alb_session_cookies)

        cook = SimpleCookie()
        cook.load(http_cookie)
        morsel_keys = cook.get(alb_session_cookies[0]).keys()
        self.assertTrue("expires" in morsel_keys)

    def test_get_public_key(self):
        this = ALBAuthMiddleware(None)
        kid = jwt.get_unverified_headers(self.mock_encoded_jwt_data).get("kid")
        this.cache_holder[kid] = self.mock_public_key
        self.assertEqual(
            this.get_public_key(self.mock_encoded_jwt_data), self.mock_public_key
        )
