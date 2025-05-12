from django.apps import AppConfig


class NonmemberConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nonMember'
