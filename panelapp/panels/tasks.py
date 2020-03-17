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
import logging
import requests
import csv
import tempfile
import os
from requests.exceptions import HTTPError
from django.conf import settings
from django.template.loader import render_to_string
from django.template.defaultfilters import pluralize
from celery import shared_task
from django.db import transaction
from panelapp.tasks import send_email
from panelapp.tasks import send_mass_email
from django.core.mail import EmailMessage
from panels.exceptions import GeneDoesNotExist
from panels.exceptions import GenesDoNotExist
from panels.exceptions import UserDoesNotExist
from panels.exceptions import TSVIncorrectFormat
from panels.exceptions import IncorrectGeneRating
from panels.exceptions import IsSuperPanelException


@shared_task
def increment_panel_async(panel_pk, user_pk=None, version_comment=None, major=False, update_stats=True, include_superpanels=False):
    from accounts.models import User
    from panels.models import GenePanelSnapshot

    if user_pk:
        gps = GenePanelSnapshot.objects.get(pk=panel_pk).increment_version(
            major=major, user=User.objects.get(pk=user_pk), comment=version_comment,
            include_superpanels=include_superpanels
        )
    else:
        gps = GenePanelSnapshot.objects.get(pk=panel_pk).increment_version(
            major=major, comment=version_comment, include_superpanels=include_superpanels
        )

    if update_stats:
        gps._update_saved_stats()


@shared_task
def import_panel(user_pk, upload_pk):
    """Process large panel lists in the background

    Sends an email to the user once the panel has been imported
    """

    from accounts.models import User
    from panels.models import UploadedPanelList

    user = User.objects.get(pk=user_pk)
    panel_list = UploadedPanelList.objects.get(pk=upload_pk)

    error = True
    try:
        panel_list.process_file(user, background=True)
        message = "Panel list successfully imported"
        error = False
    except GeneDoesNotExist as line:
        message = "Line: {} has a wrong gene, please check it and try again.".format(
            line
        )
    except UserDoesNotExist as line:
        message = "Line: {} has a wrong username, please check it and try again.".format(
            line
        )
    except TSVIncorrectFormat as line:
        message = "Line: {} is not properly formatted, please check it and try again.".format(
            line
        )
    except GenesDoNotExist as genes_error:
        message = (
            "Following lines have genes which do not exist in the"
            "database, please check it and try again:\n\n{}".format(genes_error)
        )
    except IsSuperPanelException as e:
        message = "One of the panels contains child panels"
    except Exception as e:
        print(e)
        message = "Unhandled error occured, please forward it to the dev team:\n\n{}".format(
            e
        )

    panel_list.import_log = message
    panel_list.save()

    send_email.delay(
        user.email,
        "Error importing panel list" if error else "Success importing panel list",
        "{}\n\n----\nPanelApp".format(message),
    )


@shared_task
def import_reviews(user_pk, review_pk):
    """Process large panel reviews in the background

    Sends an email to the user once the panel has been imported
    """

    from accounts.models import User
    from panels.models import UploadedReviewsList

    user = User.objects.get(pk=user_pk)
    panel_list = UploadedReviewsList.objects.get(pk=review_pk)

    error = True
    try:
        panel_list.process_file(user, background=True)
        message = "Reviews have been successfully imported"
        error = False
    except GeneDoesNotExist as line:
        message = "Line: {} has a wrong gene, please check it and try again.".format(
            line
        )
    except UserDoesNotExist as line:
        message = "Line: {} has a wrong username, please check it and try again.".format(
            line
        )
    except TSVIncorrectFormat as line:
        message = "Line: {} is not properly formatted, please check it and try again.".format(
            line
        )
    except IncorrectGeneRating as e:
        message = e
    except GenesDoNotExist as genes_error:
        message = (
            "Following lines have genes which do not exist in the"
            "database, please check it and try again:\n\n{}".format(genes_error)
        )
    except IsSuperPanelException as e:
        message = "One of the panels contains child panels"
    except Exception as e:
        print(e)
        message = "There was an error importing reviews"

    panel_list.import_log = message
    panel_list.save()

    send_email.delay(
        user.email,
        "Error importing reviews list" if error else "Success importing reviews list",
        "{}\n\n----\nPanelApp".format(message),
    )


