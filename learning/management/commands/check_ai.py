from django.core.management.base import BaseCommand, CommandError
from learning.ai_engine import _call
from learning.ai_errors import explain_error

class Command(BaseCommand):
    help = 'Make one small AI request without displaying keys or provider error bodies.'
    def handle(self, *args, **options):
        try:
            result = _call('Reply briefly.', 'Say OK.', max_tokens=1024)
            if not result:
                raise ValueError('Empty response')
        except Exception as exc:
            raise CommandError(explain_error(exc)) from None
        self.stdout.write(self.style.SUCCESS('AI connection successful.'))
