# from django.shortcuts import render
import re

from rest_framework.exceptions import Throttled
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import viewsets, generics, status, permissions, views
from rest_framework.decorators import action, throttle_classes
from rest_framework.response import Response

from . import throttle
from .models import *
from .serializers import *
from .paginator import BasePaginator, CustomCommentPagination
from django.http import Http404
from django.conf import settings
from django.db.models import F  # Suport view lesson
from func_Handle.handle_Input import no_accent_vietnamese
from courses.throttle import UserLoginRateThrottle

# https://www.youtube.com/watch?v=yPl5VTB7tDk&list=PLlVHoHHccp2_kuKovosZTK_Ftu6XwgFyH&index=5&t=1277s phut 34:00


# Create your views here.

# class LoginView(oauth2_views):
#

# Captcha
import requests
from rest_framework.decorators import api_view


@api_view(['post'])
@throttle_classes([UserLoginRateThrottle])
def log_out(request):
    content = {
        'status': 'request was permitted'
    }
    return Response(content)


@api_view(['POST'])
def recaptcha(request):
    r = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={
            'secret': '6Ldir2IgAAAAAD3BbhUbO4GRbKn4jxl1WQZ5OXtk',
            'response': request.data['captcha_value'],
        }
    )

    return Response({'captcha': r.json()})


# API View

class UserAPIView(viewsets.ViewSet, generics.CreateAPIView):
    parser_classes = [MultiPartParser, FormParser]
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer

    # throttle_classes = (UserRegisterRateThrottle,)

    # FIXME: Bị bug không nhận được dữ liệu ảnh, đã fix được bên serializers.py nhưng vẫn để đoạn code này làm kỷ niêm

    # def create(self, request, *args, **kwargs):
    #     username = request.data.get('username')
    #     password = request.data.get('password')
    #     email = request.data.get('email')
    #     first_name = request.data.get('first_name')
    #     last_name = request.data.get('last_name')
    #     avatar = request.data.get('avatar')
    #     user = User(username=username, password=password, avatar=avatar)
    #     user.set_password(user.password)
    # user.save()
    # return Response(self.serializer_class(user, context={"request": request}).data,
    #                 status=status.HTTP_200_OK)
    # TODO: Đoạn code trên cũng có thể fix được lỗi nhận dữ liệu file ảnh nhưng dùng bên serializers.py sẽ gọn gàng hơn

    # def get_throttles(self):
    #     if self.action == 'create':
    #         return (UserRegisterRateThrottle(),)
    #     else:
    #         return []

    def get_permissions(self):
        # print(self.action)
        if self.action == 'get_current_user':
            return [permissions.IsAuthenticated()]
        else:
            return [permissions.AllowAny()]

    @action(methods=['get'], detail=False, url_path='current-user')
    def get_current_user(self, request):
        return Response(self.serializer_class(request.user, context={"request": request}).data,
                        status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='check-exist-user')
    def check_user_exist(self, request):
        # print(request.headers.get('username'))
        username = request.headers.get('username')
        if User.objects.filter(username=username):
            return Response(data='exist', status=status.HTTP_200_OK)
        else:
            return Response(data='not exist', status=status.HTTP_200_OK)

    # def perform_create(self, serializer):
    #     user = serializer.save()
    #
    # def throttled(self, request, wait):
    #     raise Throttled(detail={
    #         "message": "recaptcha_required",
    #     })


class AuthInfoView(views.APIView):
    def get(self, request):
        return Response(settings.OAUTH2_INFO, status=status.HTTP_200_OK)
        # return Response("Hello")


