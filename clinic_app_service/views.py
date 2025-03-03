# views.py
from django.shortcuts import render, redirect
from .models import MedicalRecord
from .forms import MedicalRecordForm

def index(request):
    medi = MedicalRecord.objects.all()
    form = MedicalRecordForm()
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')  # або на іншу сторінку
    return render(request, 'index.html', {'medi': medi, 'form': form})