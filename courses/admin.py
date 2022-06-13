from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Category)
admin.site.register(Courses)
admin.site.register(Lesson)
admin.site.register(Tag)
admin.site.register(Comment)
admin.site.register(User)