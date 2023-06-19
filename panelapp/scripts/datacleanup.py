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
"""
Replace some users names (email addresses) and lock them out.

NEVER use in prod environment.

Usage: cat datacleanup.py | python manage.py shell

"""
import sys

from django.contrib.auth import get_user_model


def main():
    print("Disabling non-active/non-staff users", file=sys.stderr)
    User = get_user_model()
    all_users = 0
    passive_users = 0
    emails_changed = 0
    passwords_disabled = 0
    for user in User.objects.all():
        all_users += 1
        if user.is_staff and user.is_active:
            continue
        if user.username in ["TEST_Curator", "TEST_Reviewer"]:
            continue
        passive_users += 1
        # user.username = f'user-{user.id}'
        new_email = f"user-{user.id}@domain.invalid"  # RFC 6761
        if new_email != user.email:
            user.email = new_email
            emails_changed += 1
        if user.has_usable_password():
            user.set_unusable_password()
            passwords_disabled += 1
        user.save()
    print(f"Users passive/all: {passive_users}/{all_users}", file=sys.stderr)
    print(
        f"Emails/passwords changed: {emails_changed}/{passwords_disabled}",
        file=sys.stderr,
        flush=True,
    )


# No "if __name__ == '__main__':" here as this script is piped to manage.py shell
main()
