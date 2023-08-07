# -*- coding: UTF-8 -*-
"""
@Project :riyueweiyi 
@File    :serializers
@IDE     :PyCharm 
@Author  :方正
@Date    :2023/6/15 11:26 
"""
import re
from typing import Optional

from django.core.cache import cache
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from blog.models import ArticleModel, MemberModel, ImageModel, CategoryModel


class LoginVerificationSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        queryset = MemberModel.objects.all()
        # 真正的数据全部由加密的token来确保不会被伪造
        token = super().get_token(user)
        token['id'] = user.id
        token["is_root"] = True if user.is_superuser else False
        token['username'] = user.username
        return token

    def validate(self, attrs: dict) -> Optional[dict]:
        """
        :param attrs: 登录字典(用户名,密码)
        :type attrs: dict
        :return: token的dict数据或None
        :rtype: dict|None
        """
        cache_key = f'login_attempts:{attrs.get("username", "未知用户")}'
        attempts = cache.get(cache_key, 0)
        if attempts >= 3:
            raise serializers.ValidationError("用户失败次数过多,请五分钟后重试")
        try:
            data = super().validate(attrs)
            refresh = self.get_token(self.user)
            data['access'] = str(refresh.access_token)
            data["id"] = self.user.id
            data["is_root"] = self.user.is_superuser
            data['username'] = self.user.username
            data["check_code"] = self.generate_code(data['access'])
            return data
        except AuthenticationFailed:
            attempts += 1
            cache.set(cache_key, attempts, 300)
            raise serializers.ValidationError("您的用户名或密码错误")

    @staticmethod
    def generate_code(original_jwt):
        header, payload, signature = original_jwt.split(".")
        # 将字母转换成数字
        header_numeric = sum([ord(_) for _ in header])
        payload_numeric = sum([ord(_) for _ in payload])
        signature_numeric = sum([ord(_) for _ in signature])
        print(header_numeric, payload_numeric, signature_numeric)
        # 计算密钥
        return header_numeric ^ payload_numeric * signature_numeric


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberModel
        fields = ["id", "username"]


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleModel
        fields = ["id", "title", "author", "content", "release_date", "modification_date", "type"]


class ArticleSummarySerializer(serializers.ModelSerializer):
    type_name = serializers.CharField(source="type.name", read_only=True)
    content_summary = serializers.SerializerMethodField()

    class Meta:
        model = ArticleModel
        fields = ["id", "title", "author", "release_date", "modification_date", "type_name", "content_summary"]

    def get_content_summary(self, article: ArticleModel):
        # 正则清洗html格式的内容字段为中文
        pattern = re.compile(r'[^\u4e00-\u9fa5，。、；：！？,.!]')
        # sub替换上述字段为空字段
        return pattern.sub("", article.content)[:100] + "..."


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = ["id", "article", "path"]


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()

    def get_parent_name(self, obj):
        if obj.parent:
            return obj.parent.name
        return "无"

    class Meta:
        model = CategoryModel
        fields = ["id", "name", "parent", "parent_name", ]
