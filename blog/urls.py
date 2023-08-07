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
    path("api/login_verification/", LoginVerificationApi.as_view()),
    path("api/article/", ArticleViewApi.as_view()),
    path("api/article/<int:pk>", ArticleViewApi.as_view()),
    path("api/article_root/", ArticleRootViewApi.as_view()),
    path("api/article_root/<int:pk>", ArticleRootViewApi.as_view()),
    path("api/article_summary/", ArticleSummaryViewApi.as_view()),
    path("api/article_summary_root/", ArticleSummaryRootViewApi.as_view()),
    path("api/image/", ImageViewApi.as_view()),
    path("api/category/", CategoryViewApi.as_view()),
    path("api/category/<int:pk>", CategoryViewApi.as_view()),
    path("api/category_summary/", CategorySummaryViewApi.as_view()),
    path("api/setting_image/",get_image_setting),
    path("api/change_image_compressibility/", change_image_compressibility),
    path("api/change_image_save_method/",change_image_save_method),
]
