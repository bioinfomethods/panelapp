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
from django.shortcuts import redirect
from django.urls import reverse_lazy

from .models import GenePanel


class PanelMixin:
    def get_object(self, *args, **kwargs):
        return GenePanel.objects.get(pk=self.kwargs["pk"]).active_panel

    def get_success_url(self):
        return reverse_lazy("panels:detail", kwargs={"pk": self.kwargs["pk"]})


class ActAndRedirectMixin:
    def get(self, *args, **kwargs):
        self.act()
        return redirect(self.get_success_url())
