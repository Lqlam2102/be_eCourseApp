from django.urls import path, include
from rest_framework import routers
from .views import CategoryAPIView, CoursesAPIView, LessonAPIView, UserAPIView, AuthInfoView, CommentAPIView , recaptcha

routers = routers.DefaultRouter()
routers.register('categories', CategoryAPIView, 'category')
routers.register('courses', CoursesAPIView, 'course')
routers.register('lessons', LessonAPIView, 'lesson')
routers.register('users', UserAPIView, 'user')
routers.register('comment', CommentAPIView, 'comment')
urlpatterns = [
    path('', include(routers.urls)),
    path('oauth2-info/', AuthInfoView.as_view()),
    path('recaptcha/', recaptcha)
]
