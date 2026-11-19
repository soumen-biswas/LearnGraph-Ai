from django.contrib.auth.models import User, Group
from django.core.cache import cache
from django.test import TestCase


class RoleNavigationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin=User.objects.create_superuser('owner','owner@example.com','Test-password-234!')
        self.teacher=User.objects.create_user('instructor',email='teacher@example.com',password='Test-password-234!',is_staff=True)
        group=Group.objects.create(name='Teacher');self.teacher.groups.add(group)
        self.student=User.objects.create_user('learner',email='student@example.com',password='Test-password-234!')

    def test_login_destinations_with_email(self):
        for user, target in [(self.admin,'/manage/'),(self.teacher,'/teach/'),(self.student,'/')]:
            self.client.logout()
            response=self.client.post('/auth/login/',{'email':user.email,'password':'Test-password-234!'})
            self.assertRedirects(response,target,fetch_redirect_response=False)

    def test_root_redirects_and_role_menus(self):
        for user,target in [(self.admin,'/manage/'),(self.teacher,'/teach/')]:
            self.client.force_login(user)
            self.assertRedirects(self.client.get('/'),target,fetch_redirect_response=False)
            response=self.client.get(target)
            for link in ['href="/quiz/"','href="/chat/"','href="/assessments/"','href="/completion/"']:
                self.assertNotContains(response,link)
        self.client.force_login(self.student)
        response=self.client.get('/')
        self.assertContains(response,'href="/quiz/"')
        self.assertNotContains(response,'href="/manage/"')

    def test_staff_next_cannot_override_landing(self):
        response=self.client.post('/auth/login/?next=/quiz/',{'email':self.admin.email,'password':'Test-password-234!'})
        self.assertRedirects(response,'/manage/',fetch_redirect_response=False)

    def test_student_external_next_rejected(self):
        response=self.client.post('/auth/login/?next=https://evil.example/',{'email':self.student.email,'password':'Test-password-234!'})
        self.assertRedirects(response,'/',fetch_redirect_response=False)

    def test_wrong_password_and_duplicate_email_rejected(self):
        self.client.post('/auth/login/',{'email':self.admin.email,'password':'wrong'})
        self.assertNotIn('_auth_user_id',self.client.session)
        User.objects.create_user('duplicate',email=self.admin.email,password='Test-password-234!')
        self.client.post('/auth/login/',{'email':self.admin.email,'password':'Test-password-234!'})
        self.assertNotIn('_auth_user_id',self.client.session)
