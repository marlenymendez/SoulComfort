from django.apps import AppConfig

class MiappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'miapp'

    def ready(self):
        from django.contrib.auth.models import User
        from miapp.models import UserProfile
        from django.db.utils import OperationalError

        try:
            if not User.objects.filter(username="admin").exists():
                user = User.objects.create_superuser(
                    username="admin",
                    password="1234"
                )
                profile = UserProfile.objects.get(user=user)
                profile.tipo_usuario = "admin"
                profile.save()
               
        except OperationalError:
            pass