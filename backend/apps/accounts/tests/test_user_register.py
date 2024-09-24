from django.urls import include, path, reverse
from rest_framework.test import APITestCase, URLPatternsTestCase


class AccountTests(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path('register/', include('apps.accounts.api.urls')),
    ]

    def test_create_account(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('register')
        data = {'email': 'test@test.com', 'password': '<PASSWORD>'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_account_with_invalid_email(self):
        """
        Ensure we can't create a new account object with an invalid email.
        """
        url = reverse('register')
        invalid_data = {'email': 'test@test', 'password': '<PASSWORD>'}
        invalid_response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(invalid_response.status_code, status.HTTP_400_OK)

    def test_create_account_with_duplicate_email(self):
        """
        Ensure we can't create a new account object with a duplicate email.
        """
        url = reverse('register')
        first_email = {'email': 'test@test.com', 'password': '<PASSWORD>'}
        duplicate_email = first_email.copy()
        first_response = self.client.post(url, first_email, format='json')
        duplicate_response = self.client.post(url, duplicate_email, format='json')
        self.assertEqual(first_response.status_code, status.HTTP_201_OK)
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_OK)