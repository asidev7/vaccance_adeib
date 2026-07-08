from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def staff_comite_required(view_func=None, login_url='/comite/login/'):
    """Decorator for all comité staff (admin, tresorier, secretaire)."""
    def check_role(user):
        if not user.is_authenticated:
            return False
        if not user.is_staff_comite:
            raise PermissionDenied("Accès réservé aux membres du comité.")
        return True
    actual_decorator = user_passes_test(check_role, login_url=login_url)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def admin_required(view_func=None, login_url='/comite/login/'):
    """Decorator for admin only."""
    def check_role(user):
        if not user.is_authenticated:
            return False
        if not user.is_admin:
            raise PermissionDenied("Accès réservé à l'administrateur.")
        return True
    actual_decorator = user_passes_test(check_role, login_url=login_url)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def tresorier_required(view_func=None, login_url='/comite/login/'):
    """Decorator for admin + tresorier."""
    def check_role(user):
        if not user.is_authenticated:
            return False
        if not user.is_tresorier:
            raise PermissionDenied("Accès réservé à l'administrateur et au trésorier.")
        return True
    actual_decorator = user_passes_test(check_role, login_url=login_url)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def secretaire_required(view_func=None, login_url='/comite/login/'):
    """Decorator for admin + secretaire."""
    def check_role(user):
        if not user.is_authenticated:
            return False
        if not user.is_secretaire:
            raise PermissionDenied("Accès réservé à l'administrateur et au secrétaire.")
        return True
    actual_decorator = user_passes_test(check_role, login_url=login_url)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def enseignant_required(view_func=None, login_url='/enseignant/login/'):
    """Decorator for enseignants only."""
    def check_role(user):
        if not user.is_authenticated:
            return False
        if user.role != 'enseignant':
            raise PermissionDenied("Accès réservé aux enseignants.")
        return True
    actual_decorator = user_passes_test(check_role, login_url=login_url)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator
