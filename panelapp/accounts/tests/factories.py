import factory
from accounts.models import User
from accounts.models import Reviewer


class ReviewerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reviewer

    affiliation = factory.Faker('word')
    workplace = Reviewer.WORKPLACES.Other
    role = Reviewer.ROLES.Other
    group = Reviewer.GROUPS.Other

    user = factory.SubFactory('accounts.tests.factories.UserFactory', reviewer=None)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('first_name')
    username = factory.Faker('user_name')
    email = factory.LazyAttribute(lambda a: '{0}.{1}@example.com'.format(a.first_name, a.last_name).lower())
    is_active = True

    reviewer = factory.RelatedFactory(ReviewerFactory, 'user')

    @classmethod
    def _generate(cls, create, attrs):
        """
        Set the password so we can login via the frontend
        """

        user = super()._generate(create, attrs)
        user.set_password('pass')
        user.save()

        return user
