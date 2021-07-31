from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test',
            description='Это тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост первых 15 символов',
            author=User.objects.create(
                username='Testingman', password='12345',
            ),
        )

    def test_text_max_lenght(self):
        """Проверка ограничения вывода длины поста."""
        post = PostModelTest.post
        expected_length = post.text[:15]
        self.assertEqual(expected_length, 'Тестовый пост п')

    def test_object_group_is_title_field(self):
        """В поле __str__ объекта group записано значение поля group.title."""
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
