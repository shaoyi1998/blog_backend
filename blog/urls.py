# -*- coding: UTF-8 -*-
"""
@Project :riyueweiyi 
@File    :urls
@IDE     :PyCharm 
@Author  :方正
@Date    :2023/6/15 11:43 
"""
from django.urls import path, include

from blog.views import *

urlpatterns = [
    path("api/article/",ArticleViewApi.as_view()),
    path("api/image/", ImageViewApi.as_view())
]

