from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AccountTests(APITestCase):
    def test_create_account(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse("register-list")
        data = {"email": "test@test.com", "password": "<PASSWORD>"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 6)

    def test_create_account_with_invalid_email(self):
        """
        Ensure we can't create a new account object with an invalid email.
        """
        url = reverse("register-list")
        invalid_data = {"email": "test@test", "password": "<PASSWORD>"}
        invalid_response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_account_with_duplicate_email(self):
        """
        Ensure we can't create a new account object with a duplicate email.
        """
        url = reverse("register-list")
        first_email = {"email": "test@test.com", "password": "<PASSWORD>"}
        duplicate_email = first_email.copy()
        first_response = self.client.post(url, first_email, format="json")
        duplicate_response = self.client.post(url, duplicate_email, format="json")
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)
