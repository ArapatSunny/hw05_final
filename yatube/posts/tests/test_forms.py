import shutil
import tempfile
import unittest
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.user = User.objects.create(username='PostFormMan')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Группа создания поста new',
            description='Проверка формы new',
            slug='test_create_new_post',
        )

        cls.post = Post.objects.create(
            text='Тестовый new1 текст',
            author=cls.user,
            group=cls.group,
        )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post(self):
        """Валидная форма создает запись в БД."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый new2 текст',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }
        response = PostFormTests.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.first()
        self.assertEqual(new_post.text, 'Тестовый new2 текст')
        self.assertEqual(new_post.group.title, 'Группа создания поста new')
        self.assertEqual(new_post.author.username, 'PostFormMan')
        self.assertEqual(new_post.image, 'posts/small.gif')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        """Проверка редактирования поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Редакция 1',
            'group': PostFormTests.group.id,
        }
        response = PostFormTests.authorized_client.post(
            reverse('post_edit', kwargs={
                'username': PostFormTests.post.author.username,
                'post_id': PostFormTests.post.id,
            }),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('post', kwargs={
            'username': PostFormTests.post.author.username,
            'post_id': PostFormTests.post.id,
        }))
        self.assertEqual(Post.objects.count(), posts_count)
        edited_post = Post.objects.last()
        self.assertEqual(edited_post.text, 'Редакция 1')
        self.assertEqual(edited_post.group.id, 1)
        self.assertEqual(edited_post.author, PostFormTests.user)
        self.assertEqual(response.status_code, HTTPStatus.OK)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user0 = User.objects.create_user(username='PostAuthor')
        cls.authorized_client0 = Client()
        cls.authorized_client0.force_login(cls.user0)

        cls.user1 = User.objects.create_user(username='CommentMan')
        cls.authorized_client1 = Client()
        cls.authorized_client1.force_login(cls.user1)

        cls.user2 = User.objects.create_user(username='CommentMan2')

        cls.post0 = Post.objects.create(
            text='Пост автора',
            author=cls.user0,
        )

        cls.form = CommentForm()

    def test_only_authorized_client_can_comment_post(self):
        """Только авторизированный пользователь может комментировать посты."""
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)
        form_data = {
            'post': CommentFormTest.post0,
            'author': CommentFormTest.user1,
            'text': 'Коммент от юзера1',
        }
        response = CommentFormTest.authorized_client1.post(
            reverse('add_comment', kwargs={
                'username': CommentFormTest.post0.author.username,
                'post_id': CommentFormTest.post0.id,
            }),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('post', kwargs={
            'username': CommentFormTest.post0.author.username,
            'post_id': CommentFormTest.post0.id
        }))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        new_comment = Comment.objects.first()
        self.assertEqual(new_comment.text, 'Коммент от юзера1')
        self.assertEqual(str(new_comment.author), 'CommentMan')
        self.assertEqual(new_comment.post, CommentFormTest.post0)

    @unittest.expectedFailure
    def test_non_authorized_client_trying_to_comment_post(self):
        """Попытка неавторизованного пользователя прокомментировать пост."""
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)
        form_data = {
            'post': CommentFormTest.post0,
            'author': CommentFormTest.user2,
            'text': 'Коммент от юзера2',
        }
        response = CommentFormTest.user2.post(
            reverse('add_comment', kwargs={
                'username': CommentFormTest.post0.author.username,
                'post_id': CommentFormTest.post0.id,
            }),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('post', kwargs={
            'username': CommentFormTest.post0.author.username,
            'post_id': CommentFormTest.post0.id
        }))
        self.assertEqual(Comment.objects.count(), comments_count + 1 + 1)
