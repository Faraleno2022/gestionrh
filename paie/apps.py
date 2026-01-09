from django.apps import AppConfig


class PaieConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'paie'
    verbose_name = 'Gestion de la paie'
    
    def ready(self):
        import paie.signals  # noqa
