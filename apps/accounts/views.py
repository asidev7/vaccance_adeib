from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def comite_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff_comite and user.est_actif:
            login(request, user)
            return redirect('core_comite:dashboard_comite')
        else:
            messages.error(request, 'Identifiants invalides ou accès non autorisé.')
    return render(request, 'comite/login.html')


def comite_logout(request):
    logout(request)
    return redirect('core:accueil')


def enseignant_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'enseignant' and user.est_actif:
            login(request, user)
            return redirect('enseignant:dashboard')
        else:
            messages.error(request, 'Identifiants invalides ou accès non autorisé.')
    return render(request, 'enseignant/login.html')


def enseignant_logout(request):
    logout(request)
    return redirect('core:accueil')
