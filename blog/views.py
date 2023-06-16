from functools import wraps

import jwt
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseServerError
from rest_framework import generics

from blog.models import ArticleModel, ImageModel
from blog.serializers import ArticleSerializer, ImageSerializer
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


# Create your views here.

class ArticleViewApi(generics.CreateAPIView, generics.ListAPIView, generics.UpdateAPIView,
                     generics.DestroyAPIView):
    queryset = ArticleModel.objects.all()
    serializer_class = ArticleSerializer
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

    def put(self, request, *args, **kwargs):
        if kwargs["token_data"]["is_root"]:
            return self.update(request)
        else:
            return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行更新操作", })

    def delete(self, request, *args, **kwargs):
        if kwargs["token_data"]["is_root"]:
            return self.destroy(request)
        return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行删除操作", })


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

    def put(self, request, *args, **kwargs):
        if kwargs["token_data"]["is_root"]:
            return self.update(request)
        else:
            return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行更新操作", })

    def delete(self, request, *args, **kwargs):
        if kwargs["token_data"]["is_root"]:
            return self.destroy(request)
        return JsonResponse(status=403, data={"错误编码": 403, "原因": "无权执行删除操作", })


def page_not_found(request, exception):
    return HttpResponseNotFound(f"页面不存在")


# 后端500处理
def page_error(request):
    return HttpResponseServerError("页面错误")
