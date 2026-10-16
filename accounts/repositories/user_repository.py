from django.contrib.auth import get_user_model

from accounts.domain.data_objects import UserData


class DjangoUserRepository:
    def username_exists(self, username):
        return get_user_model().objects.filter(username=username).exists()

    def create(self, *, username, password):
        user = get_user_model().objects.create_user(username=username, password=password)
        return UserData(user.pk, user.username)
