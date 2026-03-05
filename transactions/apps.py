from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transactions'

    def ready(self):
        # Registrar señales al iniciar la app
        try:
            import transactions.signals  # registrar signals
        except Exception:
            pass