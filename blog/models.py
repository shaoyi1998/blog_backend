import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now


class MemberModel(AbstractUser):
    join_date = models.DateField(default=datetime.date.today(), verbose_name="加入时间")

    def __str__(self):
        return self.username


class CategoryModel(models.Model):
    name = models.CharField(max_length=100,unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ArticleModel(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50, verbose_name="文章标题", unique=True)
    content = models.CharField(max_length=100000000, verbose_name="文章内容")
    author = models.ForeignKey(MemberModel, on_delete=models.SET_NULL, null=True, verbose_name="作者")
    type = models.ForeignKey(CategoryModel, on_delete=models.PROTECT, verbose_name="类型")
    release_date = models.DateTimeField(verbose_name="发布时间")
    modification_date = models.DateTimeField(default=now(),verbose_name="修改时间")

    def __str__(self):
        return self.title


class ImageModel(models.Model):
    id = models.AutoField(primary_key=True)
    article = models.ForeignKey(ArticleModel, on_delete=models.CASCADE, related_name='images', verbose_name="所属文章")
    path = models.ImageField(upload_to='media/', verbose_name="路径")

    def __str__(self):
        return self.path
