from http import HTTPStatus

from django.test import Client, TestCase


class StaticPagesURLsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

        self.response = self.guest_client.get('/about/author/')
        self.response2 = self.guest_client.get('/about/tech/')

    def test_author_and_tech_url_access(self):
        """Проверка доступности адресов страниц Об авторе и Технологии."""
        response_list = [self.response, self.response2, ]
        for response in response_list:
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_author_and_tech_uses_correct_template(self):
        """Проверка шаблона для страниц Об авторе и Технологии."""
        self.assertTemplateUsed(self.response, 'about/author.html')
        self.assertTemplateUsed(self.response2, 'about/tech.html')