class CategoryAPIView(viewsets.ViewSet, generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CoursesAPIView(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = CourseSerializer
    pagination_class = BasePaginator

    def get_queryset(self):
        courses = Courses.objects.filter(active=True)
        q = self.request.query_params.get('q')
        # q = no_accent_vietnamese(q)

        if q is not None:
            custom_list = [course.id for course in courses if
                           re.search(no_accent_vietnamese(q).lower(), no_accent_vietnamese(course.subject).lower())]
            courses = courses.filter(id__in=custom_list)

            # courses = courses.filter(subject__icontains=q)
            # Neu la icontains thi khong phan biet hoa thuong
        cate_id = self.request.query_params.get('category_id')
        if cate_id is not None:
            courses = courses.filter(category_id=cate_id)
        return courses

    @action(methods=['get', ], detail=True, url_path='lessons')
    def get_lessons(self, request, pk):
        # course = self.get_object()
        # course = Courses.objects.get(pk=pk)
        lessons = Courses.objects.get(pk=pk).lessons.filter(active=True)
        query = self.request.query_params.get('q')

        if query is not None:
            # lessons.forEach(self.subject == query)
            lessons = lessons.filter(subject__icontains=query)
        return Response(LessonSerializer(lessons, many=True, context={"request": request}).data,
                        status=status.HTTP_200_OK)


class LessonAPIView(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = Lesson.objects.filter(active=True)
    serializer_class = LessonDetailSerializer

    # permission_classes =  []
    # pagination_class = []
    def get_permissions(self):
        if self.action in ['add_comment', 'take_action', 'rating']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    # def get_paginated_response(self, data):
    #     if self.action == 'get_comment':
    #         return [BasePaginator]

    @action(methods=['post', ], detail=True, url_path='tags')
    def get_or_creat_tags(self, request, pk):
        try:
            lesson = self.get_object()
        except Http404:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            tags = self.request.data.get('tags')
            if tags is not None:
                for tag in tags:
                    t, _ = Tag.objects.get_or_create(name=tag)
                    lesson.tags.add(t)
                lesson.save()
                return Response(data=LessonDetailSerializer(lesson).data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=True, url_path='add-comment')
    def add_comment(self, request, pk):
        content = request.data.get('content')
        if content:
            c = Comment.objects.create(content=content, lesson=self.get_object(), creator=request.user)
            # return Response(data=CommentSerializer(c).data, status=status.HTTP_201_CREATED)
            return Response(CommentSerializer(c, context={"request": request}).data,
                            status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=True, url_path='comments')
    def get_comment(self, request, pk):
        paginator = BasePaginator()
        paginator.page_size = 10
        lesson = self.get_object()
        query = lesson.comment_set.order_by("-id").all()
        result_page = paginator.paginate_queryset(query, self.request)
        serializers = CommentSerializer(result_page, many=True, context={"request": self.request})
        return paginator.get_paginated_response(serializers.data)

        # --------------------------------------------------------

        # l = self.get_object()
        # return Response(
        #     CommentSerializer(l.comment_set.order_by("-id").all(), many=True, context={"request": self.request}).data,
        #     status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='like')
    def take_action(self, request, pk):
        try:
            action_type = int(request.data.get('type'))
        except IndexError | ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            lesson = self.get_object()
            action = Action.objects.create(lesson=lesson, type=action_type, creator=request.user)
            return Response(ActionSerializer(action).data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=True, url_path='rating')
    def rating(self, request, pk):
        try:
            rate = int(request.data.get('rating'))
        except IndexError | ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            lesson = self.get_object()
            rating = Action.objects.create(lesson=lesson, rate=rate, creator=request.user)
            return Response(RatingSerializer(rating).data, status=status.HTTP_201_CREATED)

    @action(methods=['get'], detail=True, url_path='view')
    def inc_view(self, request, pk):
        v, created = LessonView.objects.get_or_create(lesson=self.get_object())
        v.view = F('view') + 1
        v.save()
        v.refresh_from_db()
        return Response(LessonViewSerializer(v).data, status=status.HTTP_200_OK)


class CommentAPIView(viewsets.ViewSet, generics.DestroyAPIView, generics.UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        if request.user == self.get_object().creator:
            super().destroy(request, *args, **kwargs)
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, *args, **kwargs):
        if request.user == self.get_object().creator:
            return super().partial_update(request, *args, **kwargs)
        return Response(status=status.HTTP_403_FORBIDDEN)
