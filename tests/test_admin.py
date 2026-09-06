import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

CHANGELIST_URLS = [
    "admin:chores_member_changelist",
    "admin:chores_chore_changelist",
    "admin:chores_completion_changelist",
]


@pytest.fixture
def superuser_client(client, db):
    user = get_user_model().objects.create_superuser(
        username="admin", email="admin@example.com", password="password"
    )
    client.force_login(user)
    return client


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", CHANGELIST_URLS)
def test_admin_changelist_returns_200_for_superuser(superuser_client, url_name):
    response = superuser_client.get(reverse(url_name))

    assert response.status_code == 200
