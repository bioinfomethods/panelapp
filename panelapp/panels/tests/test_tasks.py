from faker import Factory
from django.test import override_settings
import responses
from django.core import mail
from accounts.tests.setup import LoginGELUser
from panels.models import GenePanel
from panels.tests.factories import GeneFactory
from panels.tests.factories import GenePanelSnapshotFactory
from panels.tests.factories import GenePanelEntrySnapshotFactory
from panels.tasks import moi_check, retrieve_omim_moi


fake = Factory.create()


class TaskTest(LoginGELUser):

    @override_settings(OMIM_API_KEY="TEST-KEY")
    @responses.activate
    def test_moi_check(self):
        responses.add(responses.GET, 'https://api.omim.org/api/entry?mimNumber={}&include=geneMap&include=externalLinks&format=json&apiKey={}'.format('123456', "TEST-KEY"),
                      json={'omim':{'entryList':[{'entry':{'geneMap':{'phenotypeMapList':[{"phenotypeMap":{'phenotypeInheritance':'X-linked recessive'}}]}}}]}}, status=200)
        gene = GeneFactory(omim_gene=['123456'])
        gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public, major_version=2)
        GenePanelEntrySnapshotFactory.create_batch(2, panel=gps, saved_gel_status=3)
        GenePanelEntrySnapshotFactory.create(gene_core=gene,panel=gps, saved_gel_status=3, moi="BIALLELIC, autosomal or pseudoautosomal")
        moi_check()
        assert mail.outbox[0].attachments == [('incorrect_moi.csv', '', 'text/csv')]
