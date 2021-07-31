from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name='Название группы',
        max_length=200,
        help_text='Дайте название группе'
    )
    slug = models.SlugField(
        verbose_name='Адрес страницы группы',
        unique=True,
        help_text=('Укажите уникальный адрес для страницы группы. '
                   'Используйте только латиницу, цифры, дефисы и '
                   'знаки подчёркивания'),
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Опишите вашу группу',
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Введите текст',
        help_text='Текст вашего поста здесь'
    )
    pub_date = models.DateTimeField(
        'date published',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Выбор группы',
        help_text='Выбор группы по желанию'
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True, null=True
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15] + '...'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        verbose_name='Введите текст',
        help_text='Текст Вашего комментария здесь'
    )
    created = models.DateTimeField(
        'date published',
        auto_now_add=True,
    )

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        blank=True, null=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        blank=True, null=True
    )
    created = models.DateTimeField(
        auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created']

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name="unique_followers")
        ]

    def __str__(self):
        return f'{self.user} follows {self.author}'
