"""
Auth Views — LearnGraph
Signup with email verification, Login, Logout
"""
import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .models import UserProfile, EmailVerification


# ── SIGNUP ────────────────────────────────────────────────────────────────────
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    error = None
    success = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        # Validation
        if not all([name, email, password, password2]):
            error = "All fields are required."
        elif password != password2:
            error = "Passwords do not match."
        elif password_error(password, User(username=email, email=email)):
            error = password_error(password, User(username=email, email=email))
        elif email_error(email):
            error = 'Enter a valid email address.'
        else:
            # Check if email exists
            existing_user = User.objects.filter(email=email).first() or User.objects.filter(username=email).first()

            if existing_user:
                if existing_user.is_active:
                    # Fully registered — tell them to login
                    error = "This email is already registered. Please sign in."
                else:
                    # Unverified — resend code and let them verify
                    # Resending verification must never replace an existing account's password or identity.

                    # Invalidate old codes
                    EmailVerification.objects.filter(user=existing_user, is_used=False).update(is_used=True)

                    # Send new code
                    code = EmailVerification.generate_code()
                    EmailVerification.objects.create(user=existing_user, code=code)
                    _send_verification_email(existing_user, code)

                    request.session['pending_verification_email'] = email
                    return redirect('verify_email')
            else:
                # New user — create
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=name.split()[0],
                    last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                )
                user.is_active = False  # Inactive until email verified
                user.save()

                # Create profile
                UserProfile.objects.create(user=user, is_email_verified=False)

                # Generate & send verification code
                code = EmailVerification.generate_code()
                EmailVerification.objects.create(user=user, code=code)
                _send_verification_email(user, code)

                request.session['pending_verification_email'] = email
                return redirect('verify_email')

    return render(request, 'learning/auth/signup.html', {'error': error, 'success': success})


# ── EMAIL VERIFICATION ────────────────────────────────────────────────────────
def verify_email_view(request):
    email = request.session.get('pending_verification_email')
    if not email:
        return redirect('signup')

    error = None
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return redirect('signup')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()

        verification = EmailVerification.objects.filter(
            user=user, code=code, is_used=False
        ).last()

        if not verification:
            error = "Invalid code. Please check your email."
        elif not verification.is_valid():
            error = "Code has expired. Please request a new one."
        else:
            # Mark verified
            verification.is_used = True
            verification.save()

            user.is_active = True
            user.save()

            profile = user.profile
            profile.is_email_verified = True
            profile.save()

            # Auto login
            del request.session['pending_verification_email']
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')

    return render(request, 'learning/auth/verify.html', {
        'email': email,
        'error': error,
    })


@require_POST
def resend_code_view(request):
    """Resend verification code."""
    email = request.session.get('pending_verification_email')
    if not email:
        return redirect('signup')

    try:
        user = User.objects.get(email=email)
        # Invalidate old codes
        EmailVerification.objects.filter(user=user, is_used=False).update(is_used=True)

        # New code
        code = EmailVerification.generate_code()
        EmailVerification.objects.create(user=user, code=code)
        _send_verification_email(user, code)

    except User.DoesNotExist:
        pass

    return redirect('verify_email')


# ── LOGIN ─────────────────────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    error = None

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # Superusers created in the terminal often have a username different
        # from their email. Resolve a unique email without bypassing auth.
        candidates = list(User.objects.filter(email__iexact=email)[:2])
        username = candidates[0].get_username() if len(candidates) == 1 else email
        user = authenticate(request, username=username, password=password) if len(candidates) < 2 else None

        if user is None:
            # Check if email exists but not verified
            try:
                u = User.objects.get(email=email)
                if not u.is_active and u.check_password(password):
                    request.session['pending_verification_email'] = email
                    # Resend code
                    code = EmailVerification.generate_code()
                    EmailVerification.objects.filter(user=u, is_used=False).update(is_used=True)
                    EmailVerification.objects.create(user=u, code=code)
                    _send_verification_email(u, code)
                    return redirect('verify_email')
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
            error = "Invalid email or password."
        else:
            login(request, user)
            from academy.access import is_teacher
            if request.user.is_superuser:
                return redirect('portal_home')
            if is_teacher(request.user):
                return redirect('academy_dashboard')
            next_url = request.GET.get('next', '/')
            return redirect(next_url if url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()) else '/')

    return render(request, 'learning/auth/login.html', {'error': error})


# ── LOGOUT ────────────────────────────────────────────────────────────────────
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


# ── EMAIL HELPER ──────────────────────────────────────────────────────────────
def _send_verification_email(user, code):
    """Send 6-digit verification code to user email."""
    subject = "LearnGraph AI — Email Verification Code"
    message = f"""Hi {user.first_name or user.username},

Your LearnGraph AI verification code is:

    {code}

This code expires in {getattr(settings, 'VERIFICATION_CODE_EXPIRY', 10)} minutes.

If you did not sign up, ignore this email.

— LearnGraph AI Team
"""

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
    except Exception:
        # Never log credentials, verification codes, or provider exception bodies.
        import logging
        logging.getLogger(__name__).warning('Verification email delivery failed.')


def password_error(password, user):
    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        return ' '.join(exc.messages)
    return None


def email_error(email):
    try:
        validate_email(email)
        return len(email) > 150
    except ValidationError:
        return True


# ── ACCOUNT SETTINGS ──────────────────────────────────────────────────────────
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def account_view(request):
    """Account settings page."""
    error = None
    success = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            success = "Profile updated successfully."

        elif action == 'change_password':
            current_pw = request.POST.get('current_password', '')
            new_pw = request.POST.get('new_password', '')
            confirm_pw = request.POST.get('confirm_password', '')

            if not request.user.check_password(current_pw):
                error = "Current password is incorrect."
            elif password_error(new_pw, request.user):
                error = password_error(new_pw, request.user)
            elif new_pw != confirm_pw:
                error = "Passwords do not match."
            else:
                request.user.set_password(new_pw)
                request.user.save()
                # Re-login after password change
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                success = "Password changed successfully."

    return render(request, 'learning/auth/account.html', {
        'error': error,
        'success': success,
        'page': 'account',
    })


@login_required
def delete_account_view(request):
    """Delete account — requires password confirmation."""
    error = None

    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm', '')

        if confirm != 'DELETE':
            error = "Please type DELETE to confirm."
        elif not request.user.check_password(password):
            error = "Incorrect password."
        else:
            user = request.user
            from django.db.models.deletion import ProtectedError
            try:
                user.delete()
            except ProtectedError:
                error = 'This teaching account owns classes or protected records. Ask an administrator to reassign them before deleting the account.'
            else:
                logout(request)
                return redirect('signup')

    return render(request, 'learning/auth/delete_account.html', {
        'error': error,
    })
