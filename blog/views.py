import base64
import datetime
import json
import os
import re
from functools import wraps
from io import BytesIO

import jwt
from PIL import Image
from django.db import transaction, models
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseServerError, HttpResponse, HttpRequest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, filters
from rest_framework_simplejwt.views import TokenObtainPairView

from blog.models import ArticleModel, ImageModel, CategoryModel
from blog.serializers import ArticleSerializer, ImageSerializer, LoginVerificationSerializer, CategorySerializer, \
    ArticleSummarySerializer
from riyueweiyi import settings


def token_verify(f):
    @wraps(f)
    def warp(self, *args, **kwargs):
        # 根据函数和类区分jwt_token验证处理逻辑
        jwt_token = str(self.request.auth) if not isinstance(self, HttpRequest) else \
            self.headers.get("Authorization").split(" ")[1]
        token_data = jwt.decode(jwt_token, key=settings.SIMPLE_JWT["SIGNING_KEY"],
                                algorithms=["HS256"])
        kwargs["token_data"] = token_data
        return f(self, *args, **kwargs)

    return warp


def compress_base64_image(image_data, quality=90):
    # 将图像数据加载到 Pillow 图像对象
    image = Image.open(BytesIO(image_data))
    # 压缩图像
    image = image.convert("RGB")  # 将图像转换为 RGB 模式
    output = BytesIO()  # 创建一个字节流对象，用于保存压缩后的图像数据
    image.save(output, format="JPEG", quality=quality)  # 保存图像到字节流，指定压缩质量

    # 将压缩后的图像数据转换为 Base64 编码

    return output


def extract_base64_images(title: str, content: str, article: models.Model):
    # 匹配正则
    pattern = '<img.*?src="data:image/[^;]+;base64,([^"]+)".*?>'
    replacement = r'<img src="{}" />'
    for index, match in enumerate(re.findall(pattern, content)):
        image_data = base64.b64decode(match)
        compressed_data = compress_base64_image(image_data, quality=settings.IMAGE_COMPRESSIBILITY)
        # 创建 ImageModel 实例
        image = ImageModel(article=article)
        # 保存图像文件
        image_path = 'article_images/{}/{}.jpeg'.format(title, index)  # 假设使用 PNG 格式保存
        image_file = compressed_data
        # 原子操作
        with transaction.atomic():
            if os.path.exists(abs_path := os.path.join(settings.MEDIA_ROOT, image_path)):
                os.remove(abs_path)
            ImageModel.objects.filter(article=article, path=image_path).delete()
            image.path.save(image_path, image_file)
        # 将文章内容中的 img src 替换为图像的 URL
        replacement_string = replacement.format(image.path.url)
        # 替换 content 中的 img src
        content = re.sub(pattern, replacement_string, content, count=1)
    return content


# Create your views here.

class LoginVerificationApi(TokenObtainPairView):
    serializer_class = LoginVerificationSerializer


class ArticleViewApi(generics.ListAPIView):
    queryset = ArticleModel.objects.all().order_by("-release_date")
    serializer_class = ArticleSerializer
    pagination_class = None

    def get_authenticators(self):
        # 在GET请求中，如果未提供JWT令牌，则不执行JWT认证
        if self.request.method == 'GET':
            return []
        return super().get_authenticators()

    def get(self, request, *args, **kwargs):
        now = timezone.now()
        self.queryset = self.queryset.filter(release_date__lt=now)
        article_id = int(kwargs.get("pk", ""))
        article = self.queryset.get(id=article_id)
        if article:
            return JsonResponse(status=200, data={
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "type": article.type.name if article.type else None,
                "release_date": article.release_date,
                "author": article.author,
                "modification_date": article.modification_date
            })
        return JsonResponse(status=404, data={"error": "访问文章不存在或无权访问"})


