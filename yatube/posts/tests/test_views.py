import shutil
import tempfile
import time

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.guest_client = Client()

        cls.user = User.objects.create_user(username='ViewTestMan')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.user2 = User.objects.create_user(username='ViewTestMan2')
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

        cls.group = Group.objects.create(
            title='TitleGroupViewsTest',
            slug='test_views_slug',
            description='Тест группа 2 для view-тестов',
        )
        cls.group2 = Group.objects.create(
            title='TitleGroupViewsTest2',
            slug='test_views_slug2',
            description='Тест группа 2 для view-тестов',
        )
        cls.post1 = Post.objects.create(
            text='Тест-пост 1 для view группы 1',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def sub_test_is_instance(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                return self.assertIsInstance(form_field, expected)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('index'): 'index.html',
            reverse('group_posts',
                    kwargs={'slug': PostsPagesTests.group.slug}):
            'group.html',
            reverse('post_edit',
                    kwargs={
                        'username': PostsPagesTests.post1.author.username,
                        'post_id': PostsPagesTests.post1.id}):
            'new.html',
            reverse('new_post'): 'new.html',
            reverse('profile', kwargs={
                    'username': PostsPagesTests.user.username}):
            'profile.html',
            reverse('follow_index'): 'follow.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = PostsPagesTests.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_shows_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = PostsPagesTests.guest_client.get(reverse('index'))
        self.assertEqual(response.context['page'].number, 1)
        self.assertEqual(len(response.context.get('page').object_list), 1)

    def test_group_page_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = PostsPagesTests.guest_client.get(reverse(
            'group_posts', kwargs={'slug': PostsPagesTests.group.slug})
        )
        self.assertEqual(response.context['page'].number, 1)
        self.assertEqual(response.context['group'], PostsPagesTests.group)

    def test_new_post_page_shows_correct_context(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = PostsPagesTests.authorized_client.get(reverse('new_post'))
        PostsPagesTests.sub_test_is_instance(self, response)
        self.assertTrue(response.context['is_new'])

    def test_post_edit_page_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = PostsPagesTests.authorized_client.get(reverse(
            'post_edit', kwargs={
                'username': PostsPagesTests.post1.author.username,
                'post_id': PostsPagesTests.post1.id}))
        PostsPagesTests.sub_test_is_instance(self, response)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = PostsPagesTests.authorized_client.get(reverse(
            'profile', kwargs={
                'username': PostsPagesTests.user.username}))
        self.assertEqual(response.context['author'].username, 'ViewTestMan')
        self.assertEqual(response.context['page'].number, 1)

    def test_post_page_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = PostsPagesTests.authorized_client.get(reverse(
            'post', kwargs={
                'username': PostsPagesTests.post1.author.username,
                'post_id': PostsPagesTests.post1.id}))
        self.assertEqual(response.context['post'], PostsPagesTests.post1)
        self.assertEqual(str(response.context['author']),
                         PostsPagesTests.post1.author.username)
        form_fields = {
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                return self.assertIsInstance(form_field, expected)

    def test_index_page_contains_posts(self):
        """Посты с группой и без группы попадают на главную страницу"""
        Post.objects.create(
            text='Тест-пост для view без группы',
            author=PostsPagesTests.user)
        response0 = PostsPagesTests.guest_client.get(reverse('index'))
        self.assertEqual(len(response0.context.get('page').object_list), 2)

    def test_group_post_contains_expected_group_post(self):
        """Пост попал в группу для которой был предназначен."""
        response1 = PostsPagesTests.guest_client.get(reverse(
            'group_posts', kwargs={'slug': PostsPagesTests.group.slug}))
        post_group1_count = len(response1.context.get('page').object_list)
        self.assertEqual(post_group1_count, 1)
        post_group1 = response1.context.get('page').object_list[0]
        self.assertEqual(post_group1.text, 'Тест-пост 1 для view группы 1')
        self.assertEqual(post_group1.author.username, 'ViewTestMan')
        self.assertEqual(post_group1.group.title, 'TitleGroupViewsTest')

    def test_group_post_not_contains_unexpected_group_post(self):
        """Пост не попал в группу для которой не был предназначен."""
        Post.objects.create(
            text='Тест-пост 2 для view группы 2',
            author=PostsPagesTests.user2,
            group=PostsPagesTests.group2,
        )
        response2 = PostsPagesTests.guest_client.get(reverse(
            'group_posts', kwargs={'slug': PostsPagesTests.group2.slug}))
        post_group2_count = len(response2.context.get('page').object_list)
        self.assertEqual(post_group2_count, 1)
        response1 = PostsPagesTests.guest_client.get(reverse(
            'group_posts', kwargs={'slug': PostsPagesTests.group.slug}))
        post_group1 = response1.context.get('page').object_list[0]
        post_group2 = response2.context.get('page').object_list[0]
        self.assertNotEqual(post_group1, post_group2)

    def test_view_page_not_found_uses_correct_template(self):
        """Если страница не найдена, используется шаблон 404.html."""
        templates_for_users = {
            '/404/': PostsPagesTests.guest_client,
            '/404a/': PostsPagesTests.authorized_client,
        }
        for template, user in templates_for_users.items():
            with self.subTest(template=template):
                response = user.get(template)
                self.assertTemplateUsed(response, 'misc/404.html')

    def test_pages_context_contains_picture(self):
        """Проверка при выводе поста с картинкой изображение
        передаётся в словаре context."""
        response_index = PostsPagesTests.guest_client.get(reverse('index'))
        response_profile = PostsPagesTests.guest_client.get(reverse(
            'profile', kwargs={
                'username': PostsPagesTests.user.username}))
        response_group = PostsPagesTests.guest_client.get(
            reverse('group_posts',
                    kwargs={'slug': PostsPagesTests.group.slug}))
        response_post = PostsPagesTests.guest_client.get(
            reverse('post', kwargs={
                'username': PostsPagesTests.post1.author.username,
                'post_id': PostsPagesTests.post1.id}))
        pages_context_list = [
            response_index.context.get('page').object_list[0].image,
            response_profile.context.get('page').object_list[0].image,
            response_group.context.get('page').object_list[0].image,
            response_post.context['post'].image,
        ]
        for pages_context in pages_context_list:
            self.assertEqual(pages_context, 'posts/small.gif')

    def test_index_cache_page(self):
        """Проверка кеширования главной страницы 20 секунд."""
        response0 = PostsPagesTests.guest_client.get(reverse('index'))
        len0 = len(response0.context.get('page').object_list)
        self.assertEqual(len0, 1)

        post2 = Post.objects.create(
            text='Cache+1',
            author=PostsPagesTests.user,
        )
        post2.save()

        response1 = PostsPagesTests.guest_client.get(reverse('index'))
        self.assertIsNone(response1.context)

        time.sleep(20)
        response1 = PostsPagesTests.guest_client.get(reverse('index'))
        len1 = len(response1.context.get('page').object_list)
        self.assertEqual(len1, 2)

    def test_cache(self):
        """Запись из базы остаётся в response.content главной страницы
        до тех пор, пока кеш не будет очищен принудительно."""
        response0 = PostsPagesTests.guest_client.get(reverse('index'))
        len0 = len(response0.context.get('page').object_list)
        self.assertEqual(len0, 1)

        post = Post.objects.filter(author=PostsPagesTests.user)
        post.delete()

        response1 = PostsPagesTests.guest_client.get(reverse('index'))
        p = '<a name="post'
        encode = p.encode()
        self.assertTrue(encode in response1.content)

        cache.clear()

        response2 = PostsPagesTests.guest_client.get(reverse('index'))
        len2 = len(response2.context.get('page').object_list)
        self.assertEqual(len2, 0)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()

        cls.user0 = User.objects.create_user(username='User0')
        cls.authorized_client0 = Client()
        cls.authorized_client0.force_login(cls.user0)

        cls.user1 = User.objects.create_user(username='User1')
        cls.authorized_client1 = Client()
        cls.authorized_client1.force_login(cls.user1)

        cls.user2 = User.objects.create_user(username='User2')
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

    def check_follow_false(self):
        follow = Follow.objects.filter(
            user=FollowViewsTest.user1,
            author=FollowViewsTest.user0).exists()
        return self.assertFalse(follow)

    def check_follow_true(self):
        follow = Follow.objects.filter(
            user=FollowViewsTest.user1,
            author=FollowViewsTest.user0
        ).exists()
        return self.assertTrue(follow)

    def test_authorized_user_can_follow_authors(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        FollowViewsTest.check_follow_false(self)

        FollowViewsTest.authorized_client1.post(
            reverse('profile_follow',
                    kwargs={'username': FollowViewsTest.user0.username}),
            follow=True)

        FollowViewsTest.check_follow_true(self)

    def test_authorized_user_can_unfollow_authors(self):
        """Авторизованный пользователь может удалять подписку
        на других пользователей."""
        Follow.objects.create(
            user=FollowViewsTest.user1,
            author=FollowViewsTest.user0)

        FollowViewsTest.check_follow_true(self)

        FollowViewsTest.authorized_client1.post(
            reverse('profile_unfollow',
                    kwargs={'username': FollowViewsTest.user0.username}),
            follow=True)

        FollowViewsTest.check_follow_false(self)

    def test_post_appears_only_in_line_of_following_user(self):
        """Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан на него.."""
        Follow.objects.create(
            user=FollowViewsTest.user1,
            author=FollowViewsTest.user0)

        response0 = FollowViewsTest.authorized_client1.get(
            reverse('follow_index'))
        len0 = len(response0.context.get('page').object_list)
        self.assertEqual(len0, 0)

        Post.objects.create(
            text='follow',
            author=FollowViewsTest.user0,
        )

        response1 = FollowViewsTest.authorized_client1.get(
            reverse('follow_index'))
        len1 = len(response1.context.get('page').object_list)
        self.assertEqual(len1, 1)

        post = response1.context.get('page').object_list[0]
        self.assertEqual(post.text, 'follow')

        response2 = FollowViewsTest.authorized_client2.get(
            reverse('follow_index'))
        len2 = len(response2.context.get('page').object_list)
        self.assertEqual(len2, 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='PaginatorTestMan')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.posts = []
        for i in range(13):
            cls.posts.append(
                Post(
                    text=f'Тестовое сообщение{i}',
                    author=cls.user
                )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        cache.clear()

    def test_pages_contains_records(self):
        """Количество записей к выводу на страницу."""
        response1 = self.guest_client.get(reverse('index'))
        response2 = self.guest_client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response1.context.get('page').object_list), 10)
        self.assertEqual(len(response2.context.get('page').object_list), 3)
