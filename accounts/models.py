from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    # oneToOne is foreignkey and unique index
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    avatar = models.FileField(null=True)
    nickname = models.CharField(null=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.user, self.nickname)


# 定义一个返回profile的property方法，植入到user类中去
# 这样可以通过user实例来直接访问与之关联的profile
# 对User进行hack，更方便快捷的访问profile，可以常用于OneToOne结构中
def get_profile(user: User):
    # 基于user实例的profile缓存，对同一个user.profile多次操作时只需要访问一次数据库就好
    # 这种对于实例的一个属性的cache，可以避免多次profile访问时造成的多次数据库查询
    if hasattr(user, '_cached_user_profile'):
        return getattr(user, '_cached_user_profile')
    profile, _ = UserProfile.objects.get_or_create(user=user)
    setattr(user, '_cached_user_profile', profile)
    return profile


# 为django内置的User增加了一个profile property，在project运行起来时就会执行这一句
User.profile = property(get_profile)

