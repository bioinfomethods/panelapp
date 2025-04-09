##
## Copyright (c) 2016-2020 Genomics England Ltd.
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

from django import forms

from panels.exceptions import (
    GeneDoesNotExist,
    GenesDoNotExist,
    ImportException,
    ImportValidationError,
    IncorrectGeneRating,
    IsSuperPanelException,
    RegionsDoNotExist,
    STRsDoNotExist,
    TSVIncorrectFormat,
    UserDoesNotExist,
    UsersDoNotExist,
)
from panels.models import (
    UploadedGeneList,
    UploadedPanelList,
    UploadedReviewsList,
)


class UploadGenesForm(forms.Form):
    gene_list = forms.FileField(label="Select a file", required=True)

    def process_file(self, **kwargs):
        gene_list = UploadedGeneList.objects.create(
            gene_list=self.cleaned_data["gene_list"]
        )
        gene_list.create_genes()


class UploadPanelsForm(forms.Form):
    panel_list = forms.FileField(label="Select a file", required=True)

    def process_file(self, **kwargs):
        message = None
        panel_list = UploadedPanelList.objects.create(
            panel_list=self.cleaned_data["panel_list"]
        )
        try:
            return panel_list.process_file(kwargs.pop("user"))
        except GeneDoesNotExist as e:
            message = (
                "Line: {} has a wrong gene, please check it and try again.".format(e)
            )
        except UserDoesNotExist as e:
            message = (
                "Line: {} has a wrong username, please check it and try again.".format(
                    e
                )
            )
        except UsersDoNotExist as e:
            message = (
                "Can't find following users: {}, please check it and try again.".format(
                    e
                )
            )
        except GenesDoNotExist as e:
            message = (
                "Can't find following genes: {}, please check it and try again.".format(
                    e
                )
            )
        except STRsDoNotExist as e:
            message = (
                "Can't find following STRs: {}, please check it and try again.".format(
                    e
                )
            )
        except RegionsDoNotExist as e:
            message = "Can't find following Regions: {}, please check it and try again.".format(
                e
            )
        except TSVIncorrectFormat as e:
            message = "Line: {} is not properly formatted, please check it and try again.".format(
                e
            )
        except ImportValidationError as err:
            message = err.invalid_rows  # ValidationError supports list of messages
        except ImportException as err:
            message = err.message
        except IsSuperPanelException as e:
            message = "One of the panels contains child panels"

        if message:
            raise forms.ValidationError(message)


class UploadReviewsForm(forms.Form):
    review_list = forms.FileField(label="Select a file", required=True)

    def process_file(self, **kwargs):
        message = None
        review_list = UploadedReviewsList.objects.create(
            reviews=self.cleaned_data["review_list"]
        )
        try:
            return review_list.process_file(kwargs.pop("user"))
        except GeneDoesNotExist as e:
            message = (
                "Line: {} has a wrong gene, please check it and try again.".format(e)
            )
        except UserDoesNotExist as e:
            message = (
                "Line: {} has a wrong username, please check it and try again.".format(
                    e
                )
            )
        except UsersDoNotExist as e:
            message = (
                "Can't find following users: {}, please check it and try again.".format(
                    e
                )
            )
        except GenesDoNotExist as e:
            message = (
                "Can't find following genes: {}, please check it and try again.".format(
                    e
                )
            )
        except ImportValidationError as err:
            message = err.invalid_rows  # ValidationError supports list of messages
        except ImportException as err:
            message = err.message
        except TSVIncorrectFormat as e:
            message = "Line: {} is not properly formatted, please check it and try again.".format(
                e
            )
        except IsSuperPanelException as e:
            message = "One of the panels contains child panels"
        except IncorrectGeneRating as e:
            message = e
        if message:
            raise forms.ValidationError(message)
