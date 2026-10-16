from rest_framework.authtoken.models import Token


class DjangoTokenRepository:
    def get_or_create(self, user_id):
        token, _ = Token.objects.get_or_create(user_id=user_id)
        return token.key

    def revoke(self, key):
        Token.objects.filter(key=key).delete()
