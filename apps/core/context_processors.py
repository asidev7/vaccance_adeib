from .models import SessionVacances


def session_active(request):
    """Add the active session to all template contexts."""
    session = SessionVacances.objects.filter(est_active=True).first()
    return {
        'session_active': session,
    }
