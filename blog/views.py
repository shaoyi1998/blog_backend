import base64
import os
import re
from functools import wraps
from io import BytesIO

import jwt
from PIL import Image
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseServerError
from rest_framework import generics
from rest_framework_simplejwt.views import TokenObtainPairView

from blog.models import ArticleModel, ImageModel, CategoryModel
from blog.serializers import ArticleSerializer, ImageSerializer, LoginVerificationSerializer, CategorySerializer, \
    ArticleSummarySerializer
from riyueweiyi import settings


def token_verify(f):
    @wraps(f)
    def warp(self, *args, **kwargs):
        # 如果是生产环境,根据jwt_token验证处理逻辑
        token_data = jwt.decode(str(self.request.auth), key=settings.SIMPLE_JWT["SIGNING_KEY"],
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


def extract_base64_images(title, content, article):
    # 匹配正则
    pattern = '<img.*?src="data:image/[^;]+;base64,([^"]+)".*?>'
    replacement = r'<img src="{}" />'
    for index, match in enumerate(re.findall(pattern, content)):
        image_data = base64.b64decode(match)
        compressed_data = compress_base64_image(image_data, quality=80)
        # 创建 ImageModel 实例
        image = ImageModel(article=article)

        # 保存图像文件
        image_path = 'article_images/{}/{}.jpeg'.format(title, index)  # 假设使用 PNG 格式保存
        image_file = compressed_data
        image.path.save(image_path, image_file)
        # 将文章内容中的 img src 替换为图像的 URL
        replacement_string = replacement.format(image.path.url)
        # 替换 content 中的 img src
        content = re.sub(pattern, replacement_string, content, count=1)
    return content


# Create your views here.

class LoginVerificationApi(TokenObtainPairView):
    serializer_class = LoginVerificationSerializer


class ArticleViewApi(generics.CreateAPIView, generics.ListAPIView, generics.UpdateAPIView,
                     generics.DestroyAPIView):
    queryset = ArticleModel.objects.all()
    serializer_class = ArticleSerializer
    pagination_class = None

    def get(self, request, *args, **kwargs):
        print(kwargs.get("pk", ""))
        if article_id := int(kwargs.get("pk", "")):
            article = ArticleModel.objects.get(id=article_id)
            return JsonResponse(status=200, data={
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "type": article.type.name if article.type else None,
                "release_date": article.release_date
            })
        return self.list(request)

    @token_verify
    def post(self, request, *args, **kwargs):
        # 创建处理人与处理时间
        if kwargs["token_data"]["is_root"]:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            article = serializer.save()
            category = CategoryModel.objects.get(id=request.data["type"][-1])  # 获取ID为20的CategoryModel对象
            article.type = category
            article.content = extract_base64_images(request.data.get("title", "-1"), request.data.get("content", ""),
                                                    article)
            article.save()
            return JsonResponse(status=201, data={'message': '文章上传成功'})
        else:
            return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行创建操作", })

    @token_verify
    def put(self, request, *args, **kwargs):
        if kwargs["token_data"]["is_root"]:
            print(request.data)
            request.data["type"] = int(request.data["type"][-1]) if isinstance(request.data["type"], list) else request.data["type"]
            print(request.data["type"])
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
    queryset = ArticleModel.objects.all()
    serializer_class = ArticleSummarySerializer

    def get(self, request, *args, **kwargs):
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
    pagination_class = None

    def get(self, request, *args, **kwargs):
        return self.list(request)


def page_not_found(request, exception):
    return HttpResponseNotFound(f"页面不存在")


# 后端500处理
def page_error(request):
    return HttpResponseServerError("页面错误")
