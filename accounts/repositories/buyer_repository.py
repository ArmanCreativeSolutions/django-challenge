from django.contrib.auth import get_user_model


class DjangoBuyerRepository:
    def lock_active(self, user_id):
        user = get_user_model().objects.select_for_update().filter(pk=user_id).first()
        return user is not None and user.is_active
