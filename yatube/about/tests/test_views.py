from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

        self.response = self.guest_client.get(reverse('about:author'))
        self.response2 = self.guest_client.get(reverse('about:tech'))

    def test_urls_author_and_tech_accessable_by_name_in_view(self):
        """URLs, генерируемые при помощи имени
        about:author, about:tech доступны."""
        response_list = [self.response, self.response2, ]
        for response in response_list:
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_author_and_tech_uses_correct_template(self):
        """При запросе к about:author, about:tech
        применяется соответствующие шаблоны."""
        response_expected = {
            self.response: 'about/author.html',
            self.response2: 'about/tech.html',
        }
        for response, expected in response_expected.items():
            with self.subTest(response=response):
                self.assertTemplateUsed(response, expected)
