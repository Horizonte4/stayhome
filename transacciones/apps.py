from django.apps import AppConfig


class TransaccionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transacciones'

    def ready(self):
        # Registrar señales al iniciar la app
        try:
            import transacciones.signals  # registrar signals
        except Exception:
            pass