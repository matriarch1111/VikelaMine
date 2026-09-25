from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
def home(r): return render(r, 'core/home.html')
def summaries(r): return render(r, 'core/summaries.html')
def reports(r): return render(r, 'core/reports.html')
def near_danger(r): return render(r, 'core/reports.html')
def maps(r): return render(r, 'core/summaries.html')
def contact(r): return render(r, 'core/home.html')
def add_report(r): return render(r, 'core/add_report.html')
def settings_page(r): return render(r, 'core/settings.html')
def report_hazard(r): 
    if r.method=='POST': print(r.POST.dict()); return redirect('/reports/')
    return redirect('/')
def sos_alert(r): return JsonResponse({"ok":1})
def forgot_password(r); return render(r, 'core/forgot_password.html')