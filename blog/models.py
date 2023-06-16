import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models


class MemberModel(AbstractUser):
    join_date = models.DateField(default=datetime.date.today(), verbose_name="加入时间")

    def __str__(self):
        return self.username


class ArticleModel(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50, verbose_name="文章标题")
    content = models.CharField(max_length=10000, verbose_name="文章内容")
    author = models.ForeignKey(MemberModel, on_delete=models.SET_NULL, null=True, verbose_name="作者")
    type = models.CharField(max_length=200,verbose_name="文章分类")

    def __str__(self):
        return self.title


class ImageModel(models.Model):
    id = models.AutoField(primary_key=True)
    article = models.ForeignKey(ArticleModel, on_delete=models.CASCADE, related_name='images', verbose_name="所属文章")
    path = models.ImageField(upload_to='article_images/', verbose_name="路径")

    def __str__(self):
        return self.path