@shared_task
def email_panel_promoted(panel_pk):
    """Emails everyone who contributed to the panel about the new major version"""

    from panels.models import GenePanel

    active_panel = GenePanel.objects.get(pk=panel_pk).active_panel

    subject = "A panel you reviewed has been promoted"
    messages = []

    for contributor in active_panel.contributors:
        if contributor.email:  # check if we have an email in the database
            text = render_to_string(
                "panels/emails/panel_promoted.txt",
                {
                    "first_name": contributor.first_name,
                    "panel_name": active_panel.panel,
                    "panel_id": panel_pk,
                    "settings": settings,
                },
            )

            message = (subject, text, settings.DEFAULT_FROM_EMAIL, [contributor.email])
            messages.append(message)

    logging.debug(
        "Number of emails to send after panel promotion: {}".format(len(messages))
    )
    if messages:
        send_mass_email(tuple(messages))


@shared_task
def background_copy_reviews(user_pk, gene_symbols, panel_from_pk, panel_to_pk):
    from accounts.models import User
    from panels.models import GenePanelSnapshot

    user = User.objects.get(pk=user_pk)

    panels = GenePanelSnapshot.objects.get_active(all=True, internal=True).filter(
        pk__in=[panel_from_pk, panel_to_pk]
    )
    if panels[0].pk == panel_from_pk:
        panel_from = panels[0]
        panel_to = panels[1]
    else:
        panel_to = panels[0]
        panel_from = panels[1]

    try:
        total_count = 0
        with transaction.atomic():
            panel_to = panel_to.increment_version()
            total_count = panel_to.copy_gene_reviews_from(gene_symbols, panel_from)
        subject = "Success copying the reviews"
        message = "{} review{} copied".format(total_count, pluralize(total_count))
    except Exception as e:
        print(e)
        subject = "Error copying reviews"
        message = "There was an error copying the reviews"

    send_email.delay(user.email, subject, "{}\n\n----\nPanelApp".format(message))


def retrieve_omim_moi(omim):
    """
    OMIM API CALL
    Retrieve MOIs for a specific gene from OMIM and return them as a set to check against.
    param: str
        OMIM number
    """
    url = 'https://api.omim.org/api/entry?mimNumber={}&include=geneMap&include=externalLinks&format=json&apiKey={}'.format(omim, settings.OMIM_API_KEY)
    moi = set()
    try:
        res = requests.get(url)
        res.raise_for_status()
        omim_data = res.json()
        for omim_entry in omim_data['omim']['entryList']:
            for phenotype in omim_entry['entry'].get('geneMap', {}).get('phenotypeMapList', []):
                if phenotype['phenotypeMap']['phenotypeInheritance']:
                    for pheno in phenotype['phenotypeMap']['phenotypeInheritance'].split(';'):
                        moi.add(pheno)
    except HTTPError:
        logging.error('HTTP error on request to OMIM.')
    except ValueError:
        logging.error('OMIM response not in JSON format.')
    except Exception as e:
        logging.error(e)

    return moi


moi_mapping = {
    'MONOALLELIC,': ['Autosomal dominant', 'dominant', 'AD', 'DOMINANT'],
    'BIALLELIC,': ['Autosomal recessive', 'recessive', 'AR', 'RECESSIVE'],
    'BOTH': ['Autosomal recessive', 'Autosomal dominant', 'recessive', 'dominant', 'AR/AD', 'AD/AR',
             'DOMINANT/RECESSIVE', 'RECESSIVE/DOMINANT'],
    'X-LINKED:': ['X-linked recessive', 'XLR', 'X-linked dominant', 'x-linked over-dominance',
                  'X-LINKED', 'X-linked', 'XLD', 'XL'],
    'MITOCHONDRIAL': ['Mitochondrial']
}


