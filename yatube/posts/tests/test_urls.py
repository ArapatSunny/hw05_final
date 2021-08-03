from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='TestingURLMan')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.user2 = User.objects.create_user(username='user2')
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

        cls.group = Group.objects.create(
            title='GroupTestUrls',
            slug='testUrls',
            description='Тестируем адреса, доступность'
        )

        cls.post = Post.objects.create(
            text='Текст поста URL Test',
            author=cls.user,
            group=cls.group,
        )

        cls.post_edit_address = reverse('post_edit', kwargs={
            'username': cls.user,
            'post_id': cls.post.id})

        cls.post_id_address = reverse('post', kwargs={
            'username': cls.user,
            'post_id': cls.post.id})

        cls.profile_address = reverse('profile', kwargs={
            'username': cls.user
        })

        cls.templates_urls = {
            'index.html': '/',
            'group.html': f'/group/{cls.group.slug}/',
            'new.html': '/new/',
            'profile.html': f'/{cls.post.author.username}/',
            'post.html': cls.post_id_address,
        }

        cls.urls_access = {
            '/': cls.guest_client,
            '/group/testUrls/': cls.guest_client,
            '/new/': cls.authorized_client2,
            cls.profile_address: cls.guest_client,
            cls.post_id_address: cls.guest_client,
            cls.post_edit_address: cls.authorized_client,
        }

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_urls_access(self):
        """Проверка доступа страниц."""
        for url, access in URLTests.urls_access.items():
            with self.subTest(url=url):
                response = access.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_access_for_not_author_post(self):
        """Проверка доступа страницы для не автора поста."""
        response_list = [
            URLTests.guest_client.get(URLTests.post_edit_address),
            URLTests.authorized_client2.get(URLTests.post_edit_address),
        ]
        for response in response_list:
            self.assertNotEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_redirect_for_not_author_post(self):
        """Проверка переадресации страницы post_edit для не автора поста."""
        response = URLTests.guest_client.get(
            URLTests.post_edit_address, follow=True)
        self.assertRedirects(
            response,
            f'/auth/login/?next={URLTests.post_edit_address}')
        response = URLTests.authorized_client2.get(
            URLTests.post_edit_address, follow=True)
        self.assertRedirects(
            response, URLTests.post_id_address)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, address in URLTests.templates_urls.items():
            with self.subTest(address=address):
                response = URLTests.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_edit_url_uses_correct_template(self):
        """URL-адрес post_edit использует соответсвующий шаблон."""
        response = URLTests.authorized_client.get(URLTests.post_edit_address)
        self.assertTemplateUsed(response, 'new.html')

    def test_page_not_found_url_uses_correct_template(self):
        """Если страница не найдена, возврат Ошибка 404."""
        template_access_for_users = {
            '/404/': URLTests.guest_client,
            '/404a/': URLTests.authorized_client,
        }
        for template, user in template_access_for_users.items():
            with self.subTest(template=template):
                response = user.get(template)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
