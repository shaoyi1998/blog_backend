# -*- coding: UTF-8 -*-
"""
@Project :riyueweiyi 
@File    :serializers
@IDE     :PyCharm 
@Author  :方正
@Date    :2023/6/15 11:26 
"""
from rest_framework import serializers

from blog.models import ArticleModel, MemberModel, ImageModel


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberModel
        fields = ["id", "username"]


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleModel
        fields = ["id", "title", "author", "content"]


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = ["id", "article", "path"]