@shared_task
def moi_check():
    """
    AUTOMATED MOI CHECK
    Does a daily systematic check of all MOIs for current Green genes on Panels V1+.
    Checking for consistency with chromosome, between panels and with OMIM database.
    """
    from panels.models.genepanelentrysnapshot import GenePanelEntrySnapshot
    from panels.models.genepanel import GenePanel

    green_genes = GenePanelEntrySnapshot.objects.get_active().filter(saved_gel_status__gte=3,
                                                                     panel__major_version__gte=1,
                                                                     panel__panel__status__in=[GenePanel.STATUS.public,
                                                                                               GenePanel.STATUS.promoted]).iterator()
    incorrect_moi = []
    gene_check = {}
    for gene in green_genes:
        moi = gene.moi
        if not moi or moi == "Unknown":
            msg = 'Green gene {} with {} moi on panel {}'.format(gene.name, gene.moi, gene.panel)
            incorrect_moi.append([msg, gene.name, gene.moi, gene.panel, gene.panel.pk])
            continue
        chromosome = None
        gene_dict = gene.gene.get('ensembl_genes')
        if gene_dict:
            for entry in gene_dict:
                for number in gene_dict[entry]:
                    if gene_dict[entry][number]['location']:
                        chromosome = gene_dict[entry][number]['location'].split(':')[0]

        if moi == 'Other - please specifiy in evaluation comments' and chromosome != 'Y':
            msg = 'Green gene {} with {} moi on panel {}'.format(gene.name, gene.moi, gene.panel)
            incorrect_moi.append([msg, gene.name, gene.moi, gene.panel, gene.panel.pk])

        if chromosome == 'X' and moi not in ["X-LINKED: hemizygous mutation in males, biallelic mutations in females",
                                             "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)",
                                             ]:
            msg = 'Green gene {} on X chromosome with {} moi on panel {}'.format(gene.name, gene.moi, gene.panel)
            incorrect_moi.append([msg, gene.name, gene.moi, gene.panel, gene.panel.pk])

        if gene_check.get(gene.name):
            if moi != gene_check[gene.name]:
                exception = ["MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted", "MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown"]
                if moi not in exception and gene_check[gene.name] not in exception:
                    msg = 'Green gene {} has different moi {} on panel {} than {}'.format(gene.name, gene.moi, gene.panel, gene_check[gene.name])
                    incorrect_moi.append([msg, gene.name, gene.moi, gene.panel, gene.panel.pk])
        else:
            try:
                moi = set(moi_mapping.get(moi.split()[0]))
            except TypeError as e:
                moi = set()
            if gene.gene.get('omim_gene') and settings.OMIM_API_KEY:
                omim_moi = retrieve_omim_moi(gene.gene.get('omim_gene')[0])
                if not any(omim_moi):
                    continue
                if moi & omim_moi:
                    gene_check[gene.name] = gene.moi
                else:
                    msg = 'Green gene {} with discrepant OMIM moi {} and {} on panel {}'.format(gene.name, omim_moi, gene.moi, gene.panel)
                    incorrect_moi.append([msg, gene.name, gene.moi, gene.panel, gene.panel.pk])
            else:
                if moi:
                    gene_check[gene.name] = gene.moi
                else:
                    msg = 'Green gene {} with empty moi on panel {}'.format(gene.name, gene.panel)
                    incorrect_moi.append([msg, gene.name, gene.moi, gene.panel, gene.panel.pk])

    if incorrect_moi:
        with tempfile.TemporaryFile(mode="r+") as file:
            writer = csv.writer(file)
            writer.writerow(['Message', 'Gene Name', 'Moi', 'Panel', 'ID'])
            for error in incorrect_moi:
                writer.writerow(error)

            email = EmailMessage(
                "MOI Errors",
                'Errors are attached in csv file.',
                settings.DEFAULT_FROM_EMAIL,
                [settings.PANEL_APP_EMAIL],
            )
            email.attach('incorrect_moi.csv', file.read(), 'text/csv')
            email.send()