class ArticleRootViewApi(generics.CreateAPIView, generics.ListAPIView, generics.UpdateAPIView,
                         generics.DestroyAPIView):
    queryset = ArticleModel.objects.all().order_by("-release_date")
    serializer_class = ArticleSerializer
    pagination_class = None

    @token_verify
    def get(self, request, *args, **kwargs):
        if article_id := int(kwargs.get("pk", "")):
            article = ArticleModel.objects.get(id=article_id)
            return JsonResponse(status=200, data={
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "type": article.type.name if article.type else None,
                "release_date": article.release_date,
                "author": article.author,
                "modification_date": article.modification_date
            })
        return self.list(request)

    @token_verify
    def post(self, request, *args, **kwargs):
        # 创建处理人与处理时间
        if kwargs["token_data"]["is_root"]:
            request.data["type"] = int(request.data["type"][-1])
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            article = serializer.save()
            category = CategoryModel.objects.get(id=request.data["type"])  # 获取ID为20的CategoryModel对象
            article.type = category
            # 检测是否选择保存为文件或是base64直接存储
            article.content = extract_base64_images(request.data.get("title", "-1"), request.data.get("content", ""),
                                                    article) if settings.IMAGE_SAVE_IS_FILE else request.data.get(
                "content", "")
            article.save()
            return JsonResponse(status=201, data={'message': '文章上传成功'})
        else:
            return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行创建操作", })

    @token_verify
    def put(self, request, *args, **kwargs):
        if kwargs["token_data"]["is_root"]:
            request.data["type"] = int(request.data.get("type")[-1]) if isinstance(request.data.get("type"),
                                                                                   list) else request.data.get("type")
            request.data["content"] = extract_base64_images(request.data.get("title", "-1"),
                                                            request.data.get("content", ""),
                                                            ArticleModel.objects.get(id=kwargs.get("pk"))) \
                if settings.IMAGE_SAVE_IS_FILE else request.data["content"]
            return self.update(request)
        else:
            return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行更新操作", })

    @token_verify
    def delete(self, request, *args, **kwargs):
        if kwargs["token_data"]["is_root"]:
            article = ArticleModel.objects.prefetch_related('images').get(id=kwargs.get("pk", ""))
            image_paths = [image.path.path for image in article.images.all()]
            for path in image_paths:
                if os.path.exists(path):
                    os.remove(path)
            return self.destroy(request)
        return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行删除操作", })


class ArticleSummaryViewApi(generics.ListAPIView):
    queryset = ArticleModel.objects.select_related("type").order_by("-release_date")
    serializer_class = ArticleSummarySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["type"]

    def get(self, request, *args, **kwargs):
        now = timezone.now()
        self.queryset = self.queryset.filter(release_date__lt=now)
        if filter_type := self.request.query_params.get("type", None):
            self.queryset = self.queryset.filter(type=filter_type)
        return self.list(request)

    def get_authenticators(self):
        # 在GET请求中，如果未提供JWT令牌，则不执行JWT认证
        if self.request.method == 'GET':
            return []
        return super().get_authenticators()


class ArticleSummaryRootViewApi(generics.ListAPIView):
    queryset = ArticleModel.objects.select_related("type").order_by("-release_date")
    serializer_class = ArticleSummarySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["type"]

    @token_verify
    def get(self, request, *args, **kwargs):
        if filter_type := self.request.query_params.get("type", None):
            self.queryset = self.queryset.filter(type=filter_type)
        return self.list(request)


class ImageViewApi(generics.CreateAPIView, generics.ListAPIView, generics.UpdateAPIView,
                   generics.DestroyAPIView):
    queryset = ImageModel.objects.all()
    serializer_class = ImageSerializer
    pagination_class = None

    def get(self, request, *args, **kwargs):
        return self.list(request)

    @token_verify
    def post(self, request, *args, **kwargs):
        # 创建处理人与处理时间
        if kwargs["token_data"]["is_root"]:
            return self.create(request)
        else:
            return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行创建操作", })

    @token_verify
    def put(self, request, *args, **kwargs):
        if kwargs["token_data"]["is_root"]:
            return self.update(request)
        else:
            return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行更新操作", })

    @token_verify
    def delete(self, request, *args, **kwargs):
        if kwargs["token_data"]["is_root"]:
            return self.destroy(request)
        return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行删除操作", })


