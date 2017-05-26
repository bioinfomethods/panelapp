from django.db import models
from model_utils.models import TimeStampedModel
from accounts.models import User


class Comment(TimeStampedModel):
    user = models.ForeignKey(User)
    comment = models.TextField()
    flagged = models.BooleanField(default=False)

    def dict_tr(self):
        return {
            "date": self.created,
            "comment": self.comment
        }

    def __eq__(self, other):
        if self.comment == other.comment:
            return True
        else:
            return False
