from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
class Command(BaseCommand):
    help = 'Create a Teacher group with course-content permissions only.'
    def handle(self,*args,**kwargs):
        group,_=Group.objects.get_or_create(name='Teacher')
        group.permissions.clear()  # Teachers use the scoped portal, not global model permissions.
        self.stdout.write('Teacher role ready. A superuser can grant staff status and assign this group.')
