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
import re

from panels.exceptions import TSVIncorrectFormat


def remove_non_ascii(text, replacemenet=" "):
    return re.sub(r"[^\x00-\x7F]+", " ", text)


def clean_tsv_value(value, key):
    """
    Check tsv value for non-ascii characters and clean tabs, quotes and extra spaces
    :param value:
    :param key:
    :return:
    """

    try:
        value.encode("ascii")
    except UnicodeDecodeError:
        raise TSVIncorrectFormat(f"Line: {key} Invalid Character")

    return value.replace("\t", " ").replace('"', "").strip()