class CategoryViewApi(generics.CreateAPIView, generics.ListAPIView, generics.DestroyAPIView, generics.UpdateAPIView):
    queryset = CategoryModel.objects.all()
    serializer_class = CategorySerializer

    def get_authenticators(self):
        # 在GET请求中，如果未提供JWT令牌，则不执行JWT认证
        if self.request.method == 'GET':
            return []
        return super().get_authenticators()

    def get(self, request, *args, **kwargs):
        return self.list(request)

    @token_verify
    def post(self, request, *args, **kwargs):
        # 创建处理人与处理时间
        if kwargs["token_data"]["is_root"]:
            print(request.data)
            request.data["parent"] = request.data["parent"][-1] if isinstance(request.data["parent"], list) else None
            return self.create(request)
        else:
            return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行创建操作", })

    @token_verify
    def put(self, request, *args, **kwargs):
        if kwargs["token_data"]["is_root"]:
            return self.update(request)
        else:
            return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行更新操作", })

    @token_verify
    def delete(self, request, *args, **kwargs):
        if kwargs["token_data"]["is_root"]:
            return self.destroy(request)
        return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行删除操作", })


class CategorySummaryViewApi(generics.ListAPIView):
    queryset = CategoryModel.objects.all()
    serializer_class = CategorySerializer
    # 访问权限类 jwt
    pagination_class = None

    def get_authenticators(self):
        # 在GET请求中，如果未提供JWT令牌，则不执行JWT认证
        if self.request.method == 'GET':
            return []
        return super().get_authenticators()

    def get(self, request, *args, **kwargs):
        return self.list(request)


def page_not_found(request, exception):
    return HttpResponseNotFound(f"页面不存在")


# 后端500处理
def page_error(request):
    return HttpResponseServerError("页面错误")


@token_verify
def delete_unused_files(request: HttpRequest, *args, **kwargs):
    all_image_files_path_set = set()
    article_images_dirs = os.path.join(settings.MEDIA_ROOT, "article_images")
    for article_images_dir in os.listdir(article_images_dirs):
        for image in article_images_dir:
            all_image_files_path_set.add(os.path.join(article_images_dir, image))
    used_image_files_path_set = {os.path.join(settings.MEDIA_ROOT, _.path) for _ in ImageModel.objects.all()}
    unused_files_set = all_image_files_path_set - used_image_files_path_set
    success = len(unused_files_set)
    for unused_file_path in unused_files_set:
        try:
            os.remove(unused_file_path)
        except Exception as e:
            success -= 1
            print(f"删除文件{unused_file_path}失败,报错如下", e)
    return HttpResponse(f"删除未使用文件共计{len(unused_files_set)},成功删除{success}个", status=200)


@token_verify
def get_image_setting(request: HttpRequest, *args, **kwargs):
    print(request.headers)
    return JsonResponse(status=200, data={"image_save_is_file": settings.IMAGE_SAVE_IS_FILE,
                                          "image_compressibility": settings.IMAGE_COMPRESSIBILITY})


@token_verify
@csrf_exempt
def change_image_compressibility(request: HttpRequest, *args, **kwargs):
    image_compressibility = int(json.loads(request.body).get("image_compressibility"))
    # 确保取值在20-100之间
    settings.IMAGE_COMPRESSIBILITY = max(20, min(image_compressibility, 100))
    print(settings.IMAGE_COMPRESSIBILITY)
    return HttpResponse()


@token_verify
@csrf_exempt
def change_image_save_method(request: HttpRequest, *args, **kwargs):
    # 确保取值在20-100之间
    settings.IMAGE_SAVE_IS_FILE = json.loads(request.body).get("image_save_is_file")
    print(settings.IMAGE_SAVE_IS_FILE)
    return HttpResponse()
