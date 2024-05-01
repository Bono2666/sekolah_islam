from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import connection, IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.forms.models import modelformset_factory
from apps.forms import *
from apps.mail import send_email
from apps.models import *
from authentication.decorators import role_required
from tablib import Dataset
from django.utils import timezone
import xlwt
from django.http import HttpResponse
import xlsxwriter
from django.db.models import Sum
from django.db.models import Max
from django.db.models import Min
from . import host
from reportlab.pdfgen import canvas
from django.http import FileResponse
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4
from django.db.models import Count
from PyPDF2 import PdfMerger
from django.conf import settings
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.utils.text import Truncator
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from crum import get_current_user


@login_required(login_url='/login/')
def home(request):
    context = {
        'segment': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
    }
    return render(request, 'home/index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, email, position_name FROM apps_user INNER JOIN apps_position ON apps_user.position_id = apps_position.position_id")
        users = cursor.fetchall()

    context = {
        'data': users,
        'segment': 'user',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/user_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_add(request):
    position = Position.objects.all()
    if request.POST:
        form = FormUser(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            if not settings.DEBUG and form.instance.signature:
                user = User.objects.get(user_id=form.instance.user_id)
                my_file = user.signature
                filename = '../../www/aqiqahon/apps/media/' + my_file.name
                with open(filename, 'wb+') as temp_file:
                    for chunk in my_file.chunks():
                        temp_file.write(chunk)

            return HttpResponseRedirect(reverse('user-view', args=[form.instance.user_id, ]))
        else:
            message = form.errors
            context = {
                'form': form,
                'position': position,
                'segment': 'user',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/user_add.html', context)
    else:
        form = FormUser()
        context = {
            'form': form,
            'position': position,
            'segment': 'user',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/user_add.html', context)


# View User
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_view(request, _id):
    users = User.objects.get(user_id=_id)
    auth = Auth.objects.filter(user_id=_id)
    area = AreaUser.objects.filter(user_id=_id)
    form = FormUserView(instance=users)
    position = Position.objects.all()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_menu.menu_id, menu_name, q_auth.menu_id FROM apps_menu LEFT JOIN (SELECT * FROM apps_auth WHERE user_id = '" + str(_id) + "') AS q_auth ON apps_menu.menu_id = q_auth.menu_id WHERE q_auth.menu_id IS NULL")
        menu = cursor.fetchall()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_areasales.area_id, area_name, q_area.area_id FROM apps_areasales LEFT JOIN (SELECT * FROM apps_areauser WHERE user_id = '" + str(_id) + "') AS q_area ON apps_areasales.area_id = q_area.area_id WHERE q_area.area_id IS NULL")
        item_area = cursor.fetchall()

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in menu:
            if str(i[0]) in check:
                try:
                    auth = Auth(user_id=_id, menu_id=i[0])
                    auth.save()
                except IntegrityError:
                    continue
            else:
                Auth.objects.filter(user_id=_id, menu_id=i[0]).delete()

        return HttpResponseRedirect(reverse('user-view', args=[_id, ]))

    context = {
        'form': form,
        'formAuth': form,
        'data': users,
        'auth': auth,
        'menu': menu,
        'area': area,
        'item_area': item_area,
        'positions': position,
        'segment': 'user',
        'group_segment': 'master',
        'tab': 'auth',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_view.html', context)


# View User Area
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_area_view(request, _id):
    users = User.objects.get(user_id=_id)
    auth = Auth.objects.filter(user_id=_id)
    area = AreaUser.objects.filter(user_id=_id)
    form = FormUserView(instance=users)
    position = Position.objects.all()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_menu.menu_id, menu_name, q_auth.menu_id FROM apps_menu LEFT JOIN (SELECT * FROM apps_auth WHERE user_id = '" + str(_id) + "') AS q_auth ON apps_menu.menu_id = q_auth.menu_id WHERE q_auth.menu_id IS NULL")
        menu = cursor.fetchall()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_areasales.area_id, area_name, q_area.area_id FROM apps_areasales LEFT JOIN (SELECT * FROM apps_areauser WHERE user_id = '" + str(_id) + "') AS q_area ON apps_areasales.area_id = q_area.area_id WHERE q_area.area_id IS NULL")
        item_area = cursor.fetchall()

    if request.POST:
        area_check = request.POST.getlist('area[]')
        for i in item_area:
            if str(i[0]) in area_check:
                try:
                    area = AreaUser(user_id=_id, area_id=i[0])
                    area.save()
                except IntegrityError:
                    continue
            else:
                AreaUser.objects.filter(user_id=_id, area_id=i[0]).delete()

        return HttpResponseRedirect(reverse('user-area-view', args=[_id, ]))

    context = {
        'form': form,
        'formAuth': form,
        'data': users,
        'auth': auth,
        'menu': menu,
        'area': area,
        'item_area': item_area,
        'positions': position,
        'segment': 'user',
        'group_segment': 'master',
        'tab': 'area',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_view.html', context)


# Update Auth
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def auth_update(request, _id, _menu):
    auth = Auth.objects.get(user=_id, menu=_menu)

    if request.POST:
        auth.add = 1 if request.POST.get('add') else 0
        auth.edit = 1 if request.POST.get('edit') else 0
        auth.delete = 1 if request.POST.get('delete') else 0
        auth.save()

        return HttpResponseRedirect(reverse('user-view', args=[_id, ]))

    return render(request, 'home/user_view.html')


# Delete Auth
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def auth_delete(request, _id, _menu):
    auth = Auth.objects.filter(user=_id, menu=_menu)

    auth.delete()
    return HttpResponseRedirect(reverse('user-view', args=[_id, ]))


# Delete AreaUser
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def area_user_delete(request, _id, _area):
    area = AreaUser.objects.filter(user=_id, area=_area)

    area.delete()
    return HttpResponseRedirect(reverse('user-area-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def remove_signature(request, _id):
    users = User.objects.get(user_id=_id)
    users.signature = None
    users.save()
    return HttpResponseRedirect(reverse('user-view', args=[_id, ]))


# Update User
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_update(request, _id):
    users = User.objects.get(user_id=_id)
    position = Position.objects.all()
    auth = Auth.objects.filter(user_id=_id)
    area = AreaUser.objects.filter(user_id=_id)

    if request.POST:
        form = FormUserUpdate(request.POST, request.FILES, instance=users)
        if form.is_valid():
            form.save()
            if not settings.DEBUG and users.signature:
                my_file = users.signature
                filename = '../../www/aqiqahon/apps/media/' + my_file.name
                with open(filename, 'wb+') as temp_file:
                    for chunk in my_file.chunks():
                        temp_file.write(chunk)
            return HttpResponseRedirect(reverse('user-view', args=[_id, ]))
    else:
        form = FormUserUpdate(instance=users)

    message = form.errors
    context = {
        'form': form,
        'data': users,
        'positions': position,
        'auth': auth,
        'area': area,
        'segment': 'user',
        'group_segment': 'master',
        'crud': 'update',
        'tab': 'auth',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_view.html', context)


# Delete User
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_delete(request, _id):
    users = User.objects.get(user_id=_id)

    users.delete()
    return HttpResponseRedirect(reverse('user-index'))


@login_required(login_url='/login/')
def change_password(request):
    if request.POST:
        form = FormChangePassword(data=request.POST, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return HttpResponseRedirect(reverse('home'))
    else:
        form = FormChangePassword(user=request.user)

    message = form.errors
    context = {
        'form': form,
        'data': request.user,
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
    }
    return render(request, 'home/user_change_password.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def set_password(request, _id):
    users = User.objects.get(user_id=_id)
    if request.POST:
        form = FormSetPassword(data=request.POST, user=users)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return HttpResponseRedirect(reverse('user-view', args=[_id, ]))
    else:
        form = FormSetPassword(user=users)

    message = form.errors
    context = {
        'form': form,
        'data': users,
        'segment': 'user',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_set_password.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DISTRIBUTOR')
def distributor_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT distributor_id, distributor_name, sap_code FROM apps_distributor")
        distributors = cursor.fetchall()

    context = {
        'data': distributors,
        'segment': 'distributor',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='DISTRIBUTOR') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/distributor_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DISTRIBUTOR')
def distributor_add(request):
    if request.POST:
        form = FormDistributor(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('distributor-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'distributor',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='DISTRIBUTOR') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/distributor_add.html', context)
    else:
        form = FormDistributor()
        context = {
            'form': form,
            'segment': 'distributor',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='DISTRIBUTOR') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/distributor_add.html', context)


# View Distributor
@login_required(login_url='/login/')
@role_required(allowed_roles='DISTRIBUTOR')
def distributor_view(request, _id):
    distributors = Distributor.objects.get(distributor_id=_id)
    form = FormDistributorView(instance=distributors)

    context = {
        'form': form,
        'data': distributors,
        'segment': 'distributor',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='DISTRIBUTOR') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/distributor_view.html', context)


# Update Distributor
@login_required(login_url='/login/')
@role_required(allowed_roles='DISTRIBUTOR')
def distributor_update(request, _id):
    distributors = Distributor.objects.get(distributor_id=_id)
    if request.POST:
        form = FormDistributorUpdate(
            request.POST, request.FILES, instance=distributors)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('distributor-view', args=[_id, ]))
    else:
        form = FormDistributorUpdate(instance=distributors)

    message = form.errors
    context = {
        'form': form,
        'data': distributors,
        'segment': 'distributor',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='DISTRIBUTOR') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/distributor_view.html', context)


# Delete Distributor
@login_required(login_url='/login/')
@role_required(allowed_roles='DISTRIBUTOR')
def distributor_delete(request, _id):
    distributors = Distributor.objects.get(distributor_id=_id)

    distributors.delete()
    return HttpResponseRedirect(reverse('distributor-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='AREA')
def area_sales_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT area_id, area_name, username FROM apps_areasales INNER JOIN apps_user ON apps_areasales.manager = apps_user.user_id")
        area_sales = cursor.fetchall()

    context = {
        'data': area_sales,
        'segment': 'area_sales',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='AREA') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/area_sales_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='AREA')
def area_sales_add(request):
    AreaSalesDetailFormSet = modelformset_factory(
        AreaSalesDetail, form=FormAreaSalesDetail, extra=0, can_delete=True, can_delete_extra=True)
    distributor = Distributor.objects.all()
    manager = User.objects.filter(position_id='ASM')

    if request.POST:
        form = FormAreaSales(request.POST, request.FILES)
        formset = AreaSalesDetailFormSet(
            request.POST, queryset=AreaSalesDetail.objects.none())

        if form.is_valid():
            new = form.save(commit=False)
            new.area_id = form.cleaned_data.get('area_id').replace(' ', '')
            new.form = host.url + 'order/new/' + new.area_id
            new.save()
            return HttpResponseRedirect(reverse('area-sales-view', args=[form.instance.area_id, ]))
        # if all([form.is_valid(), formset.is_valid()]):
        #     try:
        #         parent = form.save(commit=False)
        #         parent.save()
        #         for form in formset:
        #             if form.cleaned_data.get('distributor') is None:
        #                 if form.cleaned_data.get('DELETE'):
        #                     continue
        #                 else:
        #                     continue
        #             else:
        #                 if form.cleaned_data.get('DELETE'):
        #                     form.instance.delete()
        #                     continue

        #             child = form.save(commit=False)
        #             child.area = parent
        #             child.save()
        #         return HttpResponseRedirect(reverse('area-sales-index'))
        #     except Exception:
        #         return HttpResponseRedirect(reverse('area-sales-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'manager': manager,
                'segment': 'area_sales',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'distributors': distributor,
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='AREA') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/area_sales_add.html', context)
    else:
        form = FormAreaSales()
        formset = AreaSalesDetailFormSet(
            queryset=AreaSalesDetail.objects.none())

        message = form.errors
        context = {
            'form': form,
            'manager': manager,
            'formset': formset,
            'segment': 'area_sales',
            'group_segment': 'master',
            'crud': 'add',
            'message': message,
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'distributors': distributor,
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='AREA') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/area_sales_add.html', context)


# View Area Sales
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA')
def area_sales_view(request, _id):
    area_sales = AreaSales.objects.get(area_id=_id)
    AreaSalesDetailFormSet = modelformset_factory(
        AreaSalesDetail, form=FormAreaSalesDetailView, extra=0)
    qs = area_sales.areasalesdetail_set.all()
    form = FormAreaSalesView(instance=area_sales)
    formset = AreaSalesDetailFormSet(queryset=qs)
    detail = AreaSalesDetail.objects.filter(area_id=_id)
    managers = User.objects.filter(position_id='ASM')
    # distributor = Distributor.objects.all()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_distributor.distributor_id, distributor_name, q_distributor.distributor_id FROM apps_distributor LEFT JOIN (SELECT * FROM apps_areasalesdetail WHERE area_id = '" + str(_id) + "') AS q_distributor ON apps_distributor.distributor_id = q_distributor.distributor_id WHERE q_distributor.distributor_id IS NULL")
        distributor = cursor.fetchall()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT area_id, area_name, username FROM apps_areasales INNER JOIN apps_user ON apps_areasales.manager = apps_user.user_id WHERE area_id = '" + str(_id) + "'")
        areas = cursor.fetchall()

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in distributor:
            if str(i[0]) in check:
                try:
                    detail = AreaSalesDetail(area_id=_id, distributor_id=i[0])
                    detail.save()
                except IntegrityError:
                    continue
            else:
                AreaSalesDetail.objects.filter(
                    area_id=_id, distributor_id=i[0]).delete()
        return HttpResponseRedirect(reverse('area-sales-view', args=[_id, ]))

    context = {
        'form': form,
        'formset': formset,
        'data': area_sales,
        'areas': areas,
        'detail': detail,
        'managers': managers,
        'segment': 'area_sales',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'distributors': distributor,
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='AREA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/area_sales_view.html', context)


# Update Area Sales
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA')
def area_sales_update(request, _id):
    area_sales = AreaSales.objects.get(area_id=_id)
    AreaSalesDetailFormSet = modelformset_factory(
        AreaSalesDetail, form=FormAreaSalesDetail, extra=0, can_delete=True, can_delete_extra=True)
    qs = area_sales.areasalesdetail_set.all()
    distributor = Distributor.objects.all()
    detail = AreaSalesDetail.objects.filter(area_id=_id)
    managers = User.objects.filter(position_id='ASM')

    if request.POST:
        form = FormAreaSalesUpdate(
            request.POST, request.FILES, instance=area_sales)
        formset = AreaSalesDetailFormSet(request.POST, queryset=qs)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('area-sales-view', args=[_id, ]))
        # if all([form.is_valid(), formset.is_valid()]):
        #     try:
        #         parent = form.save(commit=False)
        #         parent.save()
        #         for form in formset:
        #             if form.cleaned_data.get('distributor') is None:
        #                 if form.cleaned_data.get('DELETE'):
        #                     continue
        #                 else:
        #                     continue
        #             else:
        #                 if form.cleaned_data.get('DELETE'):
        #                     form.instance.delete()
        #                     continue

        #             child = form.save(commit=False)
        #             child.area = parent
        #             child.save()
        #         return HttpResponseRedirect(reverse('area-sales-view', args=[_id, ]))
        #     except Exception:
        #         return HttpResponseRedirect(reverse('area-sales-view', args=[_id, ]))
    else:
        form = FormAreaSalesUpdate(instance=area_sales)
        formset = AreaSalesDetailFormSet(queryset=qs)

    message = form.errors
    context = {
        'form': form,
        'formset': formset,
        'data': area_sales,
        'detail': detail,
        'managers': managers,
        'segment': 'area_sales',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'distributors': distributor,
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='AREA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/area_sales_view.html', context)


# Delete Area Sales
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA')
def area_sales_delete(request, _id):
    area_sales = AreaSales.objects.get(area_id=_id)

    area_sales.delete()
    return HttpResponseRedirect(reverse('area-sales-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='AREA')
def area_sales_detail_delete(request, _id, _distributor):
    area_sales_detail = AreaSalesDetail.objects.get(
        area_id=_id, distributor_id=_distributor)

    area_sales_detail.delete()
    return HttpResponseRedirect(reverse('area-sales-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='AREA-CHANNEL')
def area_channel_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_areachannel.area_id, apps_areasales.area_name, apps_user.username FROM apps_areachannel INNER JOIN apps_areasales ON apps_areachannel.area_id = apps_areasales.area_id INNER JOIN apps_user ON apps_areasales.manager = apps_user.user_id")
        area_channels = cursor.fetchall()

    context = {
        'data': area_channels,
        'segment': 'area_channel',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='AREA-CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/area_channel_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='AREA-CHANNEL')
def area_channel_add(request):
    channel = Channel.objects.all()
    areas = AreaSales.objects.all()
    if request.POST:
        form = FormAreaChannel(request.POST, request.FILES)
        if form.is_valid():
            parent = form.save(commit=False)
            parent.save()
            for i in channel:
                child = AreaChannelDetail(
                    area=parent, channel=i, status=0)
                child.save()
            return HttpResponseRedirect(reverse('area-channel-view', args=[form.instance.area_id, ]))
        else:
            message = form.errors
            context = {
                'form': form,
                'areas': areas,
                'segment': 'area_channel',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(
                    user_id=request.user.user_id, menu_id='AREA-CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/area_channel_add.html', context)
    else:
        form = FormAreaChannel()
        context = {
            'form': form,
            'areas': areas,
            'segment': 'area_channel',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(
                user_id=request.user.user_id, menu_id='AREA-CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/area_channel_add.html', context)


# View Area Channel
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA-CHANNEL')
def area_channel_view(request, _id):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_areachannel.area_id, apps_areasales.area_name, apps_user.username FROM apps_areachannel INNER JOIN apps_areasales ON apps_areachannel.area_id = apps_areasales.area_id INNER JOIN apps_user ON apps_areasales.manager = apps_user.user_id WHERE apps_areachannel.area_id = '" + str(_id) + "'")
        area_channels = cursor.fetchone()

    detail = AreaChannelDetail.objects.filter(area=_id)

    context = {
        'data': area_channels,
        'detail': detail,
        'segment': 'area_channel',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='AREA-CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/area_channel_view.html', context)


# Delete Area Channel
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA-CHANNEL')
def area_channel_delete(request, _id):
    area_channels = AreaChannel.objects.get(area_id=_id)

    area_channels.delete()
    return HttpResponseRedirect(reverse('area-channel-index'))


# Update Area Channel Detail
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA-CHANNEL')
def area_channel_detail_update(request, _id, _channel):
    area_channels = AreaChannelDetail.objects.get(area=_id, channel=_channel)

    if request.POST:
        area_channels.status = 1 if request.POST.get('status') else 0
        area_channels.save()

        return HttpResponseRedirect(reverse('area-channel-view', args=[_id, ]))

    return render(request, 'home/area_channel_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_add(request):
    if request.POST:
        form = FormPosition(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('position-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'position',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/position_add.html', context)
    else:
        form = FormPosition()
        context = {
            'form': form,
            'segment': 'position',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/position_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT position_id, position_name FROM apps_position")
        positions = cursor.fetchall()

    context = {
        'data': positions,
        'segment': 'position',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/position_index.html', context)


# Update Position
@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_update(request, _id):
    positions = Position.objects.get(position_id=_id)
    if request.POST:
        form = FormPositionUpdate(
            request.POST, request.FILES, instance=positions)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('position-view', args=[_id, ]))
    else:
        form = FormPositionUpdate(instance=positions)

    message = form.errors
    context = {
        'form': form,
        'data': positions,
        'segment': 'position',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/position_view.html', context)


# Delete Position
@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_delete(request, _id):
    positions = Position.objects.get(position_id=_id)

    positions.delete()
    return HttpResponseRedirect(reverse('position-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_view(request, _id):
    positions = Position.objects.get(position_id=_id)
    form = FormPositionView(instance=positions)

    context = {
        'form': form,
        'data': positions,
        'segment': 'position',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/position_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_add(request):
    if request.POST:
        form = FormMenu(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('menu-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'menu',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/menu_add.html', context)
    else:
        form = FormMenu()
        context = {
            'form': form,
            'segment': 'menu',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/menu_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT menu_id, menu_name, menu_remark FROM apps_menu")
        menus = cursor.fetchall()

    context = {
        'data': menus,
        'segment': 'menu',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/menu_index.html', context)


# Update Menu
@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_update(request, _id):
    menus = Menu.objects.get(menu_id=_id)
    if request.POST:
        form = FormMenuUpdate(request.POST, request.FILES, instance=menus)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('menu-view', args=[_id, ]))
    else:
        form = FormMenuUpdate(instance=menus)

    message = form.errors
    context = {
        'form': form,
        'data': menus,
        'segment': 'menu',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/menu_view.html', context)


# Delete Menu
@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_delete(request, _id):
    menus = Menu.objects.get(menu_id=_id)

    menus.delete()
    return HttpResponseRedirect(reverse('menu-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_view(request, _id):
    menus = Menu.objects.get(menu_id=_id)
    form = FormMenuView(instance=menus)

    context = {
        'form': form,
        'data': menus,
        'segment': 'menu',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/menu_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CHANNEL')
def channel_add(request):
    if request.POST:
        form = FormChannel(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('channel-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'channel',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/channel_add.html', context)
    else:
        form = FormChannel()
        context = {
            'form': form,
            'segment': 'channel',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/channel_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CHANNEL')
def channel_index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT channel_id, channel_name FROM apps_channel")
        channels = cursor.fetchall()

    context = {
        'data': channels,
        'segment': 'channel',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/channel_index.html', context)


# Update Channel
@login_required(login_url='/login/')
@role_required(allowed_roles='CHANNEL')
def channel_update(request, _id):
    channels = Channel.objects.get(channel_id=_id)
    if request.POST:
        form = FormChannelUpdate(
            request.POST, request.FILES, instance=channels)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('channel-view', args=[_id, ]))
    else:
        form = FormChannelUpdate(instance=channels)

    message = form.errors
    context = {
        'form': form,
        'data': channels,
        'segment': 'channel',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/channel_view.html', context)


# Delete Channel
@login_required(login_url='/login/')
@role_required(allowed_roles='CHANNEL')
def channel_delete(request, _id):
    channels = Channel.objects.get(channel_id=_id)

    channels.delete()
    return HttpResponseRedirect(reverse('channel-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CHANNEL')
def channel_view(request, _id):
    channels = Channel.objects.get(channel_id=_id)
    form = FormChannelView(instance=channels)

    context = {
        'form': form,
        'data': channels,
        'segment': 'channel',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/channel_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUISINE')
def cuisine_index(request):
    cuisines = Cuisine.objects.all()

    context = {
        'data': cuisines,
        'segment': 'cuisine',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUISINE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cuisine_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUISINE')
def cuisine_add(request):
    if request.POST:
        form = FormCuisine(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('cuisine-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'cuisine',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUISINE') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/cuisine_add.html', context)
    else:
        form = FormCuisine()
        context = {
            'form': form,
            'segment': 'cuisine',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUISINE') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/cuisine_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUISINE')
def cuisine_view(request, _id):
    cuisines = Cuisine.objects.get(cuisine_id=_id)
    form = FormCuisineView(instance=cuisines)

    context = {
        'form': form,
        'data': cuisines,
        'segment': 'cuisine',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUISINE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cuisine_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUISINE')
def cuisine_update(request, _id):
    cuisines = Cuisine.objects.get(cuisine_id=_id)
    if request.POST:
        form = FormCuisineUpdate(
            request.POST, request.FILES, instance=cuisines)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('cuisine-view', args=[_id, ]))
    else:
        form = FormCuisineUpdate(instance=cuisines)

    message = form.errors
    context = {
        'form': form,
        'data': cuisines,
        'segment': 'cuisine',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUISINE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cuisine_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUISINE')
def cuisine_delete(request, _id):
    cuisines = Cuisine.objects.get(cuisine_id=_id)

    cuisines.delete()
    return HttpResponseRedirect(reverse('cuisine-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CATEGORY')
def category_index(request):
    categories = Category.objects.all()

    context = {
        'data': categories,
        'segment': 'category',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CATEGORY') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/category_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CATEGORY')
def category_add(request):
    if request.POST:
        form = FormCategory(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('category-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'category',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CATEGORY') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/category_add.html', context)
    else:
        form = FormCategory()
        context = {
            'form': form,
            'segment': 'category',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CATEGORY') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/category_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CATEGORY')
def category_view(request, _id):
    categories = Category.objects.get(category_id=_id)
    form = FormCategoryView(instance=categories)

    context = {
        'form': form,
        'data': categories,
        'segment': 'category',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CATEGORY') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/category_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CATEGORY')
def category_update(request, _id):
    categories = Category.objects.get(category_id=_id)
    if request.POST:
        form = FormCategoryUpdate(
            request.POST, request.FILES, instance=categories)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('category-view', args=[_id, ]))
    else:
        form = FormCategoryUpdate(instance=categories)

    message = form.errors
    context = {
        'form': form,
        'data': categories,
        'segment': 'category',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CATEGORY') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/category_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CATEGORY')
def category_delete(request, _id):
    categories = Category.objects.get(category_id=_id)

    categories.delete()
    return HttpResponseRedirect(reverse('category-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_index(request):
    packages = Package.objects.all()

    context = {
        'data': packages,
        'segment': 'package',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/package_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_add(request):
    categories = Category.objects.all()
    if request.POST:
        form = FormPackage(request.POST, request.FILES)
        if form.is_valid():
            new = form.save(commit=False)
            new.category_id = request.POST.get('category')
            new.type = request.POST.get('type')
            new.save()
            return HttpResponseRedirect(reverse('package-view', args=[new.package_id, ]))
        else:
            message = form.errors
            context = {
                'form': form,
                'categories': categories,
                'segment': 'package',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/package_add.html', context)
    else:
        form = FormPackage()
        message = form.errors
        context = {
            'form': form,
            'categories': categories,
            'segment': 'package',
            'group_segment': 'master',
            'crud': 'add',
            'message': message,
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/package_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('main_cuisine[]')
        for i in main_cuisines:
            if str(i.cuisine_id) in check:
                try:
                    main_cuisine = MainCuisine(
                        package=packages, cuisine=i)
                    main_cuisine.save()
                except IntegrityError:
                    continue
            else:
                MainCuisine.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'main_cuisine',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_subcuisine_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('sub_cuisine[]')
        for i in sub_cuisines:
            if str(i.cuisine_id) in check:
                try:
                    sub_cuisine = SubCuisine(
                        package=packages, cuisine=i)
                    sub_cuisine.save()
                except IntegrityError:
                    continue
            else:
                SubCuisine.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-subcuisine-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'sub_cuisine',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine1_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('side_cuisine1[]')
        for i in side_cuisines1:
            if str(i.cuisine_id) in check:
                try:
                    side_cuisine1 = SideCuisine1(
                        package=packages, cuisine=i)
                    side_cuisine1.save()
                except IntegrityError:
                    continue
            else:
                SideCuisine1.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-sidecuisine1-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'side_cuisine1',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine2_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('side_cuisine2[]')
        for i in side_cuisines2:
            if str(i.cuisine_id) in check:
                try:
                    side_cuisine2 = SideCuisine2(
                        package=packages, cuisine=i)
                    side_cuisine2.save()
                except IntegrityError:
                    continue
            else:
                SideCuisine2.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-sidecuisine2-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'side_cuisine2',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine3_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('side_cuisine3[]')
        for i in side_cuisines3:
            if str(i.cuisine_id) in check:
                try:
                    side_cuisine3 = SideCuisine3(
                        package=packages, cuisine=i)
                    side_cuisine3.save()
                except IntegrityError:
                    continue
            else:
                SideCuisine3.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-sidecuisine3-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'side_cuisine3',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine4_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('side_cuisine4[]')
        for i in side_cuisines4:
            if str(i.cuisine_id) in check:
                try:
                    side_cuisine4 = SideCuisine4(
                        package=packages, cuisine=i)
                    side_cuisine4.save()
                except IntegrityError:
                    continue
            else:
                SideCuisine4.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-sidecuisine4-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'side_cuisine4',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine5_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('side_cuisine5[]')
        for i in side_cuisines5:
            if str(i.cuisine_id) in check:
                try:
                    side_cuisine5 = SideCuisine5(
                        package=packages, cuisine=i)
                    side_cuisine5.save()
                except IntegrityError:
                    continue
            else:
                SideCuisine5.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-sidecuisine5-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'side_cuisine5',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_maincuisine_delete(request, _id, _cuisine):
    MainCuisine.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_subcuisine_delete(request, _id, _cuisine):
    SubCuisine.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine1_delete(request, _id, _cuisine):
    SideCuisine1.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine2_delete(request, _id, _cuisine):
    SideCuisine2.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine3_delete(request, _id, _cuisine):
    SideCuisine3.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine4_delete(request, _id, _cuisine):
    SideCuisine4.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine5_delete(request, _id, _cuisine):
    SideCuisine5.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_update(request, _id):
    packages = Package.objects.get(package_id=_id)
    categories = Category.objects.all()
    if request.POST:
        form = FormPackageUpdate(
            request.POST, request.FILES, instance=packages)
        if form.is_valid():
            update = form.save(commit=False)
            update.category_id = request.POST.get('category')
            update.type = request.POST.get('type')
            update.male_price = request.POST.get('male_price')
            update.female_price = request.POST.get('female_price')
            update.save()
            return HttpResponseRedirect(reverse('package-view', args=[_id, ]))
    else:
        form = FormPackageUpdate(instance=packages)

    message = form.errors
    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'segment': 'package',
        'group_segment': 'master',
        'crud': 'update',
        'tab': 'main_cuisine',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_delete(request, _id):
    packages = Package.objects.get(package_id=_id)

    packages.delete()
    return HttpResponseRedirect(reverse('package-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET')
def budget_add(request, _area):
    period = Closing.objects.all()
    closing = 'True'
    closing_period = 'True'
    message = ''
    area = AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', 'area__area_name')
    selected_area = _area
    name = AreaSales.objects.get(
        area_id=selected_area) if selected_area != 'NONE' else None
    distributor = Distributor.objects.filter(
        distributor_id__in=AreaSalesDetail.objects.filter(
            area_id=selected_area).values_list('distributor_id', flat=True)
    ).exclude(
        distributor_id__in=Budget.objects.filter(
            budget_area=selected_area,
            budget_month=datetime.datetime.now().strftime('%m'),
            budget_year=datetime.datetime.now().year
        ).values_list('budget_distributor_id', flat=True)
    )
    month = '{:02d}'.format(int(request.POST.get('budget_month'))) if request.POST.get(
        'budget_month') else '{:02d}'.format(int(datetime.datetime.now().month))
    no_save = False
    if _area != 'NONE':
        approvers = BudgetApproval.objects.filter(
            area_id=_area).order_by('sequence')
        if approvers.count() == 0:
            message = "No budget's approver found for this area."
            no_save = True

    if period.count() == 0:
        closing_period = 'False'
    else:
        if period[0].month_open == str(datetime.datetime.now().month) and period[0].year_open == str(datetime.datetime.now().year):
            if request.POST:
                form = FormBudget(request.POST, request.FILES)
                if form.is_valid():
                    _id = 'UBS/' + \
                        request.POST.get('budget_area') + '/' + \
                        request.POST.get('budget_distributor') + '/' + \
                        month + '/' + request.POST.get('budget_year')
                    try:
                        budget = Budget.objects.get(budget_id=_id)
                        if budget:
                            message = 'Budget already exist'
                    except Budget.DoesNotExist:
                        parent = form.save(commit=False)
                        if parent.budget_amount == 0:
                            message = 'Beginning Budget is required'
                        else:
                            parent.budget_id = _id
                            parent.budget_balance = int(request.POST.get(
                                'budget_amount'))
                            parent.budget_status = 'DRAFT'
                            parent.budget_new = True
                            area = parent.budget_area.area_id
                            parent.save()
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "SELECT channel_id FROM apps_areachanneldetail WHERE area_id = '" + str(area) + "' AND status = 1")
                                area_channels = cursor.fetchall()
                                for i in area_channels:
                                    child = BudgetDetail(
                                        budget=parent, budget_channel_id=i[0])
                                    child.save()

                            for j in approvers:
                                release = BudgetRelease(
                                    budget=parent, budget_approval_id=j.approver_id, budget_approval_name=j.approver.username, budget_approval_email=j.approver.email, budget_approval_position=j.approver.position.position_name, sequence=j.sequence)
                                release.save()

                            email = User.objects.filter(
                                position_id='TMM', areauser__area_id=_area).values_list('email', flat=True)
                            recipient_list = list(email)
                            subject = 'Budget Percentages Input'
                            _message = 'Dear All,\n\nPlease note that Budget No. ' + _id + ' needs to be inputted as a budget percentage for each channel.\n\nClick the following link to upload some budget percentage at once.\n' + host.url + 'budget_upload/\n\nOr click the following link to change this budget channel percentage only.\n' + \
                                host.url + 'budget/view/draft/' + _id + '/NONE/' + '\n\nThank you.'
                            send_email(subject, _message, recipient_list)

                            return HttpResponseRedirect(reverse('budget-view', args=['draft', parent.budget_id, 'NONE']))
        else:
            closing = 'False'

    form = FormBudget(
        initial={'budget_year': datetime.datetime.now().year, 'budget_month': month, 'budget_amount': 0, 'budget_upping': 0, 'budget_total': 0})

    msg = form.errors
    context = {
        'msg': msg,
        'message': message,
        'form': form,
        'area': area,
        'distributor': distributor,
        'selected_area': selected_area,
        'closing': closing,
        'closing_period': closing_period,
        'name': name,
        'no_save': no_save,
        'segment': 'budget',
        'group_segment': 'budget',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/budget_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET')
def budget_index(request, _tab):
    drafts = Budget.objects.filter(budget_status='DRAFT', budget_area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-budget_year', '-budget_month').all
    draft_count = Budget.objects.filter(budget_status='DRAFT', budget_area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-budget_year', '-budget_month').count
    pendings = Budget.objects.filter(budget_status='PENDING', budget_area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-budget_year', '-budget_month').all
    pendings_count = Budget.objects.filter(budget_status='PENDING', budget_area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-budget_year', '-budget_month').count
    inapprovals = Budget.objects.filter(budget_status='IN APPROVAL', budget_area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-budget_year', '-budget_month').all
    inapprovals_count = Budget.objects.filter(budget_status='IN APPROVAL', budget_area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-budget_year', '-budget_month').count
    opens = Budget.objects.filter(budget_status='OPEN', budget_area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-budget_year', '-budget_month').all
    opens_count = Budget.objects.filter(budget_status='OPEN', budget_area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-budget_year', '-budget_month').count

    context = {
        'drafts': drafts,
        'drafts_count': draft_count,
        'pendings': pendings,
        'pendings_count': pendings_count,
        'inapprovals': inapprovals,
        'inapprovals_count': inapprovals_count,
        'opens': opens,
        'opens_count': opens_count,
        'tab': _tab,
        'segment': 'budget',
        'group_segment': 'budget',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/budget_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-ARCHIVE')
def budget_archive_index(request):
    closed_budgets = Budget.objects.filter(budget_status='CLOSED', budget_area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-budget_year', '-budget_month').all

    context = {
        'closed_budgets': closed_budgets,
        'segment': 'budget_archive',
        'group_segment': 'budget',
        'crud': 'archive',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET-ARCHIVE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/budget_archive.html', context)


# Update Budget
@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET')
def budget_update(request, _tab, _id):
    budgets = Budget.objects.get(budget_id=_id)
    budget_detail = BudgetDetail.objects.filter(budget_id=_id)

    if request.POST:
        form = FormNewBudgetUpdate(
            request.POST, request.FILES, instance=budgets) if budgets.budget_new else FormBudgetUpdate(request.POST, request.FILES, instance=budgets)
        if form.is_valid():
            update = form.save(commit=False)
            update.budget_year = budgets.budget_year
            update.budget_month = budgets.budget_month
            update.budget_balance = int(request.POST.get('budget_amount')) + \
                int(request.POST.get('budget_upping'))
            update.save()
            for i in budget_detail:
                i.budget_amount = (i.budget_percent/100) * \
                    budgets.budget_amount if budgets.budget_new else i.budget_amount
                i.budget_upping = (i.budget_percent/100) * \
                    budgets.budget_upping
                i.save()

            if budgets.budget_status == 'DRAFT':
                email = User.objects.filter(
                    position_id='TMM', areauser__area_id=budgets.budget_area).values_list('email', flat=True)
                recipient_list = list(email)
                subject = 'Budget Percentages Input'
                message = 'Dear All,\n\nPlease note that Budget No. ' + _id + ' needs to be inputted as a budget percentage for each channel.\n\nClick the following link to upload some budget percentage at once.\n' + host.url + 'budget_upload/' + '\n\nOr click the following link to change this budget channel percentage only.\n' + \
                    host.url + 'budget/view/draft/' + _id + '/NONE/' + '\n\nThank you.'
                send_email(subject, message, recipient_list)

            return HttpResponseRedirect(reverse('budget-view', args=[_tab, _id, 'NONE']))
    else:
        form = FormNewBudgetUpdate(instance=budgets) if budgets.budget_new else FormBudgetUpdate(
            instance=budgets)

    YEAR_CHOICES = []
    for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append(str(r))

    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append(str(r))

    try:
        auth_percent = Auth.objects.get(
            user_id=request.user.user_id, menu_id='BUDGET-PERCENTAGE')
    except Auth.DoesNotExist:
        auth_percent = None

    message = form.errors
    context = {
        'form': form,
        'data': budgets,
        'year': YEAR_CHOICES,
        'month': MONTH_CHOICES,
        'budget_detail': budget_detail,
        'new': budgets.budget_new,
        'tab': _tab,
        'segment': 'budget',
        'group_segment': 'budget',
        'crud': 'update',
        'message': message if message else 'NONE',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET') if not request.user.is_superuser else Auth.objects.all(),
        'btn_percent': auth_percent if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/budget_view.html', context)


# Delete Budget
@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET')
def budget_delete(request, _tab, _id):
    budgets = Budget.objects.get(budget_id=_id)

    budgets.delete()
    return HttpResponseRedirect(reverse('budget-index', args=[_tab, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET')
def budget_view(request, _tab, _id, _msg):
    budget = Budget.objects.get(budget_id=_id)
    budget.budget_amount = '{:,}'.format(budget.budget_amount)
    budget.budget_upping = '{:,}'.format(budget.budget_upping)
    budget.budget_total = '{:,}'.format(budget.budget_total)
    form = FormBudgetView(instance=budget)
    budget_detail = BudgetDetail.objects.filter(budget_id=_id)
    for detail in budget_detail:
        detail.budget_amount = '{:,}'.format(detail.budget_amount)
        detail.budget_upping = '{:,}'.format(detail.budget_upping)
        detail.budget_total = '{:,}'.format(detail.budget_total)
        detail.budget_balance = '{:,}'.format(detail.budget_balance)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_channel.channel_id, channel_name, q_channel.budget_channel_id FROM apps_channel LEFT JOIN (SELECT * FROM apps_budgetdetail WHERE budget_id = '" + str(_id) + "') AS q_channel ON apps_channel.channel_id = q_channel.budget_channel_id WHERE q_channel.budget_channel_id IS NULL")
        channel = cursor.fetchall()
    approval = BudgetRelease.objects.filter(budget_id=_id).order_by('sequence')

    YEAR_CHOICES = []
    for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append(str(r))

    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append(str(r))

    try:
        auth_percent = Auth.objects.get(
            user_id=request.user.user_id, menu_id='BUDGET-PERCENTAGE')
    except Auth.DoesNotExist:
        auth_percent = None

    context = {
        'form': form,
        'data': budget,
        'status': budget.budget_status,
        'year': YEAR_CHOICES,
        'month': MONTH_CHOICES,
        'budget_detail': budget_detail,
        'approval': approval,
        'message': 'NONE' if _msg == 'NONE' else 'Total budget percentage you entered is not 100%',
        'tab': _tab,
        'channel': channel,
        'segment': 'budget',
        'group_segment': 'budget',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET') if not request.user.is_superuser else Auth.objects.all(),
        'btn_percent': auth_percent if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/budget_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET')
def budget_detail_update(request, _tab, _id):
    budget = Budget.objects.get(budget_id=_id)
    detail = BudgetDetail.objects.filter(budget_id=_id)
    msg = 'NONE'
    if request.POST:
        hundreds = 0
        for i in detail:
            i.budget_percent = request.POST.get(
                'budget_percent_'+str(i.budget_channel_id))
            hundreds += int(i.budget_percent)
        if hundreds == 100:
            for i in detail:
                if budget.budget_new:
                    i.budget_amount = (Decimal(
                        int(i.budget_percent)/100) * budget.budget_amount)
                i.budget_upping = Decimal(
                    int(i.budget_percent)/100) * budget.budget_upping
                i.save()

            budget.budget_status = 'PENDING'
            budget.save()

            email = BudgetRelease.objects.filter(
                budget_id=_id).order_by('sequence').values_list('budget_approval_email', flat=True)
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT username FROM apps_budgetrelease INNER JOIN apps_user ON apps_budgetrelease.budget_approval_id = apps_user.user_id WHERE budget_id = '" + str(_id) + "' AND budget_approval_status = 'N' ORDER BY sequence LIMIT 1")
                approver = cursor.fetchone()

            subject = 'Budget Approval'
            message = 'Dear ' + approver[0] + ',\n\nYou have a new budget to approve. Please check your budget release list.\n\n' + \
                'Click this link to approve, revise or return this budget.\n' + host.url + 'budget_release/view/' + str(_id) + '/NONE/0/' + \
                '\n\nThank you.'
            send_email(subject, message, [email[0]])

            return HttpResponseRedirect(reverse('budget-view', args=['pending', _id, 'NONE']))
        else:
            msg = 'Total budget percentage you entered is not 100%'

    return HttpResponseRedirect(reverse('budget-view', args=[_tab, _id, msg, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-PERCENTAGE')
def budget_upload(request):
    channels = Channel.objects.all()
    success = 0
    failed = 0
    errors = []
    recipients = []
    is_send = False
    if request.POST:
        UploadLog.objects.filter(document='BUDGET').delete()
        dataset = Dataset()
        new_budget_percent = request.FILES['budget_file']
        imported_data = dataset.load(new_budget_percent.read(), format='xlsx')
        for data in imported_data:
            col = 5
            hundreds = 0
            try:
                budget = Budget.objects.get(budget_id=data[4])
                if budget.budget_status == 'DRAFT':
                    i = col
                    for channel in channels:
                        try:
                            BudgetDetail.objects.get(
                                budget_id=data[4], budget_channel_id=channel.channel_id)
                            hundreds += data[i]
                        except BudgetDetail.DoesNotExist:
                            pass
                        i += 1

                    if hundreds == 100:
                        for channel in channels:
                            try:
                                rec = BudgetDetail.objects.get(
                                    budget_id=data[4], budget_channel_id=channel.channel_id)
                                rec.budget_percent = data[col]
                                if budget.budget_new:
                                    rec.budget_amount = (Decimal(
                                        int(data[col])/100) * budget.budget_amount)
                                rec.budget_upping = Decimal(
                                    int(data[col])/100) * budget.budget_upping
                                rec.save()
                                success += 1
                                budget.budget_status = 'PENDING'
                                budget.save()

                                is_send = True
                                email = BudgetRelease.objects.filter(
                                    budget_id=data[4]).order_by('sequence').values_list('budget_approval_email', flat=True)
                                with connection.cursor() as cursor:
                                    cursor.execute(
                                        "SELECT username FROM apps_budgetrelease INNER JOIN apps_user ON apps_budgetrelease.budget_approval_id = apps_user.user_id WHERE budget_id = '" + str(data[4]) + "' AND budget_approval_status = 'N' ORDER BY sequence LIMIT 1")
                                    approver = cursor.fetchone()
                                recipients.append((approver[0], email[0]))

                            except BudgetDetail.DoesNotExist:
                                pass
                            col += 1
                    else:
                        failed += 1
                        errors.append(
                            'Budget No. ' + data[4] + ' percentage is not 100%.')
                        log = UploadLog(
                            document='BUDGET', document_id=data[4], description='Budget No. ' + data[4] + ' percentage is not 100%.')
                        log.save()
                else:
                    failed += 1
                    errors.append(
                        'Budget No. ' + data[4] + ' is not in DRAFT status.')
                    log = UploadLog(
                        document='BUDGET', document_id=data[4], description='Budget No. ' + data[4] + ' is not in DRAFT status.')
                    log.save()
            except Budget.DoesNotExist:
                failed += 1
                errors.append('Budget No. ' + data[4] + ' could not be found.')
                log = UploadLog(
                    document='BUDGET', document_id=data[4], description='Budget No. ' + data[4] + ' could not be found.')
                log.save()

        context = {
            'success': success,
            'failed': failed,
            'errors': errors,
            'total': imported_data.height,
            'segment': 'budget_upload',
            'group_segment': 'budget',
            'crud': 'upload',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.all(),
        }

        if is_send:
            recipient_list = list(dict.fromkeys(recipients))
            for mail_to in recipient_list:
                subject = 'Budget Approval'
                message = 'Dear ' + mail_to[0] + ',\n\nYou have some budgets to approve. Please check your dashboard.\n\n' + \
                    'Click this link to approve, revise or return the budgets.\n' + host.url + 'budget_release/' + \
                    '\n\nThank you.'
                send_email(subject, message, [mail_to[1]])

        return render(request, 'home/budget_uploadlog.html', context)

    context = {
        'segment': 'budget_upload',
        'group_segment': 'budget',
        'crud': 'upload',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.all(),
    }
    return render(request, 'home/budget_upload.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-PERCENTAGE')
def export_uploadlog(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Upload-Log-' + \
        str(datetime.datetime.now()) + '.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Upload Log')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Budget No.', 'Description']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()

    rows = UploadLog.objects.filter(document='BUDGET').values_list(
        'document_id', 'description')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-PERCENTAGE')
def export_budget_to_excel(request):
    channel = 'True'
    channel_ids = Channel.objects.values_list('channel_id', flat=True)
    if channel_ids.count() == 0:
        channel = 'False'
        return render(request, 'home/budget_upload  .html', {'channel': channel})

    # Retrieve budget data from the database
    budget_data = Budget.objects.filter(budget_status='DRAFT')

    # Create a new Excel workbook and add a worksheet
    workbook = xlsxwriter.Workbook('Budget_Data.xlsx')
    worksheet = workbook.add_worksheet('Budget Data')

    # Define column headers
    headers = ['Year', 'Month',
               'Area', 'Distributor', 'Budget ID']
    headers.extend([f"{channel_id} (%)" for channel_id in channel_ids])
    headers.append('Check')

    # Define cell formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#7eaa55',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
    })
    cell_format = workbook.add_format({'border': 1, 'bg_color': '#e5eedc'})
    center = workbook.add_format(
        {'align': 'center', 'border': 1, 'bg_color': '#e5eedc'})
    cell_unlock = workbook.add_format(
        {'border': 1, 'bg_color': '#ffffff', 'locked': False})

    # Set column width
    worksheet.set_column(3, 3, 9)
    worksheet.set_column(4, 4, 24)

    # Write column headers to the worksheet
    for col_index, header in enumerate(headers):
        worksheet.write(0, col_index, header, header_format)

    # Write budget data to the worksheet
    for row_index, budget in enumerate(budget_data, start=1):
        worksheet.write(row_index, 0, budget.budget_year, center)
        worksheet.write(row_index, 1, budget.budget_month, center)
        worksheet.write(row_index, 2, budget.budget_area_id, cell_format)
        worksheet.write(
            row_index, 3, budget.budget_distributor_id, cell_format)
        worksheet.write(row_index, 4, budget.budget_id, cell_format)

        # Write channel data to the worksheet
        for col_index, channel_id in enumerate(channel_ids, start=5):
            try:
                budget_detail = BudgetDetail.objects.get(
                    budget_id=budget.budget_id, budget_channel_id=channel_id)
                worksheet.write(row_index, col_index,
                                budget_detail.budget_percent, cell_unlock)
            except BudgetDetail.DoesNotExist:
                worksheet.write(row_index, col_index, 0, cell_format)

        # Write formula for the 'Check' column
        formula = f"SUM({xlsxwriter.utility.xl_range(row_index, 5, row_index, 4 + len(channel_ids))})"
        worksheet.write_formula(
            row_index, 5 + len(channel_ids), formula, cell_format)

        # Apply conditional formatting for 'Check' column
        check_cell = xlsxwriter.utility.xl_rowcol_to_cell(
            row_index, 5 + len(channel_ids))
        format_red = workbook.add_format({'bg_color': 'red', 'border': 1})
        worksheet.conditional_format(
            check_cell, {'type': 'cell', 'criteria': '!=', 'value': 100, 'format': format_red})

    # Protect the worksheet
    worksheet.protect()

    workbook.close()

    # Return the Excel file as a response
    with open('Budget_Data.xlsx', 'rb') as file:
        response = HttpResponse(file.read(
        ), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=Budget_Data.xlsx'
        return response


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-RELEASE')
def budget_release_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_budget.budget_id, apps_distributor.distributor_name, apps_budget.budget_amount, apps_budget.budget_upping, apps_budget.budget_total, apps_budget.budget_status, apps_budgetrelease.sequence FROM apps_distributor INNER JOIN apps_budget ON apps_distributor.distributor_id = apps_budget.budget_distributor_id INNER JOIN apps_budgetrelease ON apps_budget.budget_id = apps_budgetrelease.budget_id INNER JOIN (SELECT budget_id, MIN(sequence) AS seq FROM apps_budgetrelease WHERE budget_approval_status = 'N' GROUP BY budget_id ORDER BY sequence ASC) AS q_group ON apps_budgetrelease.budget_id = q_group.budget_id AND apps_budgetrelease.sequence = q_group.seq WHERE (apps_budget.budget_status = 'PENDING' OR apps_budget.budget_status = 'IN APPROVAL') AND apps_budgetrelease.budget_approval_id = '" + str(request.user.user_id) + "'")
        release = cursor.fetchall()

    context = {
        'data': release,
        'segment': 'budget_release',
        'group_segment': 'budget',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/budget_release_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_proposal.proposal_id, apps_proposal.proposal_date, apps_proposal.channel, apps_division.division_name, apps_proposal.total_cost, apps_proposal.status, apps_proposalrelease.sequence FROM apps_division INNER JOIN apps_proposal ON apps_division.division_id = apps_proposal.division_id INNER JOIN apps_proposalrelease ON apps_proposal.proposal_id = apps_proposalrelease.proposal_id INNER JOIN (SELECT proposal_id, MIN(sequence) AS seq FROM apps_proposalrelease WHERE proposal_approval_status = 'N' GROUP BY proposal_id ORDER BY sequence ASC) AS q_group ON apps_proposalrelease.proposal_id = q_group.proposal_id AND apps_proposalrelease.sequence = q_group.seq WHERE (apps_proposal.status = 'PENDING' OR apps_proposal.status = 'IN APPROVAL') AND apps_proposalrelease.proposal_approval_id = '" + str(request.user.user_id) + "'")
        release = cursor.fetchall()

    context = {
        'data': release,
        'segment': 'proposal_release',
        'group_segment': 'proposal',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROPOSAL-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/proposal_release_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-RELEASE')
def budget_release_view(request, _id, _msg, _is_revise):
    budget = Budget.objects.get(budget_id=_id)
    budget.budget_amount = '{:,}'.format(budget.budget_amount)
    budget.budget_upping = '{:,}'.format(budget.budget_upping)
    budget.budget_total = '{:,}'.format(budget.budget_total)
    form = FormBudgetView(instance=budget)
    budget_detail = BudgetDetail.objects.filter(budget_id=_id)
    for detail in budget_detail:
        detail.budget_amount = '{:,}'.format(detail.budget_amount)
        detail.budget_upping = '{:,}'.format(detail.budget_upping)
        detail.budget_total = '{:,}'.format(detail.budget_total)
        detail.budget_balance = '{:,}'.format(detail.budget_balance)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_channel.channel_id, channel_name, q_channel.budget_channel_id FROM apps_channel LEFT JOIN (SELECT * FROM apps_budgetdetail WHERE budget_id = '" + str(_id) + "') AS q_channel ON apps_channel.channel_id = q_channel.budget_channel_id WHERE q_channel.budget_channel_id IS NULL")
        channel = cursor.fetchall()

    YEAR_CHOICES = []
    for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append(str(r))

    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append(str(r))

    approved = BudgetRelease.objects.get(
        budget_id=_id, budget_approval_id=request.user.user_id).budget_approval_status

    context = {
        'form': form,
        'data': budget,
        'year': YEAR_CHOICES,
        'month': MONTH_CHOICES,
        'budget_detail': budget_detail,
        'message': 'NONE' if _msg == 'NONE' else 'Total budget percentage you entered is not 100%',
        'channel': channel,
        'is_revise': _is_revise,
        'approved': approved,
        'segment': 'budget_release',
        'group_segment': 'budget',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/budget_release_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_view(request, _id, _sub_id, _act, _msg, _is_revise):
    proposal = Proposal.objects.get(proposal_id=_id)
    budget = BudgetDetail.objects.get(
        budget=proposal.budget, budget_channel=proposal.channel)
    form = FormProposalView(instance=proposal)
    divs = Division.objects.all()
    form_incremental = FormIncrementalSales()
    incremental = IncrementalSales.objects.filter(proposal_id=_id)
    total = IncrementalSales.objects.filter(proposal_id=_id).aggregate(
        swop_carton__sum=Sum('swop_carton'),
        swop_nom__sum=Sum('swop_nom'),
        swp_carton__sum=Sum('swp_carton'),
        swp_nom__sum=Sum('swp_nom'),
        incrp_carton__sum=Sum('incrp_carton'),
        incrp_nom__sum=Sum('incrp_nom'),
    )
    incpst_carton = (total['incrp_carton__sum'] / total['swop_carton__sum']
                     ) * 100 if total['swop_carton__sum'] else 0
    incpst_nom = (total['incrp_nom__sum'] / total['swop_nom__sum']
                  ) * 100 if total['swop_nom__sum'] else 0
    form_cost = FormProjectedCost()
    cost = ProjectedCost.objects.filter(proposal_id=_id)
    total_cost = ProjectedCost.objects.filter(
        proposal_id=_id).aggregate(Sum('cost'))
    add_cost = True if budget.budget_balance > 0 else False
    approved = ProposalRelease.objects.get(
        proposal_id=_id, proposal_approval_id=request.user.user_id).proposal_approval_status

    context = {
        'form': form,
        'divs': divs,
        'formInc': form_incremental,
        'incremental': incremental,
        'data': proposal,
        'budget': budget,
        'formCost': form_cost,
        'cost': cost,
        'total': total,
        'incpst_carton': incpst_carton,
        'incpst_nom': incpst_nom,
        'total_inc': total['incrp_nom__sum'] if total['incrp_nom__sum'] else 0,
        'total_cost': total_cost['cost__sum'] if total_cost['cost__sum'] else 0,
        'sub_id': _sub_id,
        'action': _act,
        'message': _msg,
        'approved': approved,
        'is_revise': _is_revise,
        'status': proposal.status,
        'add_cost': add_cost,
        'segment': 'proposal_release',
        'group_segment': 'proposal',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PROPOSAL-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
        'btn_release': ProposalRelease.objects.get(proposal_id=_id, proposal_approval_id=request.user.user_id),
    }
    return render(request, 'home/proposal_release_view.html', context)


# Update Budget
@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-RELEASE')
def budget_release_update(request, _id):
    budgets = Budget.objects.get(budget_id=_id)
    budget_detail = BudgetDetail.objects.filter(budget_id=_id)
    amount_before = budgets.budget_amount
    upping_before = budgets.budget_upping

    if request.POST:
        form = FormNewBudgetUpdate(
            request.POST, request.FILES, instance=budgets) if budgets.budget_new else FormBudgetUpdate(request.POST, request.FILES, instance=budgets)
        if form.is_valid():
            update = form.save(commit=False)
            update.budget_year = budgets.budget_year
            update.budget_month = budgets.budget_month
            update.budget_balance = int(request.POST.get('budget_amount')) + \
                int(request.POST.get('budget_upping'))
            update.save()
            for i in budget_detail:
                i.budget_amount = (i.budget_percent/100) * \
                    budgets.budget_amount if budgets.budget_new else i.budget_amount
                i.budget_upping = (i.budget_percent/100) * \
                    budgets.budget_upping
                i.save()

            recipients = []

            release = BudgetRelease.objects.get(
                budget_id=_id, budget_approval_id=request.user.user_id)
            release.upping_note = request.POST.get('upping_note')
            release.save()

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT budget_id, email FROM apps_budget INNER JOIN apps_user ON apps_budget.entry_by = apps_user.user_id WHERE budget_id = '" + str(_id) + "'")
                entry_mail = cursor.fetchone()
                recipients.append(entry_mail[1])

                cursor.execute(
                    "SELECT budget_id, email FROM apps_budget INNER JOIN apps_user ON apps_budget.update_by = apps_user.user_id WHERE budget_id = '" + str(_id) + "'")
                update_mail = cursor.fetchone()
                recipients.append(update_mail[1])

                cursor.execute(
                    "SELECT budget_id, email FROM apps_budgetdetail INNER JOIN apps_user ON apps_budgetdetail.update_by = apps_user.user_id WHERE budget_id = '" + str(_id) + "'")
                detail_mail = cursor.fetchone()
                recipients.append(detail_mail[1])

                cursor.execute(
                    "SELECT budget_id, budget_approval_email FROM apps_budgetrelease WHERE budget_id = '" + str(_id) + "' AND budget_approval_status = 'Y'")
                approver_mail = cursor.fetchone()
                if approver_mail:
                    recipients.append(approver_mail[1])

            subject = 'Beginning Balance Revised' if budgets.budget_new else 'Upping Price Revised'
            update_item = 'Beginning Balance' if budgets.budget_new else 'Upping Price'
            before_field = amount_before if budgets.budget_new else upping_before
            update_field = update.budget_amount if budgets.budget_new else update.budget_upping
            message = 'Dear All,\n\nThe following is ' + update_item + ' update for Budget No. ' + \
                str(_id) + ':\n\nValue before: ' + \
                '{:,}'.format(before_field) + '\nValue after: ' + \
                '{:,}'.format(update_field) + '\n\nNote: ' + \
                str(release.upping_note) + '\n\nClick the following link to view the budget.\n' + host.url + 'budget/view/draft/' + \
                str(_id) + '/NONE/' + \
                '\n\nThank you.'
            recipient_list = list(dict.fromkeys(recipients))
            send_email(subject, message, recipient_list)

            return HttpResponseRedirect(reverse('budget-release-view', args=[_id, 'NONE', 0]))
    else:
        form = FormNewBudgetUpdate(instance=budgets) if budgets.budget_new else FormBudgetUpdate(
            instance=budgets)

    YEAR_CHOICES = []
    for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append(str(r))

    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append(str(r))

    message = form.errors
    context = {
        'form': form,
        'data': budgets,
        'year': YEAR_CHOICES,
        'month': MONTH_CHOICES,
        'budget_detail': budget_detail,
        'new': budgets.budget_new,
        'segment': 'budget_release',
        'group_segment': 'budget',
        'crud': 'update',
        'message': message if message else 'NONE',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/budget_release_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_update(request, _id):
    proposal = Proposal.objects.get(proposal_id=_id)
    divs = Division.objects.all()
    incremental = IncrementalSales.objects.filter(proposal_id=_id)
    cost = ProjectedCost.objects.filter(proposal_id=_id)
    total = IncrementalSales.objects.filter(proposal_id=_id).aggregate(
        swop_carton__sum=Sum('swop_carton'),
        swop_nom__sum=Sum('swop_nom'),
        swp_carton__sum=Sum('swp_carton'),
        swp_nom__sum=Sum('swp_nom'),
        incrp_carton__sum=Sum('incrp_carton'),
        incrp_nom__sum=Sum('incrp_nom'),
        incpst_carton__ratio=(
            Sum('incpst_carton') / Sum('swop_carton')) * 100 if Sum('swop_carton') else 0,
        incpst_nom__ratio=(Sum('incpst_nom') / Sum('swop_nom')
                           ) * 100 if Sum('swop_nom') else 0,
    )
    total_cost = ProjectedCost.objects.filter(
        proposal_id=_id).aggregate(Sum('cost'))
    message = '0'
    _prg = proposal.program_name
    _div = proposal.division
    _prod = proposal.products
    _start = proposal.period_start.strftime('%d %b %Y')
    _end = proposal.period_end.strftime('%d %b %Y')
    _bck = proposal.background
    _obj = proposal.objectives
    _mech = proposal.mechanism
    _rem = proposal.remarks
    _att = proposal.attachment.name if proposal.attachment else None

    if request.POST:
        form = FormProposalUpdate(
            request.POST, request.FILES, instance=proposal)
        if form.is_valid():
            parent = form.save(commit=False)
            parent.duration = form.cleaned_data['period_end'] - \
                form.cleaned_data['period_start']
            if parent.duration.days < 0:
                message = 'Period end must be greater than period start.'
            else:
                program_name = _prg if form.cleaned_data['program_name'] != _prg else None
                division = _div if form.cleaned_data['division'] != _div else None
                products = _prod if form.cleaned_data['products'] != _prod else None
                start = _start if form.cleaned_data['period_start'].strftime(
                    '%d %b %Y') != _start else None
                end = _end if form.cleaned_data['period_end'].strftime(
                    '%d %b %Y') != _end else None
                background = _bck if form.cleaned_data['background'] != _bck else None
                objectives = _obj if form.cleaned_data['objectives'] != _obj else None
                mechanism = _mech if form.cleaned_data['mechanism'] != _mech else None
                remarks = _rem if form.cleaned_data['remarks'] != _rem else None
                attachment = _att if form.cleaned_data['attachment'] != _att else None
                parent.save()

                recipients = []

                release = ProposalRelease.objects.get(
                    proposal_id=_id, proposal_approval_id=request.user.user_id)
                release.revise_note = request.POST.get('revise_note')
                release.save()

                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT proposal_id, email FROM apps_proposal INNER JOIN apps_user ON apps_proposal.entry_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
                    entry_mail = cursor.fetchone()
                    if entry_mail:
                        recipients.append(entry_mail[1])

                    cursor.execute(
                        "SELECT proposal_id, email FROM apps_proposal INNER JOIN apps_user ON apps_proposal.update_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
                    update_mail = cursor.fetchone()
                    if update_mail:
                        recipients.append(update_mail[1])

                    cursor.execute(
                        "SELECT proposal_id, email FROM apps_incrementalsales INNER JOIN apps_user ON apps_incrementalsales.update_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
                    incremental_mail = cursor.fetchone()
                    if incremental_mail:
                        recipients.append(incremental_mail[1])

                    cursor.execute(
                        "SELECT proposal_id, email FROM apps_projectedcost INNER JOIN apps_user ON apps_projectedcost.update_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
                    cost_mail = cursor.fetchone()
                    if cost_mail:
                        recipients.append(cost_mail[1])

                    cursor.execute(
                        "SELECT proposal_id, proposal_approval_email FROM apps_proposalrelease WHERE proposal_id = '" + str(_id) + "' AND proposal_approval_status = 'Y'")
                    approver_mail = cursor.fetchall()
                    for mail in approver_mail:
                        recipients.append(mail[1])

                subject = 'Proposal Revised'
                msg = 'Dear All,\n\nThe following is revised proposal for Proposal No. ' + \
                    str(_id) + ':\n\nBEFORE\n'
                if program_name:
                    msg += 'Program Name: ' + str(program_name) + '\n'
                if division:
                    msg += 'Division: ' + str(division) + '\n'
                if products:
                    msg += 'Products: ' + str(products) + '\n'
                if start:
                    msg += 'Period Start: ' + start + '\n'
                if end:
                    msg += 'Period End: ' + end + '\n'
                if background:
                    msg += 'Background:\n' + str(background) + '\n'
                if objectives:
                    msg += 'Objectives:\n' + str(objectives) + '\n'
                if mechanism:
                    msg += 'Mechanism:\n' + str(mechanism) + '\n'
                if remarks:
                    msg += 'Remarks: ' + str(remarks) + '\n'
                if attachment:
                    msg += 'Attachment: ' + str(_att) + '\n'
                msg += '\nAFTER\n'
                if program_name:
                    msg += 'Program Name: ' + \
                        str(form.cleaned_data['program_name']) + '\n'
                if division:
                    msg += 'Division: ' + \
                        str(form.cleaned_data['division']) + '\n'
                if products:
                    msg += 'Products: ' + \
                        str(form.cleaned_data['products']) + '\n'
                if start:
                    msg += 'Period Start: ' + \
                        form.cleaned_data['period_start'].strftime(
                            '%d %b %Y') + '\n'
                if end:
                    msg += 'Period End: ' + \
                        str(form.cleaned_data['period_end'].strftime(
                            '%d %b %Y')) + '\n'
                if background:
                    msg += 'Background:\n' + \
                        str(form.cleaned_data['background']) + '\n'
                if objectives:
                    msg += 'Objectives:\n' + \
                        str(form.cleaned_data['objectives']) + '\n'
                if mechanism:
                    msg += 'Mechanism:\n' + \
                        str(form.cleaned_data['mechanism']) + '\n'
                if remarks:
                    msg += 'Remarks: ' + \
                        str(form.cleaned_data['remarks']) + '\n'
                if attachment:
                    msg += 'Attachment: ' + \
                        str(form.cleaned_data['attachment']) + '\n'
                msg += '\nNote: ' + \
                    str(release.revise_note) + '\n\nClick the following link to view the proposal.\n' + host.url + 'proposal/view/inapproval/' + str(_id) + '/0/0/0/' + \
                    '\n\nThank you.'

                recipient_list = list(dict.fromkeys(recipients))
                send_email(subject, msg, recipient_list)

                return HttpResponseRedirect(reverse('proposal-release-view', args=[_id, '0', '0', '0', 0]))
    else:
        form = FormProposalUpdate(instance=proposal)

    msg = form.errors
    context = {
        'form': form,
        'incremental': incremental,
        'cost': cost,
        'total': total,
        'total_inc': total['incrp_nom__sum'] if total['incrp_nom__sum'] else 0,
        'total_cost': total_cost['cost__sum'] if total_cost['cost__sum'] else 0,
        'data': proposal,
        'divs': divs,
        'msg': msg,
        'message': message,
        'segment': 'proposal',
        'group_segment': 'proposal',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROPOSAL-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/proposal_release_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET')
def budget_detail_release_update(request, _id):
    budget = Budget.objects.get(budget_id=_id)
    detail = BudgetDetail.objects.filter(budget_id=_id)
    channel_percent_before = []
    for i in detail:
        channel_percent_before.append((i.budget_channel_id, i.budget_percent))

    msg = 'NONE'
    if request.POST:
        hundreds = 0
        for i in detail:
            i.budget_percent = request.POST.get(
                'budget_percent_'+str(i.budget_channel_id))
            hundreds += int(i.budget_percent)
        if hundreds == 100:
            for i in detail:
                if budget.budget_new:
                    i.budget_amount = (Decimal(
                        int(i.budget_percent)/100) * budget.budget_amount)
                i.budget_upping = Decimal(
                    int(i.budget_percent)/100) * budget.budget_upping
                i.save()

            recipients = []

            release = BudgetRelease.objects.get(
                budget_id=_id, budget_approval_id=request.user.user_id)
            release.percentage_note = request.POST.get('percentage_note')
            release.save()

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT budget_id, email FROM apps_budget INNER JOIN apps_user ON apps_budget.entry_by = apps_user.user_id WHERE budget_id = '" + str(_id) + "'")
                entry_mail = cursor.fetchone()
                recipients.append(entry_mail[1])

                cursor.execute(
                    "SELECT budget_id, email FROM apps_budget INNER JOIN apps_user ON apps_budget.update_by = apps_user.user_id WHERE budget_id = '" + str(_id) + "'")
                update_mail = cursor.fetchone()
                recipients.append(update_mail[1])

                cursor.execute(
                    "SELECT budget_id, email FROM apps_budgetdetail INNER JOIN apps_user ON apps_budgetdetail.update_by = apps_user.user_id WHERE budget_id = '" + str(_id) + "'")
                detail_mail = cursor.fetchone()
                recipients.append(detail_mail[1])

                cursor.execute(
                    "SELECT budget_id, budget_approval_email FROM apps_budgetrelease WHERE budget_id = '" + str(_id) + "' AND budget_approval_status = 'Y'")
                approver_mail = cursor.fetchone()
                if approver_mail:
                    recipients.append(approver_mail[1])

            subject = 'Channel Percentage Revised'
            message = 'Dear All,\n\nThe following are channel percentages update for Budget No. ' + \
                str(_id) + ':\n\nBEFORE\n'
            for i in channel_percent_before:
                message += str(i[0]) + ': ' + str(i[1]) + '%\n'
            message += '\nAFTER\n'
            for i in detail:
                message += str(i.budget_channel_id) + ': ' + \
                    str(i.budget_percent) + '%\n'
            message += '\nNote: ' + \
                str(release.percentage_note) + '\n\nClick the following link to view the budget.\n' + host.url + 'budget/view/draft/' + \
                str(_id) + '/NONE/' + \
                '\n\nThank you.'
            recipient_list = list(dict.fromkeys(recipients))
            send_email(subject, message, recipient_list)

            return HttpResponseRedirect(reverse('budget-release-view', args=[_id, 'NONE', 0]))
        else:
            msg = 'Total budget percentage you entered is not 100%'

    return HttpResponseRedirect(reverse('budget-release-view', args=[_id, msg, 1]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_incremental_add(request, _id):
    form = FormIncrementalSales(request.POST, request.FILES)
    proposal = Proposal.objects.get(proposal_id=_id)
    message = '0'
    if form.is_valid():
        try:
            check = IncrementalSales.objects.get(
                proposal_id=_id, product=request.POST.get('product'))
            if check:
                message = 'Product already exist'
        except IncrementalSales.DoesNotExist:
            swop_carton = int(request.POST.get('swop_carton'))
            swp_carton = int(request.POST.get('swp_carton'))
            if swop_carton > swp_carton:
                message = 'Sales With Program must be greater than Sales Without Program'
            else:
                incremental = form.save(commit=False)
                incremental.proposal_id = _id
                incremental.save()
                if incremental.incrp_nom < 0:
                    message = 'Incremental Sales must be greater than 0'
                    incremental.delete()
                else:
                    total_inc = IncrementalSales.objects.filter(proposal_id=_id).aggregate(Sum('incrp_nom'))[
                        'incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
                    total_cost = ProjectedCost.objects.filter(proposal_id=_id).aggregate(Sum('cost'))[
                        'cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
                    proposal.roi = (
                        total_cost / total_inc) * 100 if total_inc != 0 else 0
                    proposal.save()

    return HttpResponseRedirect(reverse('proposal-release-view', args=[_id, '0', 'add-item', message, 0]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_incremental_update(request, _id, _product):
    proposal = Proposal.objects.get(proposal_id=_id)
    update = IncrementalSales.objects.get(proposal_id=_id, id=_product)
    message = '0'
    if request.POST:
        swop_carton = int(request.POST.get('swop_carton'))
        swp_carton = int(request.POST.get('swp_carton'))
        if swop_carton > swp_carton:
            message = 'Sales With Program must be greater than Sales Without Program'
        else:
            swop_carton = update.swop_carton
            swp_carton = update.swp_carton
            swop_nom = update.swop_nom
            swp_nom = update.swp_nom
            update.swop_carton = int(request.POST.get('swop_carton'))
            update.swp_carton = int(request.POST.get('swp_carton'))
            update.swop_nom = int(request.POST.get('swop_nom'))
            update.swp_nom = int(request.POST.get('swp_nom'))
            update.save()
            if update.incrp_nom < 0:
                message = 'Incremental Sales must be greater than 0'
                update.swop_carton = swop_carton
                update.swp_carton = swp_carton
                update.swop_nom = swop_nom
                update.swp_nom = swp_nom
                update.save()
            else:
                total_inc = IncrementalSales.objects.filter(
                    proposal_id=_id).aggregate(Sum('incrp_nom'))['incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
                total_cost = ProjectedCost.objects.filter(
                    proposal_id=_id).aggregate(Sum('cost'))['cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
                proposal.roi = (total_cost / total_inc) * \
                    100 if total_inc != 0 else 0
                proposal.save()

    return HttpResponseRedirect(reverse('proposal-release-view', args=[_id, _product, 'upd-item', message, 0]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_incremental_delete(request, _id, _product):
    proposal = Proposal.objects.get(proposal_id=_id)
    incremental = IncrementalSales.objects.get(
        proposal_id=_id, id=_product)
    incremental.delete()
    total_inc = IncrementalSales.objects.filter(
        proposal_id=_id).aggregate(Sum('incrp_nom'))['incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
    total_cost = ProjectedCost.objects.filter(
        proposal_id=_id).aggregate(Sum('cost'))['cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
    proposal.roi = (total_cost / total_inc) * \
        100 if total_inc != 0 else 0
    proposal.save()

    return HttpResponseRedirect(reverse('proposal-release-view', args=[_id, '0', '0', '0', 0]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_cost_add(request, _id):
    form = FormProjectedCost(request.POST, request.FILES)
    proposal = Proposal.objects.get(proposal_id=_id)
    budget_detail = BudgetDetail.objects.get(
        budget=proposal.budget, budget_channel=proposal.channel)
    message = '0'
    if form.is_valid():
        try:
            check = ProjectedCost.objects.get(
                proposal_id=_id, activities=request.POST.get('activities'))
            if check:
                message = 'Activity already exist'
        except ProjectedCost.DoesNotExist:
            cost = form.save(commit=False)
            if cost.cost > budget_detail.budget_balance:
                message = 'Total cost must be less than or equal to budget balance'
            else:
                cost.proposal_id = _id
                cost.save()
                total_inc = IncrementalSales.objects.filter(
                    proposal_id=_id).aggregate(Sum('incrp_nom'))['incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
                total_cost = ProjectedCost.objects.filter(
                    proposal_id=_id).aggregate(Sum('cost'))['cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
                proposal.roi = (total_cost / total_inc) * \
                    100 if total_inc != 0 else 0
                proposal.total_cost = total_cost
                proposal.balance = total_cost
                proposal.status = 'PENDING'
                proposal.save()
                sum_cost = Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).aggregate(Sum('total_cost'))[
                    'total_cost__sum'] if Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).exists() else 0
                budget_detail.budget_proposed = sum_cost
                budget_detail.save()
                sum_balance = BudgetDetail.objects.filter(budget=proposal.budget).aggregate(Sum('budget_balance'))[
                    'budget_balance__sum'] if BudgetDetail.objects.filter(budget=proposal.budget).exists() else 0
                budget = Budget.objects.get(budget_id=proposal.budget)
                budget.budget_balance = sum_balance
                budget.save()

    return HttpResponseRedirect(reverse('proposal-release-view', args=[_id, '0', 'add-cost', message, 0]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_cost_delete(request, _id, _activities):
    proposal = Proposal.objects.get(proposal_id=_id)
    budget_detail = BudgetDetail.objects.get(
        budget=proposal.budget, budget_channel=proposal.channel)
    cost = ProjectedCost.objects.get(proposal_id=_id, id=_activities)
    cost.delete()
    total_inc = IncrementalSales.objects.filter(
        proposal_id=_id).aggregate(Sum('incrp_nom'))['incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
    total_cost = ProjectedCost.objects.filter(
        proposal_id=_id).aggregate(Sum('cost'))['cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
    proposal.roi = (total_cost / total_inc) * \
        100 if total_inc != 0 else 0
    proposal.total_cost = total_cost
    proposal.balance = total_cost
    proposal.save()
    sum_cost = Proposal.objects.filter(
        budget=proposal.budget, channel=proposal.channel).aggregate(Sum('total_cost'))['total_cost__sum'] if Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).exists() else 0
    budget_detail.budget_proposed = sum_cost
    budget_detail.save()
    sum_balance = BudgetDetail.objects.filter(budget=proposal.budget).aggregate(Sum('budget_balance'))[
        'budget_balance__sum'] if BudgetDetail.objects.filter(budget=proposal.budget).exists() else 0
    budget = Budget.objects.get(budget_id=proposal.budget)
    budget.budget_balance = sum_balance
    budget.save()

    return HttpResponseRedirect(reverse('proposal-release-view', args=[_id, '0', '0', '0', 0]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_cost_update(request, _id, _activities):
    proposal = Proposal.objects.get(proposal_id=_id)
    budget_detail = BudgetDetail.objects.get(
        budget=proposal.budget, budget_channel=proposal.channel)
    update = ProjectedCost.objects.get(
        proposal_id=_id, id=_activities)
    message = '0'
    if request.POST:
        cost = update.cost
        if int(request.POST.get('cost')) > budget_detail.budget_balance + cost:
            message = 'Total cost must be less than or equal to budget balance'
        else:
            update.activities = request.POST.get('activities')
            update.cost = int(request.POST.get('cost'))
            update.save()
            total_inc = IncrementalSales.objects.filter(
                proposal_id=_id).aggregate(Sum('incrp_nom'))['incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
            total_cost = ProjectedCost.objects.filter(
                proposal_id=_id).aggregate(Sum('cost'))['cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
            proposal.roi = (total_cost / total_inc) * \
                100 if total_inc != 0 else 0
            proposal.total_cost = total_cost
            proposal.balance = total_cost
            proposal.save()
            sum_cost = Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).aggregate(Sum('total_cost'))[
                'total_cost__sum'] if Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).exists() else 0
            budget_detail.budget_proposed = sum_cost
            budget_detail.save()
            sum_balance = BudgetDetail.objects.filter(budget=proposal.budget).aggregate(Sum('budget_balance'))[
                'budget_balance__sum'] if BudgetDetail.objects.filter(budget=proposal.budget).exists() else 0
            budget = Budget.objects.get(budget_id=proposal.budget)
            budget.budget_balance = sum_balance
            budget.save()

    return HttpResponseRedirect(reverse('proposal-release-view', args=[_id, _activities, 'upd-cost', message, 0]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_print(request, _id):
    proposal = Proposal.objects.get(proposal_id=_id)
    prop_id = _id.replace('/', '-')

    # Create a new PDF file with landscape orientation
    filename = 'proposal_' + prop_id + '.pdf'
    pdf_file = canvas.Canvas(filename, pagesize=landscape(A4))

    # Set the font and font size
    pdf_file.setFont("Helvetica-Bold", 11)  # Set font to bold

    # Add logo in the top left corner
    logo_path = 'https://aqiqahon.sahabataqiqah.co.id/apps/static/img/logo.png'
    pdf_file.drawImage(logo_path, 25, 515, width=60, height=60)

    # Add title beside the logo in the center of the page
    title = "PROGRAM PROPOSAL"
    title_width = pdf_file.stringWidth(
        title, "Helvetica-Bold", 11)  # Set font to bold
    page_width, _ = landscape(A4)
    title_x = (page_width - title_width) / 2
    pdf_file.setFont("Helvetica-Bold", 11)  # Set font to bold
    pdf_file.drawString(title_x, 545, title)

    # Write the proposal details to the PDF
    y = 510
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, "No.")
    pdf_file.drawString(50, y, ":")
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(60, y, pdf_file._escape(proposal.proposal_id))
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(title_x, y, "Channel")
    pdf_file.drawString(title_x + 40, y, ":")
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(title_x + 50, y, proposal.channel)
    y -= 10
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, "Date")
    pdf_file.drawString(50, y, ":")
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(60, y, proposal.proposal_date.strftime('%d %b %Y'))
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(title_x, y, "Division")
    pdf_file.drawString(title_x + 40, y, ":")
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(title_x + 50, y, proposal.division.division_name)
    y -= 10
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, "Type")
    pdf_file.drawString(50, y, ":")
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(60, y, proposal.type)

    y -= 20
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, "Program Name")
    pdf_file.drawString(90, y, ":")
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(100, y, proposal.program_name)
    y -= 10
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, "Products")
    pdf_file.drawString(90, y, ":")
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(100, y, proposal.products)
    y -= 10
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, "Area")
    pdf_file.drawString(90, y, ":")
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(100, y, proposal.area)
    y -= 10
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, "Period")
    pdf_file.drawString(90, y, ":")
    pdf_file.drawString(100, y, "Start : ")
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(130, y, proposal.period_start.strftime('%d/%m/%Y'))
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(200, y, "End : ")
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(230, y, proposal.period_end.strftime('%d/%m/%Y'))
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(300, y, "Duration : ")
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(350, y, str(proposal.duration) + ' days')
    y -= 10
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    normal_style.fontSize = 8  # Set font size to 8

    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, "Background")
    pdf_file.drawString(90, y, ":")
    pdf_file.setFont("Helvetica", 8)
    background = proposal.background.split('\n')
    y2 = y
    y -= 4
    for line in background:
        background_paragraph = Paragraph(line, normal_style)
        background_paragraph.wrapOn(pdf_file, page_width - 125, 100)
        background_paragraph.drawOn(pdf_file, 100, y)
        y -= 10

    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString((page_width / 2) + 42, y2, "Objectives")
    pdf_file.drawString((page_width / 2) + 87, y2, ":")
    pdf_file.setFont("Helvetica", 8)
    objectives = proposal.objectives.split('\n')
    y2 -= 4
    for line in objectives:
        objectives_paragraph = Paragraph(line, normal_style)
        objectives_paragraph.wrapOn(pdf_file, (page_width - 125) / 2, 100)
        objectives_paragraph.drawOn(pdf_file, (page_width / 2) + 95, y2)
        y2 -= 10

    y = y2 if y2 < y else y

    y += 4
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, "Mechanism")
    pdf_file.drawString(90, y, ":")
    pdf_file.setFont("Helvetica", 8)
    mechanism = proposal.mechanism.split('\n')
    y -= 4
    for line in mechanism:
        mechanism_paragraph = Paragraph(line, normal_style)
        mechanism_paragraph.wrapOn(pdf_file, page_width - 125, 100)
        mechanism_paragraph.drawOn(pdf_file, 100, y)
        y -= 10

    y += 4
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, "Remarks")
    pdf_file.drawString(90, y, ":")
    pdf_file.setFont("Helvetica", 8)
    remarks = proposal.remarks.split('\n')
    y -= 4
    for line in remarks:
        remarks_paragraph = Paragraph(line, normal_style)
        remarks_paragraph.wrapOn(pdf_file, page_width - 125, 100)
        remarks_paragraph.drawOn(pdf_file, 100, y)
        y -= 10

    y += 4
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, "Attachment")
    pdf_file.drawString(90, y, ":")
    pdf_file.setFont("Helvetica", 8)
    if proposal.attachment:
        pdf_file.drawString(100, y, proposal.attachment.name)
    else:
        pdf_file.drawString(100, y, 'None')

    y -= 20
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.setFillColorRGB(1, 0, 0)
    # Set border color to black (RGB: 0, 0, 0)
    pdf_file.setStrokeColorRGB(0, 0, 0)
    # Draw rectangle with specified dimensions
    pdf_file.rect(25, y - 5, page_width - 50, 15, fill=True, stroke=True)

    pdf_file.setFillColorRGB(255, 255, 255)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(title_x, y, "Incremental Sales Projection")

    pdf_file.setFillColorRGB(0, 0, 0)
    y -= 15
    pdf_file.rect(25, y - 20, 100, 30, stroke=True)
    title = "Product"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 75 - (title_width / 2)
    pdf_file.drawString(title_x, y - 6, title)

    pdf_file.rect(125, y - 5, 200, 15, stroke=True)
    title = "Sales Without Program (Rp)"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 225 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(325, y - 5, 200, 15, stroke=True)
    title = "Sales With Program (Rp)"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 425 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(525, y - 5, 150, 15, stroke=True)
    title = "Incremental (Rp)"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 600 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(675, y - 5, 142, 15, stroke=True)
    title = "Incremental (%)"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 746 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    y -= 15
    pdf_file.rect(125, y - 5, 100, 15, stroke=True)
    title = "Carton"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 175 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(225, y - 5, 100, 15, stroke=True)
    title = "Rp"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 275 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(325, y - 5, 100, 15, stroke=True)
    title = "Carton"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 375 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(425, y - 5, 100, 15, stroke=True)
    title = "Rp"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 475 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(525, y - 5, 75, 15, stroke=True)
    title = "Carton"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 562 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(600, y - 5, 75, 15, stroke=True)
    title = "Rp"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 637 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(675, y - 5, 71, 15, stroke=True)
    title = "Carton"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 711 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(746, y - 5, 71, 15, stroke=True)
    title = "Rp"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 782 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    incremental = IncrementalSales.objects.filter(proposal_id=_id)
    pdf_file.setFont("Helvetica", 8)
    for i in incremental:
        y -= 15
        pdf_file.rect(25, y - 5, 100, 15, stroke=True)
        pdf_file.drawString(30, y, i.product)
        pdf_file.rect(125, y - 5, 100, 15, stroke=True)
        pdf_file.drawRightString(220, y, "{:,}".format(i.swop_carton))
        pdf_file.rect(225, y - 5, 100, 15, stroke=True)
        pdf_file.drawRightString(320, y, "{:,}".format(i.swop_nom))
        pdf_file.rect(325, y - 5, 100, 15, stroke=True)
        pdf_file.drawRightString(420, y, "{:,}".format(i.swp_carton))
        pdf_file.rect(425, y - 5, 100, 15, stroke=True)
        pdf_file.drawRightString(520, y, "{:,}".format(i.swp_nom))
        pdf_file.rect(525, y - 5, 75, 15, stroke=True)
        pdf_file.drawRightString(595, y, "{:,}".format(i.incrp_carton))
        pdf_file.rect(600, y - 5, 75, 15, stroke=True)
        pdf_file.drawRightString(670, y, "{:,}".format(i.incrp_nom))
        pdf_file.rect(675, y - 5, 71, 15, stroke=True)
        pdf_file.drawRightString(743, y, "{:,}%".format(i.incpst_carton))
        pdf_file.rect(746, y - 5, 71, 15, stroke=True)
        pdf_file.drawRightString(814, y, "{:,}%".format(i.incpst_nom))

    total = IncrementalSales.objects.filter(proposal_id=_id).aggregate(
        swop_carton__sum=Sum('swop_carton'),
        swop_nom__sum=Sum('swop_nom'),
        swp_carton__sum=Sum('swp_carton'),
        swp_nom__sum=Sum('swp_nom'),
        incrp_carton__sum=Sum('incrp_carton'),
        incrp_nom__sum=Sum('incrp_nom'),
        incpst_carton__ratio=(Sum('incrp_carton') /
                              Sum('swop_carton')) * 100 if Sum('swop_carton') else 0,
        incpst_nom__ratio=(Sum('incrp_nom') /
                           Sum('swop_nom')) * 100 if Sum('swop_nom') else 0,
    )
    y -= 15
    pdf_file.rect(25, y - 5, 100, 15, stroke=True)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(30, y, "Total")
    pdf_file.rect(125, y - 5, 100, 15, stroke=True)
    pdf_file.drawRightString(220, y, "{:,}".format(total['swop_carton__sum']))
    pdf_file.rect(225, y - 5, 100, 15, stroke=True)
    pdf_file.drawRightString(320, y, "{:,}".format(total['swop_nom__sum']))
    pdf_file.rect(325, y - 5, 100, 15, stroke=True)
    pdf_file.drawRightString(420, y, "{:,}".format(total['swp_carton__sum']))
    pdf_file.rect(425, y - 5, 100, 15, stroke=True)
    pdf_file.drawRightString(520, y, "{:,}".format(total['swp_nom__sum']))
    pdf_file.rect(525, y - 5, 75, 15, stroke=True)
    pdf_file.drawRightString(595, y, "{:,}".format(total['incrp_carton__sum']))
    pdf_file.rect(600, y - 5, 75, 15, stroke=True)
    pdf_file.drawRightString(670, y, "{:,}".format(total['incrp_nom__sum']))
    pdf_file.rect(675, y - 5, 71, 15, stroke=True)
    pdf_file.drawRightString(743, y, "{:.1f}%".format(
        total['incpst_carton__ratio']))
    pdf_file.rect(746, y - 5, 71, 15, stroke=True)
    pdf_file.drawRightString(
        814, y, "{:.1f}%".format(total['incpst_nom__ratio']))

    y -= 25
    pdf_file.setFont("Helvetica-Bold", 8)
    # Set fill color to red (RGB: 255, 0, 0)
    pdf_file.setFillColorRGB(1, 0, 0)
    # Set border color to black (RGB: 0, 0, 0)
    pdf_file.setStrokeColorRGB(0, 0, 0)
    # Draw rectangle with specified dimensions
    pdf_file.rect(25, y - 5, (page_width / 2) +
                  50, 15, fill=True, stroke=True)

    pdf_file.setFillColorRGB(255, 255, 255)
    pdf_file.setFont("Helvetica-Bold", 8)
    title = "Projected Cost"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 25 + (((page_width / 2) + 50) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFillColorRGB(1, 0, 0)
    pdf_file.rect((page_width / 2) + 90, y - 5,
                  (page_width / 2) - 115, 15, fill=True, stroke=True)
    pdf_file.setFillColorRGB(255, 255, 255)
    title = "ROI"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = ((page_width / 2) + 90) + \
        (((page_width / 2) - 115) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    y -= 15
    pdf_file.setFillColorRGB(0, 0, 0)
    pdf_file.rect(25, y - 5, 350, 15, stroke=True)
    title = "Activities"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 200 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(375, y - 5, 121, 15, stroke=True)
    title = "Cost"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 435 - (title_width / 2)
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont("Helvetica", 8)
    pdf_file.rect((page_width / 2) + 90, y - 5, 175, 15, stroke=True)
    pdf_file.drawString(
        (page_width / 2) + 95, y, "Projected Cost")
    pdf_file.rect((page_width / 2) + 265, y - 5, 131, 15, stroke=True)
    pdf_file.drawRightString(
        (page_width / 2) + 390, y, "{:,}".format(proposal.total_cost))

    cost = ProjectedCost.objects.filter(proposal_id=_id)

    y -= 15
    y1 = y
    pdf_file.setFont("Helvetica", 8)
    pdf_file.rect((page_width / 2) + 90, y - 5, 175, 15, stroke=True)
    pdf_file.drawString(
        (page_width / 2) + 95, y, "Incremental Sales Projection")
    pdf_file.rect((page_width / 2) + 265, y - 5, 131, 15, stroke=True)
    pdf_file.drawRightString(
        (page_width / 2) + 390, y, "{:,}".format(total['incrp_nom__sum']))

    y -= 15
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.rect((page_width / 2) + 90, y - 5, 175, 15, stroke=True)
    pdf_file.drawString(
        (page_width / 2) + 95, y, "ROI")
    pdf_file.rect((page_width / 2) + 265, y - 5, 131, 15, stroke=True)
    pdf_file.drawRightString(
        (page_width / 2) + 390, y, "{:,}%".format(proposal.roi))

    pdf_file.setFont("Helvetica", 8)
    for i in cost:
        pdf_file.rect(25, y1 - 5, 350, 15, stroke=True)
        pdf_file.drawString(30, y1, i.activities)
        pdf_file.rect(375, y1 - 5, 121, 15, stroke=True)
        pdf_file.drawRightString(490, y1, "{:,}".format(i.cost))
        y1 -= 15

    pdf_file.rect(25, y1 - 5, 350, 15, stroke=True)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(30, y1, "Total")
    pdf_file.rect(375, y1 - 5, 121, 15, stroke=True)
    pdf_file.drawRightString(490, y1, "{:,}".format(proposal.total_cost))

    y = y1
    y -= 25
    col_width = (page_width - 50) / 11
    proposal = Proposal.objects.get(proposal_id=_id)
    approver = ProposalRelease.objects.filter(
        proposal_id=_id, proposal_approval_status='Y', printed=True).order_by('sequence')
    proposer = ProposalRelease.objects.filter(proposal_id=_id, proposal_approval_status='Y', as_approved='proposer', printed=True).aggregate(
        id=Count('id')) if ProposalRelease.objects.filter(proposal_id=_id, proposal_approval_status='Y', as_approved='proposer', printed=True).exists() else 0
    checker = ProposalRelease.objects.filter(proposal_id=_id, proposal_approval_status='Y', as_approved='checker', printed=True).aggregate(
        id=Count('id')) if ProposalRelease.objects.filter(proposal_id=_id, proposal_approval_status='Y', as_approved='checker', printed=True).exists() else 0
    approvers = ProposalRelease.objects.filter(proposal_id=_id, proposal_approval_status='Y', as_approved='approver', printed=True).aggregate(
        id=Count('id')) if ProposalRelease.objects.filter(proposal_id=_id, proposal_approval_status='Y', as_approved='approver', printed=True).exists() else 0
    validator = ProposalRelease.objects.filter(proposal_id=_id, proposal_approval_status='Y', as_approved='validator', printed=True).aggregate(
        id=Count('id')) if ProposalRelease.objects.filter(proposal_id=_id, proposal_approval_status='Y', as_approved='validator', printed=True).exists() else 0
    finalizer = ProposalRelease.objects.filter(proposal_id=_id, proposal_approval_status='Y', as_approved='finalizer', printed=True).aggregate(
        id=Count('id')) if ProposalRelease.objects.filter(proposal_id=_id, proposal_approval_status='Y', as_approved='finalizer', printed=True).exists() else 0

    proposer_count = proposer['id'] if proposer else 0
    checker_count = checker['id'] if checker else 0
    approvers_count = approvers['id'] if approvers else 0
    validator_count = validator['id'] if validator else 0
    finalizer_count = finalizer['id'] if finalizer else 0

    pdf_file.setFont("Helvetica", 8)
    pdf_file.rect(
        25, y - 5, (col_width * (proposer_count + 1)), 15, stroke=True)
    title = 'Proposed By' if proposer_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + ((col_width * (proposer_count + 1)) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(
        25 + (col_width * (proposer_count + 1)), y - 5, col_width * checker_count, 15, stroke=True)
    title = 'Checked By' if checker_count > 0 else ''
    title_x = 25 + (col_width * (proposer_count + 1)) + \
        ((col_width * checker_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(
        25 + (col_width * (proposer_count + 1)) + (col_width * checker_count), y - 5, col_width * approvers_count, 15, stroke=True)
    title = 'Approved By' if approvers_count > 0 else ''
    title_x = 25 + (col_width * (proposer_count + 1)) + \
        (col_width * checker_count) + \
        ((col_width * approvers_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(
        25 + (col_width * (proposer_count + 1)) + (col_width * checker_count) + (col_width * approvers_count), y - 5, col_width * validator_count, 15, stroke=True)
    title = 'Validated By' if validator_count > 0 else ''
    title_x = 25 + (col_width * (proposer_count + 1)) + (col_width * checker_count) + \
        (col_width * approvers_count) + \
        ((col_width * validator_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(
        25 + (col_width * (proposer_count + 1)) + (col_width * checker_count) + (col_width * approvers_count) + (col_width * validator_count), y - 5, col_width * finalizer_count, 15, stroke=True)
    title = 'Approved By' if finalizer_count > 0 else ''
    title_x = 25 + (col_width * (proposer_count + 1)) + (col_width * checker_count) + (col_width * approvers_count) + \
        (col_width * validator_count) + \
        ((col_width * finalizer_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(25, y - 55, col_width, 50, stroke=True)
    sign_path = User.objects.get(user_id=proposal.entry_by).signature.path if User.objects.get(
        user_id=proposal.entry_by).signature else ''
    if sign_path:
        pdf_file.drawImage(sign_path, 30, y - 50,
                           width=col_width - 10, height=40)
    else:
        pass
    pdf_file.rect(25, y - 70, col_width, 15, stroke=True)
    title = proposal.entry_pos
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 25 + (col_width - title_width) / 2
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(title_x, y - 65, title)
    pdf_file.rect(25, y - 85, col_width, 15, stroke=True)
    pdf_file.setFont("Helvetica", 8)
    title = 'Date: ' + proposal.entry_date.strftime('%d/%m/%Y')
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width - title_width) / 2
    pdf_file.drawString(title_x, y - 80, title)

    for i in range(1, approver.count() + 1):
        pdf_file.rect(25 + (col_width * i), y - 55, col_width, 50, stroke=True)
        if approver:
            sign_path = User.objects.get(user_id=approver[i - 1].proposal_approval_id).signature.path if User.objects.get(
                user_id=approver[i - 1].proposal_approval_id).signature else ''
            if sign_path:
                pdf_file.drawImage(sign_path, 30 + (col_width * i), y - 50,
                                   width=col_width - 10, height=40)
            else:
                pass
            pdf_file.rect(25 + (col_width * i), y - 70,
                          col_width, 15, stroke=True)
            title = approver[i - 1].proposal_approval_position
            title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
            title_x = 25 + (col_width * i) + (col_width - title_width) / 2
            pdf_file.setFont("Helvetica-Bold", 8)
            pdf_file.drawString(title_x, y - 65, title)
            pdf_file.rect(25 + (col_width * i), y - 85,
                          col_width, 15, stroke=True)
            pdf_file.setFont("Helvetica", 8)
            title = 'Date: ' + \
                approver[i - 1].proposal_approval_date.strftime('%d/%m/%Y')
            title_width = pdf_file.stringWidth(title, "Helvetica", 8)
            title_x = 25 + (col_width * i) + (col_width - title_width) / 2
            pdf_file.drawString(title_x, y - 80, title)
        else:
            pass

    pdf_file.save()

    # Assuming `proposal.attachment` contains the file path of the attachment
    attachment_path = proposal.attachment.path if proposal.attachment else ''

    if attachment_path:
        # Create a PdfFileMerger object
        merger = PdfMerger()

        # Add the existing PDF file to the merger
        merger.append(filename)

        # Add the attachment page to the merger
        merger.append(attachment_path)

        # Save the merged PDF file
        merger.write(filename)

    return FileResponse(open(filename, 'rb'), content_type='application/pdf')


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-RELEASE')
def budget_release_approve(request, _id):
    release = BudgetRelease.objects.get(
        budget_id=_id, budget_approval_id=request.user.user_id)
    release.budget_approval_status = 'Y'
    release.budget_approval_date = timezone.now()
    release.save()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT budget_id, MAX(sequence) AS seq FROM apps_budgetrelease GROUP BY budget_id HAVING budget_id = '" + str(_id) + "'")
        max_seq = cursor.fetchall()

    budget = Budget.objects.get(budget_id=_id)
    if release.sequence == max_seq[0][1]:
        budget.budget_status = 'OPEN'
    else:
        budget.budget_status = 'IN APPROVAL'

        email = BudgetRelease.objects.filter(budget_id=_id, budget_approval_status='N').order_by(
            'sequence').values_list('budget_approval_email', flat=True)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT budget_approval_name FROM apps_budgetrelease WHERE budget_id = '" + str(_id) + "' AND budget_approval_status = 'N' ORDER BY sequence LIMIT 1")
            approver = cursor.fetchone()

        subject = 'Budget Approval'
        message = 'Dear ' + approver[0] + ',\n\nYou have a budget to approve. Please check your dashboard.\n\n' + \
            'Click this link to approve, revise or return the budget.\n' + host.url + 'budget_release/view/' + str(_id) + '/NONE/0/' + \
            '\n\nThank you.'
        send_email(subject, message, [email[0]])

    budget.save()

    return HttpResponseRedirect(reverse('budget-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_approve(request, _id):
    proposal = Proposal.objects.get(proposal_id=_id)
    release = ProposalRelease.objects.get(
        proposal_id=_id, proposal_approval_id=request.user.user_id)
    release.proposal_approval_status = 'Y'
    release.proposal_approval_date = timezone.now()
    release.save()
    highest_approval = ProposalRelease.objects.filter(
        proposal_id=_id, limit__gt=proposal.total_cost).aggregate(Min('sequence')) if ProposalRelease.objects.filter(proposal_id=_id, limit__gt=proposal.total_cost).exists() else ProposalRelease.objects.filter(proposal_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = ProposalRelease.objects.filter(
            proposal_id=_id, sequence__lt=highest_sequence).order_by('sequence').last()
    else:
        approval = ProposalRelease.objects.filter(
            proposal_id=_id).order_by('sequence').last()

    if release.sequence == approval.sequence:
        proposal.status = 'OPEN'

        recipients = []

        maker = proposal.entry_by
        maker_mail = User.objects.get(user_id=maker).email
        recipients.append(maker_mail)

        approvers = ProposalRelease.objects.filter(
            proposal_id=_id, notif=True, proposal_approval_status='Y')
        for i in approvers:
            recipients.append(i.proposal_approval_email)

        subject = 'Proposal Approved'
        msg = 'Dear All,\n\nProposal No. ' + str(_id) + ' has been approved.\n\nClick the following link to view the proposal.\n' + host.url + 'proposal/view/open/' + str(_id) + '/0/0/0/' + \
            '\n\nThank you.'
        recipient_list = list(dict.fromkeys(recipients))
        send_email(subject, msg, recipient_list)
    else:
        proposal.status = 'IN APPROVAL'

        email = ProposalRelease.objects.filter(proposal_id=_id, proposal_approval_status='N').order_by(
            'sequence').values_list('proposal_approval_email', flat=True)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT proposal_approval_name FROM apps_proposalrelease WHERE proposal_id = '" + str(_id) + "' AND proposal_approval_status = 'N' ORDER BY sequence LIMIT 1")
            approver = cursor.fetchone()

        subject = 'Proposal Approval'
        msg = 'Dear ' + approver[0] + ',\n\nYou have a new proposal to approve. Please check your proposal release list.\n\n' + \
            'Click this link to approve, revise, return or reject this proposal.\n' + host.url + 'proposal_release/view/' + str(_id) + '/0/0/0/0/' + \
            '\n\nThank you.'
        send_email(subject, msg, [email[0]])

    proposal.save()

    return HttpResponseRedirect(reverse('proposal-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-RELEASE')
def budget_release_return(request, _id):
    recipients = []

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT budget_id, email FROM apps_budget INNER JOIN apps_user ON apps_budget.entry_by = apps_user.user_id WHERE budget_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT budget_id, email FROM apps_budget INNER JOIN apps_user ON apps_budget.update_by = apps_user.user_id WHERE budget_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        recipients.append(update_mail[1])

        cursor.execute(
            "SELECT budget_id, email FROM apps_budgetdetail INNER JOIN apps_user ON apps_budgetdetail.update_by = apps_user.user_id WHERE budget_id = '" + str(_id) + "'")
        detail_mail = cursor.fetchone()
        recipients.append(detail_mail[1])

        cursor.execute(
            "SELECT budget_id, budget_approval_email FROM apps_budgetrelease WHERE budget_id = '" + str(_id) + "' AND budget_approval_status = 'Y'")
        approver_mail = cursor.fetchone()
        if approver_mail:
            recipients.append(approver_mail[1])

    try:
        release = BudgetRelease.objects.filter(
            budget_id=_id, budget_approval_status='Y')
        for i in release:
            i.budget_approval_status = 'N'
            i.budget_approval_date = None
            i.upping_note = ''
            i.percentage_note = ''
            i.save()
    except BudgetRelease.DoesNotExist:
        pass

    note = BudgetRelease.objects.get(
        budget_id=_id, budget_approval_id=request.user.user_id)
    note.return_note = request.POST.get('return_note')
    note.save()

    budget = Budget.objects.get(budget_id=_id)
    budget.budget_status = 'DRAFT'
    budget.save()

    subject = 'Budget Returned'
    message = 'Dear All,\n\nBudget No. ' + str(_id) + ' has been returned.\n\nNote: ' + \
        str(note.return_note) + '\n\nClick the following link to revise the budget.\n' + host.url + 'budget/view/draft/' + \
        str(_id) + '/NONE/' + \
        '\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, message, recipient_list)

    return HttpResponseRedirect(reverse('budget-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_return(request, _id):
    recipients = []
    draft = False

    try:
        return_to = ProposalRelease.objects.get(
            proposal_id=_id, return_to=True, sequence__lt=ProposalRelease.objects.get(proposal_id=_id, proposal_approval_id=request.user.user_id).sequence)

        if return_to:
            approvers = ProposalRelease.objects.filter(
                proposal_id=_id, sequence__gte=ProposalRelease.objects.get(proposal_id=_id, return_to=True).sequence, sequence__lt=ProposalRelease.objects.get(proposal_id=_id, proposal_approval_id=request.user.user_id).sequence)
    except ProposalRelease.DoesNotExist:
        approvers = ProposalRelease.objects.filter(
            proposal_id=_id, sequence__lte=ProposalRelease.objects.get(proposal_id=_id, proposal_approval_id=request.user.user_id).sequence)
        draft = True

    for i in approvers:
        recipients.append(i.proposal_approval_email)
        i.proposal_approval_status = 'N'
        i.proposal_approval_date = None
        i.revise_note = ''
        i.return_note = ''
        i.reject_note = ''
        i.mail_sent = False
        i.save()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT proposal_id, email FROM apps_proposal INNER JOIN apps_user ON apps_proposal.entry_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT proposal_id, email FROM apps_proposal INNER JOIN apps_user ON apps_proposal.update_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

        cursor.execute(
            "SELECT proposal_id, email FROM apps_incrementalsales INNER JOIN apps_user ON apps_incrementalsales.update_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
        incremental_mail = cursor.fetchone()
        if incremental_mail:
            recipients.append(incremental_mail[1])

        cursor.execute(
            "SELECT proposal_id, email FROM apps_projectedcost INNER JOIN apps_user ON apps_projectedcost.update_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
        cost_mail = cursor.fetchone()
        if cost_mail:
            recipients.append(cost_mail[1])

    note = ProposalRelease.objects.get(
        proposal_id=_id, proposal_approval_id=request.user.user_id)
    note.return_note = request.POST.get('return_note')
    note.save()

    subject = 'Proposal Returned'
    msg = 'Dear All,\n\nProposal No. ' + str(_id) + ' has been returned.\n\nNote: ' + \
        str(note.return_note) + \
        '\n\nClick the following link to revise the proposal.\n'

    if draft:
        proposal = Proposal.objects.get(proposal_id=_id)
        proposal.status = 'DRAFT'
        proposal.save()
        msg += host.url + 'proposal/view/draft/' + str(_id) + '/0/0/0/' + \
            '\n\nThank you.'
    else:
        msg += host.url + 'proposal_release/view/' + \
            str(_id) + '/0/0/0/0/\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('proposal-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def proposal_release_reject(request, _id):
    recipients = []

    try:
        approvers = ProposalRelease.objects.filter(
            proposal_id=_id, sequence__lt=ProposalRelease.objects.get(proposal_id=_id, proposal_approval_id=request.user.user_id).sequence)
    except ProposalRelease.DoesNotExist:
        pass

    for i in approvers:
        recipients.append(i.proposal_approval_email)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT proposal_id, email FROM apps_proposal INNER JOIN apps_user ON apps_proposal.entry_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT proposal_id, email FROM apps_proposal INNER JOIN apps_user ON apps_proposal.update_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

        cursor.execute(
            "SELECT proposal_id, email FROM apps_incrementalsales INNER JOIN apps_user ON apps_incrementalsales.update_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
        incremental_mail = cursor.fetchone()
        if incremental_mail:
            recipients.append(incremental_mail[1])

        cursor.execute(
            "SELECT proposal_id, email FROM apps_projectedcost INNER JOIN apps_user ON apps_projectedcost.update_by = apps_user.user_id WHERE proposal_id = '" + str(_id) + "'")
        cost_mail = cursor.fetchone()
        if cost_mail:
            recipients.append(cost_mail[1])

    note = ProposalRelease.objects.get(
        proposal_id=_id, proposal_approval_id=request.user.user_id)
    note.reject_note = request.POST.get('reject_note')
    note.save()

    subject = 'Proposal Rejected'
    msg = 'Dear All,\n\nProposal No. ' + str(_id) + ' has been rejected.\n\nNote: ' + \
        str(note.reject_note) + \
        '\n\nClick the following link to see the proposal.\n'

    proposal = Proposal.objects.get(proposal_id=_id)
    proposal.status = 'REJECTED'
    proposal.save()
    sum_cost = Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).exclude(status__in=['CLOSED', 'REJECTED']).aggregate(Sum('total_cost'))[
        'total_cost__sum'] if Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).exclude(status__in=['CLOSED', 'REJECTED']).exists() else 0
    budget_detail = BudgetDetail.objects.get(
        budget=proposal.budget, budget_channel=proposal.channel)
    budget_detail.budget_proposed = sum_cost
    budget_detail.save()
    sum_balance = BudgetDetail.objects.filter(budget=proposal.budget).aggregate(Sum('budget_balance'))[
        'budget_balance__sum'] if BudgetDetail.objects.filter(budget=proposal.budget).exists() else 0
    budget = Budget.objects.get(budget_id=proposal.budget)
    budget.budget_balance = sum_balance
    budget.save()

    msg += host.url + 'proposal/view/reject/' + str(_id) + '/0/0/0/' + \
        '\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('proposal-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-APPROVAL')
def budget_approval_index(request):
    areas = AreaSales.objects.all()

    context = {
        'data': areas,
        'segment': 'budget_approval',
        'group_segment': 'approval',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/budget_approval_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-APPROVAL')
def proposal_matrix_index(request):
    areas = AreaSales.objects.all()

    context = {
        'data': areas,
        'segment': 'proposal_matrix',
        'group_segment': 'approval',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PROPOSAL-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/proposal_matrix_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-APPROVAL')
def budget_approval_view(request, _id):
    area = AreaSales.objects.get(area_id=_id)
    approvers = BudgetApproval.objects.filter(area_id=_id)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, position_name, q_budgetapprover.approver_id FROM apps_user INNER JOIN apps_position ON apps_user.position_id = apps_position.position_id LEFT JOIN (SELECT * FROM apps_budgetapproval WHERE area_id = '" + str(_id) + "') AS q_budgetapprover ON apps_user.user_id = q_budgetapprover.approver_id WHERE q_budgetapprover.approver_id IS NULL")
        users = cursor.fetchall()

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in users:
            if str(i[0]) in check:
                try:
                    approver = BudgetApproval(area_id=_id, approver_id=i[0])
                    approver.save()
                except IntegrityError:
                    continue
            else:
                BudgetApproval.objects.filter(
                    area_id=_id, approver_id=i[0]).delete()

        return HttpResponseRedirect(reverse('budget-approval-view', args=[_id, ]))

    context = {
        'data': area,
        'users': users,
        'approvers': approvers,
        'segment': 'budget_approval',
        'group_segment': 'approval',
        'tab': 'auth',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/budget_approval_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-APPROVAL')
def proposal_matrix_view(request, _id, _channel):
    area = AreaSales.objects.get(area_id=_id)
    channels = AreaChannelDetail.objects.filter(area_id=_id, status=1)
    approvers = ProposalMatrix.objects.filter(area_id=_id, channel_id=_channel)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, position_name, q_proposalmatrix.approver_id FROM apps_user INNER JOIN apps_position ON apps_user.position_id = apps_position.position_id LEFT JOIN (SELECT * FROM apps_proposalmatrix WHERE area_id = '" + str(_id) + "' AND channel_id = '" + str(_channel) + "') AS q_proposalmatrix ON apps_user.user_id = q_proposalmatrix.approver_id WHERE q_proposalmatrix.approver_id IS NULL")
        users = cursor.fetchall()

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in users:
            if str(i[0]) in check:
                try:
                    approver = ProposalMatrix(
                        area_id=_id, channel_id=_channel, approver_id=i[0])
                    approver.save()
                except IntegrityError:
                    continue
            else:
                ProposalMatrix.objects.filter(
                    area_id=_id, channel_id=_channel, approver_id=i[0]).delete()

        return HttpResponseRedirect(reverse('proposal-matrix-view', args=[_id, _channel]))

    context = {
        'data': area,
        'channels': channels,
        'users': users,
        'approvers': approvers,
        'channel': _channel,
        'segment': 'proposal_matrix',
        'group_segment': 'approval',
        'tab': 'auth',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PROPOSAL-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/proposal_matrix_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-APPROVAL')
def budget_approval_update(request, _id, _approver):
    approvers = BudgetApproval.objects.get(area=_id, approver_id=_approver)

    if request.POST:
        approvers.sequence = int(request.POST.get('sequence'))
        approvers.save()

        return HttpResponseRedirect(reverse('budget-approval-view', args=[_id, ]))

    return render(request, 'home/budget_approval_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-APPROVAL')
def proposal_matrix_update(request, _id, _channel, _approver):
    approvers = ProposalMatrix.objects.get(
        area=_id, channel_id=_channel, approver_id=_approver)

    if request.POST:
        approvers.sequence = int(request.POST.get('sequence'))
        approvers.limit = int(request.POST.get('limit'))
        approvers.return_to = True if request.POST.get('return') else False
        approvers.approve = True if request.POST.get('approve') else False
        approvers.revise = True if request.POST.get('revise') else False
        approvers.returned = True if request.POST.get('returned') else False
        approvers.reject = True if request.POST.get('reject') else False
        approvers.notif = True if request.POST.get('notif') else False
        approvers.printed = True if request.POST.get('printed') else False
        approvers.as_approved = request.POST.get('as_approved')
        approvers.save()

        return HttpResponseRedirect(reverse('proposal-matrix-view', args=[_id, _channel]))

    return render(request, 'home/proposal_matrix_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-APPROVAL')
def budget_approval_delete(request, _id, _arg):
    approvers = BudgetApproval.objects.get(area=_id, approver_id=_arg)
    approvers.delete()

    return HttpResponseRedirect(reverse('budget-approval-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-APPROVAL')
def proposal_matrix_delete(request, _id, _channel, _arg):
    approvers = ProposalMatrix.objects.get(
        area=_id, channel_id=_channel, approver_id=_arg)
    approvers.delete()

    return HttpResponseRedirect(reverse('proposal-matrix-view', args=[_id, _channel]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLOSING-PERIOD')
def closing_index(request):
    periods = Closing.objects.all()

    context = {
        'data': periods,
        'segment': 'closing_period',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLOSING-PERIOD') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/closing_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLOSING-PERIOD')
def closing_add(request):
    if request.POST:
        form = FormClosing(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('closing-index'))
    else:
        last_month = (datetime.datetime(datetime.datetime.now(
        ).year, datetime.datetime.now().month, 1) - datetime.timedelta(days=1)).month
        last_year = (datetime.datetime(datetime.datetime.now(
        ).year, datetime.datetime.now().month, 1) - datetime.timedelta(days=1)).year

        form = FormClosing(initial={'year_closed': last_year, 'month_closed': last_month,
                           'year_open': datetime.datetime.now().year, 'month_open': datetime.datetime.now().month})

    context = {
        'form': form,
        'segment': 'closing_period',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLOSING-PERIOD') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/closing_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLOSING-PERIOD')
def closing_update(request, _id):
    period = Closing.objects.get(document=_id)

    if request.POST:
        form = FormClosingUpdate(request.POST, request.FILES, instance=period)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('closing-view', args=[_id, ]))
    else:
        form = FormClosingUpdate(instance=period)

    YEAR_CHOICES = []
    for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append(str(r))

    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append(str(r))

    context = {
        'form': form,
        'data': period,
        'years': YEAR_CHOICES,
        'months': MONTH_CHOICES,
        'segment': 'closing_period',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLOSING-PERIOD') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/closing_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLOSING-PERIOD')
def closing_delete(request, _id):
    periods = Closing.objects.get(document=_id)
    periods.delete()

    return HttpResponseRedirect(reverse('closing-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLOSING-PERIOD')
def closing_view(request, _id):
    period = Closing.objects.get(document=_id)
    form = FormClosingView(instance=period)

    YEAR_CHOICES = []
    for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append(str(r))

    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append(str(r))

    context = {
        'data': period,
        'form': form,
        'years': YEAR_CHOICES,
        'months': MONTH_CHOICES,
        'segment': 'closing_period',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLOSING-PERIOD') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/closing_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='BUDGET-CLOSING')
def closing(request):
    message = '0'
    period = None
    try:
        period = Closing.objects.get(document='BUDGET')
    except Closing.DoesNotExist:
        message = 'Document Budget not found, add document Budget Closing Period first.'
    budgets = Budget.objects.filter(budget_status='OPEN')
    proposals = Proposal.objects.filter(status__in=['PENDING', 'IN APPROVAL'])

    if request.POST:
        if proposals:
            message = 'There are still proposals in approval process. Please approve or reject them first.'
        else:
            period.year_closed = request.POST.get('year_closed')
            period.month_closed = request.POST.get('month_closed')
            next_month = (datetime.datetime(int(period.year_closed),
                                            int(period.month_closed), 1) + datetime.timedelta(days=32)).month
            next_year = (datetime.datetime(int(period.year_closed),
                                           int(period.month_closed), 1) + datetime.timedelta(days=32)).year
            period.year_open = next_year
            period.month_open = next_month
            period.save()
            for budget in budgets:
                detail = BudgetDetail.objects.filter(
                    budget_id=budget.budget_id)
                total_amount = 0
                for i in detail:
                    total_amount += i.budget_balance

                new_budget = Budget(
                    budget_year=str(next_year),
                    budget_month='{:02d}'.format(next_month),
                    budget_area=budget.budget_area,
                    budget_distributor=budget.budget_distributor,
                    budget_amount=total_amount,
                    budget_upping=0,
                    budget_status='DRAFT')
                new_budget.save()

                for i in detail:
                    new_detail = BudgetDetail(
                        budget_id=new_budget.budget_id,
                        budget_channel=i.budget_channel,
                        budget_amount=i.budget_balance)
                    new_detail.save()

                approvers = BudgetApproval.objects.filter(
                    area_id=new_budget.budget_area).order_by('sequence')
                for approver in approvers:
                    new_release = BudgetRelease(
                        budget_id=new_budget.budget_id,
                        budget_approval_id=approver.approver_id,
                        budget_approval_name=approver.approver.username,
                        budget_approval_email=approver.approver.email,
                        budget_approval_position=approver.approver.position.position_name,
                        sequence=approver.sequence)
                    new_release.save()

                budget.budget_status = 'CLOSED'
                budget.save()

            context = {
                'data': period,
                'month': period.month_closed,
                'year': period.year_closed,
                'next_month': next_month,
                'next_year': next_year,
                'total': budgets.count(),
                'segment': 'budget_closing',
                'group_segment': 'budget',
                'crud': 'index',
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET-CLOSING') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/budget_closingreport.html', context)

    YEAR_CHOICES = []
    for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append(str(r))

    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append(str(r))

    context = {
        'data': period,
        'message': message,
        'segment': 'budget_closing',
        'years': YEAR_CHOICES,
        'months': MONTH_CHOICES,
        'group_segment': 'budget',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='BUDGET-CLOSING') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/closing.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DIVISION')
def division_index(request):
    divisions = Division.objects.all()

    context = {
        'data': divisions,
        'segment': 'division',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DIVISION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/division_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DIVISION')
def division_add(request):
    if request.POST:
        form = FormDivision(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('division-index'))
    else:
        form = FormDivision()

    context = {
        'form': form,
        'segment': 'division',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DIVISION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/division_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DIVISION')
def division_update(request, _id):
    division = Division.objects.get(division_id=_id)

    if request.POST:
        form = FormDivisionUpdate(
            request.POST, request.FILES, instance=division)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('division-index'))
    else:
        form = FormDivisionUpdate(instance=division)

    context = {
        'form': form,
        'data': division,
        'segment': 'division',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DIVISION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/division_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DIVISION')
def division_delete(request, _id):
    division = Division.objects.get(division_id=_id)
    division.delete()

    return HttpResponseRedirect(reverse('division-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='DIVISION')
def division_view(request, _id):
    division = Division.objects.get(division_id=_id)
    form = FormDivisionView(instance=division)

    context = {
        'data': division,
        'form': form,
        'segment': 'division',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DIVISION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/division_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_index(request, _tab):
    drafts = Proposal.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').all
    draft_count = Proposal.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').count
    pendings = Proposal.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').all
    pending_count = Proposal.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').count
    inapprovals = Proposal.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').all
    inapproval_count = Proposal.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').count
    opens = Proposal.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').all
    open_count = Proposal.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').count

    context = {
        'drafts': drafts,
        'draft_count': draft_count,
        'pendings': pendings,
        'pending_count': pending_count,
        'inapprovals': inapprovals,
        'inapproval_count': inapproval_count,
        'opens': opens,
        'open_count': open_count,
        'tab': _tab,
        'segment': 'proposal',
        'group_segment': 'proposal',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROPOSAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/proposal_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-ARCHIVE')
def proposal_archive_index(request, _tab):
    closes = Proposal.objects.filter(status='CLOSED', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').all
    close_count = Proposal.objects.filter(status='CLOSED', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').count
    rejects = Proposal.objects.filter(status='REJECTED', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').all
    reject_count = Proposal.objects.filter(status='REJECTED', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-proposal_id').count

    context = {
        'closes': closes,
        'close_count': close_count,
        'rejects': rejects,
        'reject_count': reject_count,
        'tab': _tab,
        'segment': 'proposal_archive',
        'group_segment': 'proposal',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROPOSAL-ARCHIVE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/proposal_archive.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_add(request, _area, _budget, _channel):
    selected_area = _area
    selected_budget = _budget
    selected_channel = _channel
    area = AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', 'area__area_name')
    name = AreaSales.objects.get(
        area_id=selected_area) if selected_area != '0' else None
    divs = Division.objects.all()
    budgets = Budget.objects.filter(budget_balance__gt=0, budget_status='OPEN',
                                    budget_area=selected_area) if selected_area != '0' else None
    budget_detail = BudgetDetail.objects.filter(
        budget_id=selected_budget) if selected_budget != '0' else None
    distributor = Budget.objects.get(
        budget_id=selected_budget).budget_distributor_id if selected_budget != '0' else None
    message = ''
    no_save = False
    if selected_area != '0' and selected_channel != '0':
        approvers = ProposalMatrix.objects.filter(
            area_id=_area, channel_id=_channel).order_by('sequence')
        if approvers.count() == 0 or approvers[0].limit > 0:
            message = "No proposal's approver found for this area and channel."
            no_save = True

    try:
        _no = Proposal.objects.all().order_by('seq_number').last()
    except Proposal.DoesNotExist:
        _no = None
    if _no is None:
        format_no = '{:04d}'.format(1)
    else:
        format_no = '{:04d}'.format(_no.seq_number + 1)

    _id = 'PBS-2' + format_no + '/' + selected_channel + '/' + selected_area + '/' + \
        str(distributor) + '/' + \
        str(datetime.datetime.now().strftime('%m')) + \
        '/' + str(datetime.datetime.now().year)

    if request.method == 'POST':
        form = FormProposal(request.POST, request.FILES)
        if form.is_valid():
            parent = form.save(commit=False)
            parent.duration = form.cleaned_data['period_end'] - \
                form.cleaned_data['period_start']
            if parent.duration.days < 0:
                message = 'Period end must be greater than period start.'
            else:
                parent.budget_id = selected_budget
                parent.channel = selected_channel
                parent.attachment = form.cleaned_data['attachment']
                parent.status = 'DRAFT'
                parent.seq_number = _no.seq_number + 1 if _no else 1
                parent.entry_pos = request.user.position.position_id
                parent.save()

                if not settings.DEBUG:
                    proposal = Proposal.objects.get(
                        proposal_id=parent.proposal_id)
                    if proposal.attachment:
                        my_file = proposal.attachment
                        filename = '../../www/aqiqahon/apps/media/' + my_file.name
                        with open(filename, 'wb+') as temp_file:
                            for chunk in my_file.chunks():
                                temp_file.write(chunk)

                for approver in approvers:
                    release = ProposalRelease(
                        proposal_id=parent.proposal_id,
                        proposal_approval_id=approver.approver_id,
                        proposal_approval_name=approver.approver.username,
                        proposal_approval_email=approver.approver.email,
                        proposal_approval_position=approver.approver.position.position_id,
                        sequence=approver.sequence,
                        limit=approver.limit,
                        return_to=approver.return_to,
                        approve=approver.approve,
                        revise=approver.revise,
                        returned=approver.returned,
                        reject=approver.reject,
                        notif=approver.notif,
                        printed=approver.printed,
                        as_approved=approver.as_approved)
                    release.save()

                return HttpResponseRedirect(reverse('proposal-view', args=['draft', parent.proposal_id, '0', '0', '0']))
    else:
        form = FormProposal(
            initial={'proposal_id': _id, 'area': selected_area, 'period_start': datetime.datetime.now().date(), 'period_end': datetime.datetime.now().date()})

    msg = form.errors
    context = {
        'form': form,
        'area': area,
        'name': name,
        'divs': divs,
        'budgets': budgets,
        'budget_detail': budget_detail,
        'selected_area': selected_area,
        'selected_budget': selected_budget,
        'selected_channel': selected_channel,
        'msg': msg,
        'message': message,
        'no_save': no_save,
        'segment': 'proposal',
        'group_segment': 'proposal',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROPOSAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/proposal_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_view(request, _tab, _id, _sub_id, _act, _msg):
    proposal = Proposal.objects.get(proposal_id=_id)
    budget = BudgetDetail.objects.get(
        budget=proposal.budget, budget_channel=proposal.channel)
    form = FormProposalView(instance=proposal)
    divs = Division.objects.all()
    form_incremental = FormIncrementalSales()
    incremental = IncrementalSales.objects.filter(proposal_id=_id)
    total = IncrementalSales.objects.filter(proposal_id=_id).aggregate(
        swop_carton__sum=Sum('swop_carton'),
        swop_nom__sum=Sum('swop_nom'),
        swp_carton__sum=Sum('swp_carton'),
        swp_nom__sum=Sum('swp_nom'),
        incrp_carton__sum=Sum('incrp_carton'),
        incrp_nom__sum=Sum('incrp_nom'),
    )
    incpst_carton = (total['incrp_carton__sum'] / total['swop_carton__sum']
                     ) * 100 if total['swop_carton__sum'] else 0
    incpst_nom = (total['incrp_nom__sum'] / total['swop_nom__sum']
                  ) * 100 if total['swop_nom__sum'] else 0
    form_cost = FormProjectedCost()
    cost = ProjectedCost.objects.filter(proposal_id=_id)
    total_cost = ProjectedCost.objects.filter(
        proposal_id=_id).aggregate(Sum('cost'))
    add_cost = True if budget.budget_balance > 0 else False

    highest_approval = ProposalRelease.objects.filter(
        proposal_id=_id, limit__gt=proposal.total_cost).aggregate(Min('sequence')) if ProposalRelease.objects.filter(proposal_id=_id, limit__gt=proposal.total_cost).exists() else ProposalRelease.objects.filter(proposal_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = ProposalRelease.objects.filter(
            proposal_id=_id, sequence__lt=highest_sequence).order_by('sequence')
    else:
        approval = ProposalRelease.objects.filter(
            proposal_id=_id).order_by('sequence')

    context = {
        'data': proposal,
        'budget': budget,
        'form': form,
        'divs': divs,
        'formInc': form_incremental,
        'incremental': incremental,
        'formCost': form_cost,
        'cost': cost,
        'total': total,
        'incpst_carton': incpst_carton,
        'incpst_nom': incpst_nom,
        'total_inc': total['incrp_nom__sum'] if total['incrp_nom__sum'] else 0,
        'total_cost': total_cost['cost__sum'] if total_cost['cost__sum'] else 0,
        'tab': _tab,
        'sub_id': _sub_id,
        'action': _act,
        'approval': approval,
        'message': _msg,
        'status': proposal.status,
        'add_cost': add_cost,
        'segment': 'proposal',
        'group_segment': 'proposal',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROPOSAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/proposal_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_incremental_add(request, _tab, _id):
    form = FormIncrementalSales(request.POST, request.FILES)
    proposal = Proposal.objects.get(proposal_id=_id)
    message = '0'
    if form.is_valid():
        try:
            check = IncrementalSales.objects.get(
                proposal_id=_id, product=request.POST.get('product'))
            if check:
                message = 'Product already exist'
        except IncrementalSales.DoesNotExist:
            swop_carton = int(request.POST.get('swop_carton'))
            swp_carton = int(request.POST.get('swp_carton'))
            if swop_carton > swp_carton:
                message = 'Sales With Program must be greater than Sales Without Program'
            else:
                incremental = form.save(commit=False)
                incremental.proposal_id = _id
                incremental.save()
                if incremental.incrp_nom < 0:
                    message = 'Incremental Sales must be greater than 0'
                    incremental.delete()
                else:
                    total_inc = IncrementalSales.objects.filter(proposal_id=_id).aggregate(Sum('incrp_nom'))[
                        'incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
                    total_cost = ProjectedCost.objects.filter(proposal_id=_id).aggregate(Sum('cost'))[
                        'cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
                    proposal.roi = (
                        total_cost / total_inc) * 100 if total_inc != 0 else 0
                    proposal.save()

    return HttpResponseRedirect(reverse('proposal-view', args=[_tab, _id, '0', 'add-item', message]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_cost_add(request, _tab, _id):
    form = FormProjectedCost(request.POST, request.FILES)
    proposal = Proposal.objects.get(proposal_id=_id)
    budget_detail = BudgetDetail.objects.get(
        budget=proposal.budget, budget_channel=proposal.channel)
    message = '0'
    if form.is_valid():
        try:
            check = ProjectedCost.objects.get(
                proposal_id=_id, activities=request.POST.get('activities'))
            if check:
                message = 'Activity already exist'
        except ProjectedCost.DoesNotExist:
            cost = form.save(commit=False)
            if cost.cost > budget_detail.budget_balance:
                message = 'Total cost must be less than or equal to budget balance'
            else:
                cost.proposal_id = _id
                cost.save()
                total_inc = IncrementalSales.objects.filter(
                    proposal_id=_id).aggregate(Sum('incrp_nom'))['incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
                total_cost = ProjectedCost.objects.filter(
                    proposal_id=_id).aggregate(Sum('cost'))['cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
                proposal.roi = (total_cost / total_inc) * \
                    100 if total_inc != 0 else 0
                proposal.total_cost = total_cost
                proposal.balance = total_cost
                proposal.status = 'PENDING' if proposal.status == 'DRAFT' else proposal.status
                proposal.save()

                sum_cost = Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).exclude(status__in=['CLOSED', 'REJECTED']).aggregate(Sum('total_cost'))[
                    'total_cost__sum'] if Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).exclude(status__in=['CLOSED', 'REJECTED']).exists() else 0
                budget_detail.budget_proposed = sum_cost
                budget_detail.save()
                sum_balance = BudgetDetail.objects.filter(budget=proposal.budget).aggregate(Sum('budget_balance'))[
                    'budget_balance__sum'] if BudgetDetail.objects.filter(budget=proposal.budget).exists() else 0
                budget = Budget.objects.get(budget_id=proposal.budget)
                budget.budget_balance = sum_balance
                budget.save()

                mail_sent = ProposalRelease.objects.filter(
                    proposal_id=_id).order_by('sequence').values_list('mail_sent', flat=True)
                if mail_sent[0] == False:
                    email = ProposalRelease.objects.filter(
                        proposal_id=_id).order_by('sequence').values_list('proposal_approval_email', flat=True)
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT username FROM apps_proposalrelease INNER JOIN apps_user ON apps_proposalrelease.proposal_approval_id = apps_user.user_id WHERE proposal_id = '" + str(_id) + "' AND proposal_approval_status = 'N' ORDER BY sequence LIMIT 1")
                        approver = cursor.fetchone()

                    subject = 'Proposal Approval'
                    msg = 'Dear ' + approver[0] + ',\n\nYou have a new proposal to approve. Please check your proposal release list.\n\n' + \
                        'Click this link to approve, revise, return or reject this proposal.\n' + host.url + 'proposal_release/view/' + str(_id) + '/0/0/0/0/' + \
                        '\n\nThank you.'
                    send_email(subject, msg, [email[0]])

                    # update mail sent to true
                    release = ProposalRelease.objects.filter(
                        proposal_id=_id).order_by('sequence').first()
                    release.mail_sent = True
                    release.save()

    return HttpResponseRedirect(reverse('proposal-view', args=[_tab, _id, '0', 'add-cost', message]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_incremental_delete(request, _tab, _id, _product):
    proposal = Proposal.objects.get(proposal_id=_id)
    incremental = IncrementalSales.objects.get(
        proposal_id=_id, id=_product)
    incremental.delete()
    total_inc = IncrementalSales.objects.filter(
        proposal_id=_id).aggregate(Sum('incrp_nom'))['incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
    total_cost = ProjectedCost.objects.filter(
        proposal_id=_id).aggregate(Sum('cost'))['cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
    proposal.roi = (total_cost / total_inc) * \
        100 if total_inc != 0 else 0
    proposal.save()

    return HttpResponseRedirect(reverse('proposal-view', args=[_tab, _id, '0', '0', '0']))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_cost_delete(request, _tab, _id, _activities):
    proposal = Proposal.objects.get(proposal_id=_id)
    budget_detail = BudgetDetail.objects.get(
        budget=proposal.budget, budget_channel=proposal.channel)
    cost = ProjectedCost.objects.get(proposal_id=_id, id=_activities)
    cost.delete()
    total_inc = IncrementalSales.objects.filter(
        proposal_id=_id).aggregate(Sum('incrp_nom'))['incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
    total_cost = ProjectedCost.objects.filter(
        proposal_id=_id).aggregate(Sum('cost'))['cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
    proposal.roi = (total_cost / total_inc) * \
        100 if total_inc != 0 else 0
    proposal.total_cost = total_cost
    proposal.balance = total_cost
    proposal.save()
    sum_cost = Proposal.objects.filter(
        budget=proposal.budget, channel=proposal.channel).aggregate(Sum('total_cost'))['total_cost__sum'] if Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).exists() else 0
    budget_detail.budget_proposed = sum_cost
    budget_detail.save()
    sum_balance = BudgetDetail.objects.filter(budget=proposal.budget).aggregate(Sum('budget_balance'))[
        'budget_balance__sum'] if BudgetDetail.objects.filter(budget=proposal.budget).exists() else 0
    budget = Budget.objects.get(budget_id=proposal.budget)
    budget.budget_balance = sum_balance
    budget.save()

    return HttpResponseRedirect(reverse('proposal-view', args=[_tab, _id, '0', '0', '0']))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def remove_attachment(request, _tab, _id):
    proposal = Proposal.objects.get(proposal_id=_id)
    proposal.attachment = None
    proposal.save()
    return HttpResponseRedirect(reverse('proposal-view', args=[_tab, _id, '0', '0', '0']))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL-RELEASE')
def remove_release_attachment(request, _id):
    proposal = Proposal.objects.get(proposal_id=_id)
    proposal.attachment = None
    proposal.save()
    return render(request, 'home/proposal_release_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_incremental_update(request, _tab, _id, _product):
    proposal = Proposal.objects.get(proposal_id=_id)
    update = IncrementalSales.objects.get(proposal_id=_id, id=_product)
    message = '0'
    if request.POST:
        swop_carton = int(request.POST.get('swop_carton'))
        swp_carton = int(request.POST.get('swp_carton'))
        if swop_carton > swp_carton:
            message = 'Sales With Program must be greater than Sales Without Program'
        else:
            swop_carton = update.swop_carton
            swp_carton = update.swp_carton
            swop_nom = update.swop_nom
            swp_nom = update.swp_nom
            update.swop_carton = int(request.POST.get('swop_carton'))
            update.swp_carton = int(request.POST.get('swp_carton'))
            update.swop_nom = int(request.POST.get('swop_nom'))
            update.swp_nom = int(request.POST.get('swp_nom'))
            update.save()
            if update.incrp_nom < 0:
                message = 'Incremental Sales must be greater than 0'
                update.swop_carton = swop_carton
                update.swp_carton = swp_carton
                update.swop_nom = swop_nom
                update.swp_nom = swp_nom
                update.save()
            else:
                total_inc = IncrementalSales.objects.filter(
                    proposal_id=_id).aggregate(Sum('incrp_nom'))['incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
                total_cost = ProjectedCost.objects.filter(
                    proposal_id=_id).aggregate(Sum('cost'))['cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
                proposal.roi = (total_cost / total_inc) * \
                    100 if total_inc != 0 else 0
                proposal.save()

    return HttpResponseRedirect(reverse('proposal-view', args=[_tab, _id, _product, 'upd-item', message]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_cost_update(request, _tab, _id, _activities):
    proposal = Proposal.objects.get(proposal_id=_id)
    budget_detail = BudgetDetail.objects.get(
        budget=proposal.budget, budget_channel=proposal.channel)
    update = ProjectedCost.objects.get(
        proposal_id=_id, id=_activities)
    message = '0'
    if request.POST:
        cost = update.cost
        if int(request.POST.get('cost')) > budget_detail.budget_balance + cost:
            message = 'Total cost must be less than or equal to budget balance'
        else:
            update.activities = request.POST.get('activities')
            update.cost = int(request.POST.get('cost'))
            update.save()
            total_inc = IncrementalSales.objects.filter(
                proposal_id=_id).aggregate(Sum('incrp_nom'))['incrp_nom__sum'] if IncrementalSales.objects.filter(proposal_id=_id).exists() else 0
            total_cost = ProjectedCost.objects.filter(
                proposal_id=_id).aggregate(Sum('cost'))['cost__sum'] if ProjectedCost.objects.filter(proposal_id=_id).exists() else 0
            proposal.roi = (total_cost / total_inc) * \
                100 if total_inc != 0 else 0
            proposal.total_cost = total_cost
            proposal.balance = total_cost
            proposal.status = 'PENDING' if proposal.status == 'DRAFT' else proposal.status
            proposal.save()
            sum_cost = Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).aggregate(Sum('total_cost'))[
                'total_cost__sum'] if Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).exists() else 0
            budget_detail.budget_proposed = sum_cost
            budget_detail.save()
            sum_balance = BudgetDetail.objects.filter(budget=proposal.budget).aggregate(Sum('budget_balance'))[
                'budget_balance__sum'] if BudgetDetail.objects.filter(budget=proposal.budget).exists() else 0
            budget = Budget.objects.get(budget_id=proposal.budget)
            budget.budget_balance = sum_balance
            budget.save()

    return HttpResponseRedirect(reverse('proposal-view', args=[_tab, _id, _activities, 'upd-cost', message]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_update(request, _tab, _id):
    proposal = Proposal.objects.get(proposal_id=_id)
    divs = Division.objects.all()
    incremental = IncrementalSales.objects.filter(proposal_id=_id)
    cost = ProjectedCost.objects.filter(proposal_id=_id)
    total = IncrementalSales.objects.filter(proposal_id=_id).aggregate(
        swop_carton__sum=Sum('swop_carton'),
        swop_nom__sum=Sum('swop_nom'),
        swp_carton__sum=Sum('swp_carton'),
        swp_nom__sum=Sum('swp_nom'),
        incrp_carton__sum=Sum('incrp_carton'),
        incrp_nom__sum=Sum('incrp_nom'),
        incpst_carton__ratio=(Sum('incrp_carton') /
                              Sum('swop_carton')) * 100 if Sum('swop_carton') else 0,
        incpst_nom__ratio=(Sum('incrp_nom') /
                           Sum('swop_nom')) * 100 if Sum('swop_nom') else 0,
    )
    total_cost = ProjectedCost.objects.filter(
        proposal_id=_id).aggregate(Sum('cost'))
    message = '0'
    msg = ''

    if request.POST:
        form = FormProposalUpdate(
            request.POST, request.FILES, instance=proposal)
        if form.is_valid():
            parent = form.save(commit=False)
            parent.duration = form.cleaned_data['period_end'] - \
                form.cleaned_data['period_start']
            if parent.duration.days < 0:
                message = 'Period end must be greater than period start.'
            else:
                parent.save()
                if not settings.DEBUG:
                    my_file = proposal.attachment
                    filename = '../../www/aqiqahon/apps/media/' + my_file.name
                    with open(filename, 'wb+') as temp_file:
                        for chunk in my_file.chunks():
                            temp_file.write(chunk)
                return HttpResponseRedirect(reverse('proposal-view', args=[_tab, _id, '0', '0', '0']))
    else:
        form = FormProposalUpdate(instance=proposal)

    msg = form.errors

    context = {
        'form': form,
        'data': proposal,
        'divs': divs,
        'incremental': incremental,
        'cost': cost,
        'total': total,
        'total_inc': total['incrp_nom__sum'] if total['incrp_nom__sum'] else 0,
        'total_cost': total_cost['cost__sum'] if total_cost['cost__sum'] else 0,
        'tab': _tab,
        'message': message,
        'msg': msg,
        'segment': 'proposal',
        'group_segment': 'proposal',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROPOSAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/proposal_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROPOSAL')
def proposal_delete(request, _tab, _id):
    proposal = Proposal.objects.get(proposal_id=_id)
    budget_detail = BudgetDetail.objects.get(
        budget=proposal.budget, budget_channel=proposal.channel)
    proposal.delete()
    sum_cost = Proposal.objects.filter(
        budget=proposal.budget, channel=proposal.channel).aggregate(Sum('total_cost'))['total_cost__sum'] if Proposal.objects.filter(budget=proposal.budget, channel=proposal.channel).exists() else 0
    budget_detail.budget_proposed = sum_cost
    budget_detail.save()
    sum_balance = BudgetDetail.objects.filter(budget=proposal.budget).aggregate(Sum('budget_balance'))[
        'budget_balance__sum'] if BudgetDetail.objects.filter(budget=proposal.budget).exists() else 0
    budget = Budget.objects.get(budget_id=proposal.budget)
    budget.budget_balance = sum_balance
    budget.save()

    return HttpResponseRedirect(reverse('proposal-index', args=[_tab, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM')
def program_index(request, _tab):
    programs = Program.objects.all()
    drafts = Program.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-program_id').all
    draft_count = Program.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-program_id').count
    pendings = Program.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-program_id').all
    pending_count = Program.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-program_id').count
    inapprovals = Program.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-program_id').all
    inapproval_count = Program.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-program_id').count
    opens = Program.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-program_id').all
    open_count = Program.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-program_id').count

    context = {
        'data': programs,
        'drafts': drafts,
        'draft_count': draft_count,
        'pendings': pendings,
        'pending_count': pending_count,
        'inapprovals': inapprovals,
        'inapproval_count': inapproval_count,
        'opens': opens,
        'open_count': open_count,
        'tab': _tab,
        'segment': 'program',
        'group_segment': 'program',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='PROGRAM') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/program_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM')
def program_add(request, _area, _distributor, _proposal):
    selected_area = _area
    selected_distributor = _distributor
    selected_proposal = _proposal
    proposal = Proposal.objects.get(
        proposal_id=selected_proposal) if selected_proposal != '0' else None
    inc_sales = IncrementalSales.objects.filter(
        proposal_id=selected_proposal) if selected_proposal != '0' else None
    area = AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', 'area__area_name')
    distributors = Proposal.objects.filter(
        status='OPEN', area=selected_area, balance__gt=0).values_list('budget__budget_distributor__distributor_id', 'budget__budget_distributor__distributor_name').distinct() if selected_area != '0' else None
    proposals = Proposal.objects.filter(
        status='OPEN', area=selected_area, balance__gt=0, budget__budget_distributor=selected_distributor).order_by('-proposal_id') if selected_distributor != '0' else None

    message = ''
    no_save = False
    if selected_area != '0' and selected_proposal != '0':
        approvers = ProgramMatrix.objects.filter(
            area_id=_area, channel_id=proposal.channel).order_by('sequence')
        print_approvers = ProgramMatrix.objects.filter(
            area_id=_area, channel_id=proposal.channel, printed=1).order_by('sequence')
        if approvers.count() == 0 or approvers[0].limit > 0:
            message = "No program's approver found for this area and channel."
            no_save = True

    try:
        _no = Program.objects.all().order_by('seq_number').last()
    except Program.DoesNotExist:
        _no = None
    if _no is None:
        format_no = '{:04d}'.format(1)
    else:
        format_no = '{:04d}'.format(_no.seq_number + 1)

    _id = 'SBS-3' + format_no + '/' + proposal.channel + '/' + selected_area + '/' + \
        str(proposal.budget.budget_distributor.distributor_id) + '/' + \
        datetime.datetime.now().strftime('%m/%Y') if selected_proposal != '0' else 'SBS-3' + format_no + '/' + selected_area + '/0' + \
        datetime.datetime.now().strftime('%m/%Y')

    if request.POST:
        form = FormProgram(request.POST, request.FILES)
        if form.is_valid():
            draft = form.save(commit=False)
            draft.program_id = _id
            draft.program_date = datetime.datetime.now().date()
            draft.proposal_id = selected_proposal
            draft.seq_number = _no.seq_number + 1 if _no else 1
            draft.status = 'PENDING'
            draft.entry_pos = request.user.position.position_id
            draft.save()

            for approver in approvers:
                release = ProgramRelease(
                    program_id=draft.program_id,
                    program_approval_id=approver.approver_id,
                    program_approval_name=approver.approver.username,
                    program_approval_email=approver.approver.email,
                    program_approval_position=approver.approver.position.position_id,
                    sequence=approver.sequence,
                    limit=approver.limit,
                    return_to=approver.return_to,
                    approve=approver.approve,
                    revise=approver.revise,
                    returned=approver.returned,
                    reject=approver.reject,
                    notif=approver.notif,
                    printed=approver.printed,
                    as_approved=approver.as_approved)
                release.save()

            mail_sent = ProgramRelease.objects.filter(
                program_id=_id).order_by('sequence').values_list('mail_sent', flat=True)
            if mail_sent[0] == False:
                email = ProgramRelease.objects.filter(
                    program_id=_id).order_by('sequence').values_list('program_approval_email', flat=True)
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT username FROM apps_programrelease INNER JOIN apps_user ON apps_programrelease.program_approval_id = apps_user.user_id WHERE program_id = '" + str(_id) + "' AND program_approval_status = 'N' ORDER BY sequence LIMIT 1")
                    approver = cursor.fetchone()

                subject = 'Program Approval'
                msg = 'Dear ' + approver[0] + ',\n\nYou have a new program to approve. Please check your program release list.\n\n' + \
                    'Click this link to approve, revise, return or reject this program.\n' + host.url + 'program_release/view/' + str(_id) + '/0/' + \
                    '\n\nThank you.'
                send_email(subject, msg, [email[0]])

                # update mail sent to true
                release = ProgramRelease.objects.filter(
                    program_id=_id).order_by('sequence').first()
                release.mail_sent = True
                release.save()

            return HttpResponseRedirect(reverse('program-index', args=['pending', ]))
    else:
        prod = ''
        if selected_proposal != '0':
            plus4mo = datetime.date(
                proposal.period_end.year, proposal.period_end.month, 15) + datetime.timedelta(days=120)
            deadline = datetime.date(
                plus4mo.year, plus4mo.month, 1) - datetime.timedelta(days=1)

            for i in range(0, inc_sales.count()):
                prod += inc_sales[i].product
                if i != inc_sales.count() - 1:
                    prod += ', '

            len_prog = len(proposal.program_name)
            if len_prog > 85:
                _height = 30
            else:
                _height = 15

            form = FormProgram(initial={'program_id': _id, 'area': selected_area, 'deadline': deadline, 'content': '<b><table style="width: 100%; height: 15;"><tr><td style="padding-left: 3;"><b>No. ' + _id + '</b></td><td style="text-align: right; padding-right: 3;"><b>' + 'Jakarta, ' + datetime.datetime.now().strftime('%-d %B %Y') + '</b></td></tr></table><br>Kepada Yth.<br>' + proposal.budget.budget_distributor.distributor_name + '<br>Di Tempat,</b><br><br><br>' + '<b>Hal : <u>' + proposal.program_name + '</u></b><br><br>' + 'Dengan hormat,<br>' +
                                        'Sehubungan dengan informasi proposal ABC PI dengan no. sbb :<br><ul><li><b>' + proposal.proposal_id + ' (ANP Manual)</b></li></ul>Maka bersama surat ini kami sampaikan mengenai support program dengan rincian sebagai berikut :<br><table style="width: 100%; height: 15;"><tr><td style="padding-left: 3; width: 22%; height: ' + str(_height) + '; vertical-align: top;">Nama Program</td><td style="padding-left: 3; width: 2%; height: ' + str(_height) + '; vertical-align: top;">: </td><td style="padding-left: 3; width: 76%; height: ' + str(_height) + '; vertical-align: top;">' + proposal.program_name + '</td></tr><tr><td style="padding-left: 3; width: 22%; height: 15; vertical-align: top;">Produk</td><td style="padding-left: 3; width: 2%; height: 15; vertical-align: top;">: </td><td style="padding-left: 3; width: 76%; height: 15; vertical-align: top;">' + prod + '</td></tr><tr><td style="padding-left: 3; width: 22%; height: 15; vertical-align: top;">Periode</td><td style="padding-left: 3; width: 2%; height: 15; vertical-align: top;">: </td><td style="padding-left: 3; width: 76%; height: 15; vertical-align: top;">' + proposal.period_start.strftime("%d %b") + ' - ' + proposal.period_end.strftime("%d %b %Y") + '</td></tr><tr><td style="padding-left: 3; width: 22%; height: 15; vertical-align: top;">Wilayah/Channel</td><td style="padding-left: 3; width: 2%; height: 15; vertical-align: top;">: </td><td style="padding-left: 3; width: 76%; height: 15; vertical-align: top;">' + proposal.budget.budget_area.area_name + '/' + proposal.channel + '</td></tr><tr><td style="padding-left: 3; width: 22%; height: 15; vertical-align: top;">Detail Qty</td><td style="padding-left: 3; width: 2%; height: 15; vertical-align: top;">: </td><td style="padding-left: 3; width: 76%; height: 15; vertical-align: top;"></td></tr></table>' +
                                        # '<table style="width: 100%; height: 15; padding-left: 7; margin-top: 4;"><tr><td style="border: 0;"></td><td style="text-align: center; border: 1 solid; width: 40; background-color: red; color: white;">No.</td><td style="text-align: center; border: 1 solid; width: 100; background-color: red; color: white;">Pengambilan</td><td style="text-align: center; border: 1 solid; width: 160; background-color: red; color: white;">Add Diskon (on faktur)</td><td style="border: 0;"></td></tr><tr><td style="border: 0;"></td><td style="text-align: center; border: 1 solid; width: 40;">1.</td><td style="padding-left: 2; border: 1 solid; width: 100;">8 karton</td><td style="padding-left: 2; border: 1 solid; width: 160;">3%</td><td style="border: 0;"></td></tr></table>' +
                                        '<br>Mekanisme Program dan Klaim sebagai berikut :<br>' + proposal.mechanism.replace('\n', '<br>') + '<p><b><i>"Program di atas dapat diklaim ke PT. ABC PI paling lambat tanggal ' + deadline.strftime('%d %B %Y') + ', melewati dari batas tersebut PT. ABC PI berhak menolak dan tidak memproses klaim tersebut".</i></b></p><p>Demikian surat ini kami sampaikan. Atas perhatian dan kerjasamanya kami ucapkan terima kasih.</p>', 'approval':
                                        '<p><br /><br />Hormat Kami,</p>' +
                                        '<table style="width: 100%; height: 50"><tbody><tr><td style="padding-left: 3; height: 50"><img style="flex: 0 0 auto;" src="' + str(host.url) + 'apps/media/' + str(print_approvers[0].approver.signature) + '" alt="Signature" width="120" height="70" /></td><td style="padding-left: 0; height: 50"><img style="flex: 0 0 auto;" src="' + str(host.url) + 'apps/media/' + str(print_approvers[1].approver.signature) + '" alt="Signature" width="120" height="70" /></td><td style="padding-left: 0; height: 50"><img style="flex: 0 0 auto;" src="' + str(host.url) + 'apps/media/' + str(print_approvers[2].approver.signature) + '" alt="Signature" width="120" height="70" /></td><td style="padding-left: 0; height: 50"><img style="flex: 0 0 auto;" src="' + str(host.url) + 'apps/media/' + str(print_approvers[3].approver.signature) + '" alt="Signature" width="120" height="70" /></td></tr>' +
                                        '<tr><td style="padding-left: 3; height: 15"><span style="text-decoration: underline;">' + print_approvers[0].approver.username + '</span></td><td style="padding-left: 0; height: 15"><span style="text-decoration: underline;">' + print_approvers[1].approver.username + '</span></td><td style="padding-left: 0; height: 15"><span style="text-decoration: underline;">' + print_approvers[2].approver.username + '</span></td><td style="padding-left: 0; height: 15"><span style="text-decoration: underline;">' + print_approvers[3].approver.username + '</span></td></tr>' +
                                        '<tr><td style="padding-left: 3; height: 15">' + print_approvers[0].approver.position.position_name + '</td><td style="padding-left: 0; height: 15">' + print_approvers[1].approver.position.position_name + '</td><td style="padding-left: 0; height: 15">' + print_approvers[2].approver.position.position_name + '</td><td style="padding-left: 0; height: 15">' + print_approvers[3].approver.position.position_name + '</td></tr></tbody></table>'})
        else:
            form = FormProgram()

    msg = form.errors
    context = {
        'form': form,
        'area': area,
        'distributors': distributors,
        'proposals': proposals,
        'selected_area': selected_area,
        'selected_distributor': selected_distributor,
        'selected_proposal': selected_proposal,
        'msg': msg,
        'message': message,
        'no_save': no_save,
        'segment': 'program',
        'group_segment': 'program',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='PROGRAM') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/program_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM')
def program_view(request, _tab, _id):
    program = Program.objects.get(program_id=_id)
    form = FormProgramView(instance=program)

    highest_approval = ProgramRelease.objects.filter(
        program_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = ProgramRelease.objects.filter(
            program_id=_id, sequence__lt=highest_sequence).order_by('sequence')
    else:
        approval = ProgramRelease.objects.filter(
            program_id=_id).order_by('sequence')

    context = {
        'data': program,
        'form': form,
        'tab': _tab,
        'approval': approval,
        'status': program.status,
        'segment': 'program',
        'group_segment': 'program',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROGRAM') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/program_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM')
def program_update(request, _tab, _id):
    program = Program.objects.get(program_id=_id)
    message = '0'

    if request.POST:
        form = FormProgramUpdate(
            request.POST, request.FILES, instance=program)
        if form.is_valid():
            draft = form.save(commit=False)
            draft.status = 'PENDING'
            draft.save()

            mail_sent = ProgramRelease.objects.filter(
                program_id=_id).order_by('sequence').values_list('mail_sent', flat=True)
            if mail_sent[0] == False:
                email = ProgramRelease.objects.filter(
                    program_id=_id).order_by('sequence').values_list('program_approval_email', flat=True)
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT username FROM apps_programrelease INNER JOIN apps_user ON apps_programrelease.program_approval_id = apps_user.user_id WHERE program_id = '" + str(_id) + "' AND program_approval_status = 'N' ORDER BY sequence LIMIT 1")
                    approver = cursor.fetchone()

                subject = 'Program Approval'
                msg = 'Dear ' + approver[0] + ',\n\nYou have a new program to approve. Please check your program release list.\n\n' + \
                    'Click this link to approve, revise, return or reject this program.\n' + host.url + 'program_release/view/' + str(_id) + '/0/' + \
                    '\n\nThank you.'
                send_email(subject, msg, [email[0]])

                # update mail sent to true
                release = ProgramRelease.objects.filter(
                    program_id=_id).order_by('sequence').first()
                release.mail_sent = True
                release.save()

            return HttpResponseRedirect(reverse('program-view', args=[_tab, _id]))
    else:
        form = FormProgramUpdate(instance=program)

    context = {
        'form': form,
        'data': program,
        'tab': _tab,
        'message': message,
        'segment': 'program',
        'group_segment': 'program',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROGRAM') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/program_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM')
def program_delete(request, _tab, _id):
    program = Program.objects.get(program_id=_id)
    program.delete()

    return HttpResponseRedirect(reverse('program-index', args=[_tab, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM-RELEASE')
def program_release_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_program.program_id, apps_program.program_date, apps_distributor.distributor_name, apps_proposal.channel, apps_program.status, apps_programrelease.sequence FROM apps_distributor INNER JOIN apps_budget ON apps_distributor.distributor_id = apps_budget.budget_distributor_id INNER JOIN apps_proposal ON apps_budget.budget_id = apps_proposal.budget_id INNER JOIN apps_program ON apps_proposal.proposal_id = apps_program.proposal_id INNER JOIN apps_programrelease ON apps_program.program_id = apps_programrelease.program_id INNER JOIN (SELECT program_id, MIN(sequence) AS seq FROM apps_programrelease WHERE program_approval_status = 'N' GROUP BY program_id ORDER BY sequence ASC) AS q_group ON apps_programrelease.program_id = q_group.program_id AND apps_programrelease.sequence = q_group.seq WHERE (apps_program.status = 'PENDING' OR apps_program.status = 'IN APPROVAL') AND apps_programrelease.program_approval_id = '" + str(request.user.user_id) + "'")
        release = cursor.fetchall()

    context = {
        'data': release,
        'segment': 'program_release',
        'group_segment': 'program',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROGRAM-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/program_release_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM-RELEASE')
def program_release_view(request, _id, _is_revise):
    program = Program.objects.get(program_id=_id)
    form = FormProgramView(instance=program)
    approved = ProgramRelease.objects.get(
        program_id=_id, program_approval_id=request.user.user_id).program_approval_status

    context = {
        'form': form,
        'data': program,
        'approved': approved,
        'is_revise': _is_revise,
        'status': program.status,
        'segment': 'program_release',
        'group_segment': 'program',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PROGRAM-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
        'btn_release': ProgramRelease.objects.get(program_id=_id, program_approval_id=request.user.user_id),
    }
    return render(request, 'home/program_release_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM-RELEASE')
def program_release_update(request, _id):
    program = Program.objects.get(program_id=_id)
    message = '0'
    _deadline = program.deadline
    _content = program.content

    if request.POST:
        form = FormProgramUpdate(
            request.POST, request.FILES, instance=program)
        if form.is_valid():
            parent = form.save(commit=False)
            deadline = _deadline if form.cleaned_data['deadline'] != _deadline else None
            content = _content if form.cleaned_data['content'] != _content else None
            parent.save()

            recipients = []

            release = ProgramRelease.objects.get(
                program_id=_id, program_approval_id=request.user.user_id)
            release.revise_note = request.POST.get('revise_note')
            release.save()

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT program_id, email FROM apps_program INNER JOIN apps_user ON apps_program.entry_by = apps_user.user_id WHERE program_id = '" + str(_id) + "'")
                entry_mail = cursor.fetchone()
                if entry_mail:
                    recipients.append(entry_mail[1])

                cursor.execute(
                    "SELECT program_id, email FROM apps_program INNER JOIN apps_user ON apps_program.update_by = apps_user.user_id WHERE program_id = '" + str(_id) + "'")
                update_mail = cursor.fetchone()
                if update_mail:
                    recipients.append(update_mail[1])

                cursor.execute(
                    "SELECT program_id, program_approval_email FROM apps_programrelease WHERE program_id = '" + str(_id) + "' AND program_approval_status = 'Y'")
                approver_mail = cursor.fetchall()
                for mail in approver_mail:
                    recipients.append(mail[1])

            subject = 'Program Revised'
            msg = 'Dear All,\n\nThe following is revised program for Program No. ' + \
                str(_id) + ':\n'
            if deadline:
                msg += '\nBEFORE\n'
                msg += 'Claim Deadline: ' + \
                    deadline.strftime('%d %b %Y') + '\n'
                msg += '\nAFTER\n'
                msg += 'Claim Deadline: ' + \
                    form.cleaned_data['deadline'].strftime('%d %b %Y') + '\n'

            if content:
                msg += '\nCONTENT: Content has been revised. View the program for more details.\n'

            msg += '\nNote: ' + \
                str(release.revise_note) + '\n\nClick the following link to view the program.\n' + host.url + 'program/view/inapproval/' + str(_id) + '/' + \
                '\n\nThank you.'

            recipient_list = list(dict.fromkeys(recipients))
            send_email(subject, msg, recipient_list)

            return HttpResponseRedirect(reverse('program-release-view', args=[_id, 0]))
    else:
        form = FormProgramUpdate(instance=program)

    # msg = form.errors
    context = {
        'form': form,
        'data': program,
        'message': message,
        'segment': 'program',
        'group_segment': 'program',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROGRAM-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/program_release_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM-RELEASE')
def program_release_approve(request, _id):
    program = Program.objects.get(program_id=_id)
    release = ProgramRelease.objects.get(
        program_id=_id, program_approval_id=request.user.user_id)
    release.program_approval_status = 'Y'
    release.program_approval_date = timezone.now()
    release.save()
    highest_approval = ProgramRelease.objects.filter(
        program_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = ProgramRelease.objects.filter(
            program_id=_id, sequence__lt=highest_sequence).order_by('sequence').last()
    else:
        approval = ProgramRelease.objects.filter(
            program_id=_id).order_by('sequence').last()

    if release.sequence == approval.sequence:
        program.status = 'OPEN'

        recipients = []

        maker = program.entry_by
        maker_mail = User.objects.get(user_id=maker).email
        recipients.append(maker_mail)

        approvers = ProgramRelease.objects.filter(
            program_id=_id, notif=True, program_approval_status='Y')
        for i in approvers:
            recipients.append(i.program_approval_email)

        subject = 'Program Approved'
        msg = 'Dear All,\n\nProgram No. ' + str(_id) + ' has been approved.\n\nClick the following link to view the program.\n' + host.url + 'program/view/open/' + str(_id) + \
            '\n\nThank you.'
        recipient_list = list(dict.fromkeys(recipients))
        send_email(subject, msg, recipient_list)
    else:
        program.status = 'IN APPROVAL'

        email = ProgramRelease.objects.filter(program_id=_id, program_approval_status='N').order_by(
            'sequence').values_list('program_approval_email', flat=True)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT program_approval_name FROM apps_programrelease WHERE program_id = '" + str(_id) + "' AND program_approval_status = 'N' ORDER BY sequence LIMIT 1")
            approver = cursor.fetchone()

        subject = 'Program Approval'
        msg = 'Dear ' + approver[0] + ',\n\nYou have a new program to approve. Please check your program release list.\n\n' + \
            'Click this link to approve, revise, return or reject this program.\n' + host.url + 'program_release/view/' + str(_id) + '/0/' + \
            '\n\nThank you.'
        send_email(subject, msg, [email[0]])

    program.save()

    return HttpResponseRedirect(reverse('program-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM-RELEASE')
def program_release_return(request, _id):
    recipients = []
    draft = False

    try:
        return_to = ProgramRelease.objects.get(
            program_id=_id, return_to=True, sequence__lt=ProgramRelease.objects.get(program_id=_id, program_approval_id=request.user.user_id).sequence)

        if return_to:
            approvers = ProgramRelease.objects.filter(
                program_id=_id, sequence__gte=ProgramRelease.objects.get(program_id=_id, return_to=True).sequence, sequence__lt=ProgramRelease.objects.get(program_id=_id, program_approval_id=request.user.user_id).sequence)
    except ProgramRelease.DoesNotExist:
        approvers = ProgramRelease.objects.filter(
            program_id=_id, sequence__lte=ProgramRelease.objects.get(program_id=_id, program_approval_id=request.user.user_id).sequence)
        draft = True

    for i in approvers:
        recipients.append(i.program_approval_email)
        i.program_approval_status = 'N'
        i.program_approval_date = None
        i.revise_note = ''
        i.return_note = ''
        i.reject_note = ''
        i.mail_sent = False
        i.save()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT program_id, email FROM apps_program INNER JOIN apps_user ON apps_program.entry_by = apps_user.user_id WHERE program_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT program_id, email FROM apps_program INNER JOIN apps_user ON apps_program.update_by = apps_user.user_id WHERE program_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

    note = ProgramRelease.objects.get(
        program_id=_id, program_approval_id=request.user.user_id)
    note.return_note = request.POST.get('return_note')
    note.save()

    subject = 'Program Returned'
    msg = 'Dear All,\n\nProgram No. ' + str(_id) + ' has been returned.\n\nNote: ' + \
        str(note.return_note) + \
        '\n\nClick the following link to revise the program.\n'

    if draft:
        program = Program.objects.get(program_id=_id)
        program.status = 'DRAFT'
        program.save()
        msg += host.url + 'program/view/pending/' + str(_id) + \
            '\n\nThank you.'
    else:
        msg += host.url + 'program_release/view/' + \
            str(_id) + '/0/\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('program-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM-RELEASE')
def program_release_reject(request, _id):
    recipients = []

    try:
        approvers = ProgramRelease.objects.filter(
            program_id=_id, sequence__lt=ProgramRelease.objects.get(program_id=_id, program_approval_id=request.user.user_id).sequence)
    except ProgramRelease.DoesNotExist:
        pass

    for i in approvers:
        recipients.append(i.program_approval_email)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT program_id, email FROM apps_program INNER JOIN apps_user ON apps_program.entry_by = apps_user.user_id WHERE program_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT program_id, email FROM apps_program INNER JOIN apps_user ON apps_program.update_by = apps_user.user_id WHERE program_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

    note = ProgramRelease.objects.get(
        program_id=_id, program_approval_id=request.user.user_id)
    note.reject_note = request.POST.get('reject_note')
    note.save()

    subject = 'Program Rejected'
    msg = 'Dear All,\n\nProgram No. ' + str(_id) + ' has been rejected.\n\nNote: ' + \
        str(note.reject_note) + \
        '\n\nClick the following link to see the program.\n'

    program = Program.objects.get(program_id=_id)
    program.status = 'REJECTED'
    program.save()
    msg += host.url + 'program/view/reject/' + str(_id) + \
        '\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('program-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM-ARCHIVE')
def program_archive_index(request):
    rejects = Program.objects.filter(status='REJECTED', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-program_id').all
    reject_count = Program.objects.filter(status='REJECTED', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-program_id').count

    context = {
        'rejects': rejects,
        'reject_count': reject_count,
        'segment': 'program_archive',
        'group_segment': 'program',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='PROGRAM-ARCHIVE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/program_archive.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM')
def program_print(request, _id):
    program = Program.objects.get(program_id=_id)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT signature, program_approval_name, position_name FROM apps_user INNER JOIN apps_programrelease ON user_id = program_approval_id INNER JOIN apps_position ON program_approval_position = apps_position.position_id WHERE program_id = '" + str(_id) + "' AND program_approval_status = 'Y' AND printed = True ORDER BY sequence")
        approvers = cursor.fetchall()

    for approver in approvers:
        name_length = len(approver[1])

    html_file = 'home/program_print.html'
    context = {'data': program, 'approvers': approvers,
               'host': host.url, 'space': '0' * 20}
    template = get_template(html_file)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="' + _id + '.pdf"'

    # Draw the HTML content on the PDF canvas
    pisa.CreatePDF(html, dest=response)

    return response
    # return render(request, html_file, context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM-APPROVAL')
def program_matrix_index(request):
    areas = AreaSales.objects.all()

    context = {
        'data': areas,
        'segment': 'program_matrix',
        'group_segment': 'approval',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PROGRAM-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/program_matrix_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM-APPROVAL')
def program_matrix_view(request, _id, _channel):
    area = AreaSales.objects.get(area_id=_id)
    channels = AreaChannelDetail.objects.filter(area_id=_id, status=1)
    approvers = ProgramMatrix.objects.filter(area_id=_id, channel_id=_channel)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, position_name, q_programmatrix.approver_id FROM apps_user INNER JOIN apps_position ON apps_user.position_id = apps_position.position_id LEFT JOIN (SELECT * FROM apps_programmatrix WHERE area_id = '" + str(_id) + "' AND channel_id = '" + str(_channel) + "') AS q_programmatrix ON apps_user.user_id = q_programmatrix.approver_id WHERE q_programmatrix.approver_id IS NULL")
        users = cursor.fetchall()

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in users:
            if str(i[0]) in check:
                try:
                    approver = ProgramMatrix(
                        area_id=_id, channel_id=_channel, approver_id=i[0])
                    approver.save()
                except IntegrityError:
                    continue
            else:
                ProgramMatrix.objects.filter(
                    area_id=_id, channel_id=_channel, approver_id=i[0]).delete()

        return HttpResponseRedirect(reverse('program-matrix-view', args=[_id, _channel]))

    context = {
        'data': area,
        'channels': channels,
        'users': users,
        'approvers': approvers,
        'channel': _channel,
        'segment': 'program_matrix',
        'group_segment': 'approval',
        'tab': 'auth',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PROGRAM-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/program_matrix_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM-APPROVAL')
def program_matrix_update(request, _id, _channel, _approver):
    approvers = ProgramMatrix.objects.get(
        area=_id, channel_id=_channel, approver_id=_approver)

    if request.POST:
        approvers.sequence = int(request.POST.get('sequence'))
        approvers.limit = int(request.POST.get('limit'))
        approvers.return_to = True if request.POST.get('return') else False
        approvers.approve = True if request.POST.get('approve') else False
        approvers.revise = True if request.POST.get('revise') else False
        approvers.returned = True if request.POST.get('returned') else False
        approvers.reject = True if request.POST.get('reject') else False
        approvers.notif = True if request.POST.get('notif') else False
        approvers.printed = True if request.POST.get('printed') else False
        approvers.as_approved = request.POST.get('as_approved')
        approvers.save()

        return HttpResponseRedirect(reverse('program-matrix-view', args=[_id, _channel]))

    return render(request, 'home/program_matrix_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='PROGRAM-APPROVAL')
def program_matrix_delete(request, _id, _channel, _arg):
    approvers = ProgramMatrix.objects.get(
        area=_id, channel_id=_channel, approver_id=_arg)
    approvers.delete()

    return HttpResponseRedirect(reverse('program-matrix-view', args=[_id, _channel]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_index(request, _tab):
    claims = Claim.objects.all().order_by('-claim_id')
    drafts = Claim.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').all
    draft_count = Claim.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').count
    pendings = Claim.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').all
    pending_count = Claim.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').count
    inapprovals = Claim.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').all
    inapproval_count = Claim.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').count
    opens = Claim.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').all
    open_count = Claim.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').count

    context = {
        'data': claims,
        'drafts': drafts,
        'draft_count': draft_count,
        'pendings': pendings,
        'pending_count': pending_count,
        'inapprovals': inapprovals,
        'inapproval_count': inapproval_count,
        'opens': opens,
        'open_count': open_count,
        'tab': _tab,
        'segment': 'claim',
        'group_segment': 'claim',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CLAIM') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_add(request, _area, _distributor, _program):
    selected_area = _area
    selected_distributor = _distributor
    selected_program = _program
    program = Program.objects.get(
        program_id=selected_program) if selected_program != '0' else None
    area = AreaUser.objects.filter(user_id=request.user.user_id).values_list(
        'area_id', 'area__area_name')
    distributors = Program.objects.filter(status='OPEN', area=selected_area).values_list(
        'proposal__budget__budget_distributor__distributor_id', 'proposal__budget__budget_distributor__distributor_name').distinct() if selected_area != '0' else None
    programs = Program.objects.filter(status='OPEN', deadline__gte=datetime.datetime.now().date(
    ), area=selected_area, proposal__budget__budget_distributor__distributor_id=selected_distributor, proposal__balance__gt=0).distinct() if selected_distributor != '0' else None
    proposal = Proposal.objects.get(
        proposal_id=program.proposal.proposal_id) if selected_program != '0' else None
    proposals = Proposal.objects.filter(
        status='OPEN', area=selected_area, balance__gt=0, budget__budget_distributor=selected_distributor).order_by('-proposal_id') if selected_distributor != '0' else None

    no_save = False
    add_prop = '0'
    message = ''
    difference = 0
    add_proposals = None

    if selected_area != '0' and selected_program != '0':
        approvers = ClaimMatrix.objects.filter(
            area_id=selected_area, channel=program.proposal.channel).order_by('sequence')
        if approvers.count() == 0 or approvers[0].limit > 0:
            no_save = True
            message = "No claim's approver found for this area and channel."

    try:
        _no = Claim.objects.all().order_by('seq_number').last()
    except Claim.DoesNotExist:
        _no = None
    if _no is None:
        format_no = '{:04d}'.format(1)
    else:
        format_no = '{:04d}'.format(_no.seq_number + 1)

    _id = 'CBS-4' + format_no + '/' + program.proposal.channel + '/' + selected_area + '/' + \
        program.proposal.budget.budget_distributor.distributor_id + '/' + \
        datetime.datetime.now().strftime('%m/%Y') if selected_program != '0' else 'CBS-4' + format_no + '/' + selected_area + '/0' + \
        '/' + datetime.datetime.now().strftime('%m/%Y')

    if request.POST:
        form = FormClaim(request.POST, request.FILES)
        difference = int(request.POST.get('amount')) - int(proposal.balance)
        if int(request.POST.get('amount')) > int(proposal.balance) and request.POST.get('additional_proposal') == '':
            add_prop = '1'
            message = 'Claim amount is greater than proposal balance.'
            add_proposals = Proposal.objects.filter(status='OPEN', area=selected_area, channel=proposal.channel, balance__gte=difference, budget__budget_distributor=selected_distributor).exclude(
                proposal_id=proposal.proposal_id).order_by('-proposal_id') if selected_program != '0' else None
        else:
            if form.is_valid():
                draft = form.save(commit=False)
                draft.program_id = selected_program
                draft.seq_number = _no.seq_number + 1 if _no else 1
                draft.entry_pos = request.user.position.position_id
                draft.total_claim = Decimal(request.POST.get('amount'))
                draft.amount = proposal.balance if request.POST.get(
                    'additional_proposal') else Decimal(request.POST.get('amount'))
                draft.additional_proposal_id = request.POST.get(
                    'additional_proposal')
                draft.additional_amount = difference if request.POST.get(
                    'additional_proposal') else 0
                draft.save()

                sum_amount = Claim.objects.filter(
                    proposal_id=draft.proposal_id).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount = Claim.objects.filter(additional_proposal=draft.proposal_id).exclude(
                    status__in=['REJECTED', 'DRAFT']).aggregate(Sum('additional_amount'))

                sum_amount2 = Claim.objects.filter(
                    proposal_id=draft.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount2 = Claim.objects.filter(additional_proposal=draft.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(
                    Sum('additional_amount'))

                amount = sum_amount.get('amount__sum') if sum_amount.get(
                    'amount__sum') else 0
                additional_amount = sum_add_amount.get(
                    'additional_amount__sum') if sum_add_amount.get('additional_amount__sum') else 0

                amount2 = sum_amount2.get('amount__sum') if sum_amount2.get(
                    'amount__sum') else 0
                additional_amount2 = sum_add_amount2.get('additional_amount__sum') if sum_add_amount2.get(
                    'additional_amount__sum') else 0

                proposal.proposal_claim = amount + additional_amount
                proposal.balance = proposal.total_cost - proposal.proposal_claim
                proposal.save()

                proposal2 = Proposal.objects.get(
                    proposal_id=draft.additional_proposal_id) if draft.additional_proposal else None
                if proposal2:
                    proposal2.proposal_claim = amount2 + additional_amount2
                    proposal2.balance = proposal2.total_cost - proposal2.proposal_claim
                    proposal2.save()

                for approver in approvers:
                    release = ClaimRelease(
                        claim_id=draft.claim_id,
                        claim_approval_id=approver.approver_id,
                        claim_approval_name=approver.approver.username,
                        claim_approval_email=approver.approver.email,
                        claim_approval_position=approver.approver.position.position_id,
                        sequence=approver.sequence,
                        limit=approver.limit,
                        return_to=approver.return_to,
                        approve=approver.approve,
                        revise=approver.revise,
                        returned=approver.returned,
                        reject=approver.reject,
                        notif=approver.notif,
                        printed=approver.printed,
                        as_approved=approver.as_approved)
                    release.save()

                mail_sent = ClaimRelease.objects.filter(
                    claim_id=_id).order_by('sequence').values_list('mail_sent', flat=True)
                if mail_sent[0] == False:
                    email = ClaimRelease.objects.filter(
                        claim_id=_id).order_by('sequence').values_list('claim_approval_email', flat=True)
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT username FROM apps_claimrelease INNER JOIN apps_user ON apps_claimrelease.claim_approval_id = apps_user.user_id WHERE claim_id = '" + str(_id) + "' AND claim_approval_status = 'N' ORDER BY sequence LIMIT 1")
                        approver = cursor.fetchone()

                    subject = 'Claim Approval'
                    msg = 'Dear ' + approver[0] + ',\n\nYou have a new claim to approve. Please check your claim release list.\n\n' + \
                        'Click this link to approve, revise, return or reject this claim.\n' + host.url + 'claim_release/view/' + str(_id) + '/0/' + \
                        '\n\nThank you.'
                    send_email(subject, msg, [email[0]])

                    # update mail sent to true
                    release = ClaimRelease.objects.filter(
                        claim_id=_id).order_by('sequence').first()
                    release.mail_sent = True
                    release.save()

                return HttpResponseRedirect(reverse('claim-index', args=['pending', ]))
    else:
        form = FormClaim(initial={'area': selected_area, 'claim_id': _id})

    msg = form.errors
    context = {
        'form': form,
        'area': area,
        'distributors': distributors,
        'program': program,
        'programs': programs,
        'proposals': proposals,
        'add_proposals': add_proposals,
        'selected_area': selected_area,
        'selected_distributor': selected_distributor,
        'selected_program': selected_program,
        'msg': msg,
        'message': message,
        'no_save': no_save,
        'add_prop': add_prop,
        'difference': difference,
        'segment': 'claim',
        'group_segment': 'claim',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CLAIM') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_view(request, _tab, _id):
    claim = Claim.objects.get(claim_id=_id)
    form = FormClaimView(instance=claim)
    program = Program.objects.get(program_id=claim.program_id)

    highest_approval = ClaimRelease.objects.filter(
        claim_id=_id, limit__gt=claim.total_claim).aggregate(Min('sequence')) if ClaimRelease.objects.filter(claim_id=_id, limit__gt=claim.total_claim).count() > 0 else ClaimRelease.objects.filter(claim_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = ClaimRelease.objects.filter(
            claim_id=_id, sequence__lt=highest_sequence).order_by('sequence')
    else:
        approval = ClaimRelease.objects.filter(
            claim_id=_id).order_by('sequence')

    context = {
        'data': claim,
        'form': form,
        'tab': _tab,
        'program': program,
        'approval': approval,
        'status': claim.status,
        'segment': 'claim',
        'group_segment': 'claim',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CLAIM') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/claim_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_update(request, _tab, _id):
    claim = Claim.objects.get(claim_id=_id)
    proposals = Proposal.objects.filter(
        status='OPEN', area=claim.area, balance__gt=0, budget__budget_distributor=claim.proposal.budget.budget_distributor).order_by('-proposal_id')
    program = Program.objects.get(program_id=claim.program_id)
    proposal = Proposal.objects.get(proposal_id=program.proposal.proposal_id)

    message = '0'
    add_prop = '0'
    difference = 0
    add_proposals = None
    add_prop_before = claim.additional_proposal
    amount_before = claim.amount

    if request.POST:
        form = FormClaimUpdate(request.POST, request.FILES, instance=claim)
        difference = int(request.POST.get('amount')) - \
            (int(proposal.balance) + int(claim.amount))
        if int(request.POST.get('amount')) > (int(program.proposal.balance) + int(claim.amount)) and request.POST.get('additional_proposal') == '':
            add_prop = '1'
            message = 'Claim amount is greater than proposal balance.'
            add_proposals = Proposal.objects.filter(status='OPEN', area=claim.area.area_id, channel=proposal.channel, balance__gte=difference, budget__budget_distributor=claim.proposal.budget.budget_distributor).exclude(
                proposal_id=proposal.proposal_id)
        else:
            if form.is_valid():
                draft = form.save(commit=False)
                draft.status = 'PENDING'
                draft.total_claim = Decimal(request.POST.get('amount'))
                draft.amount = proposal.balance + amount_before if request.POST.get(
                    'additional_proposal') else Decimal(request.POST.get('amount'))
                if int(request.POST.get('amount')) > (int(proposal.balance) + int(amount_before)):
                    draft.additional_proposal = request.POST.get(
                        'additional_proposal')
                else:
                    draft.additional_proposal = None
                draft.additional_amount = difference if request.POST.get(
                    'additional_proposal') else 0
                draft.save()

                sum_amount = Claim.objects.filter(
                    proposal_id=draft.proposal_id).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount = Claim.objects.filter(additional_proposal=draft.proposal_id).exclude(
                    status__in=['REJECTED', 'DRAFT']).aggregate(Sum('additional_amount'))

                sum_amount2 = Claim.objects.filter(
                    proposal_id=draft.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount2 = Claim.objects.filter(additional_proposal=draft.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(
                    Sum('additional_amount'))

                amount = sum_amount.get('amount__sum') if sum_amount.get(
                    'amount__sum') else 0
                additional_amount = sum_add_amount.get(
                    'additional_amount__sum') if sum_add_amount.get('additional_amount__sum') else 0

                amount2 = sum_amount2.get('amount__sum') if sum_amount2.get(
                    'amount__sum') else 0
                additional_amount2 = sum_add_amount2.get('additional_amount__sum') if sum_add_amount2.get(
                    'additional_amount__sum') else 0

                proposal.proposal_claim = amount + additional_amount
                proposal.balance = proposal.total_cost - proposal.proposal_claim
                proposal.save()

                proposal2 = Proposal.objects.get(
                    proposal_id=draft.additional_proposal) if draft.additional_proposal else None
                if proposal2:
                    proposal2.proposal_claim = amount2 + additional_amount2
                    proposal2.balance = proposal2.total_cost - proposal2.proposal_claim
                    proposal2.save()
                else:
                    proposal3 = Proposal.objects.get(
                        proposal_id=add_prop_before) if add_prop_before else None
                    if proposal3:
                        proposal3.proposal_claim = amount2 + additional_amount2
                        proposal3.balance = proposal3.total_cost - proposal3.proposal_claim
                        proposal3.save()

                mail_sent = ClaimRelease.objects.filter(
                    claim_id=_id).order_by('sequence').values_list('mail_sent', flat=True)
                if mail_sent[0] == False:
                    email = ClaimRelease.objects.filter(
                        claim_id=_id).order_by('sequence').values_list('claim_approval_email', flat=True)
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT username FROM apps_claimrelease INNER JOIN apps_user ON apps_claimrelease.claim_approval_id = apps_user.user_id WHERE claim_id = '" + str(_id) + "' AND claim_approval_status = 'N' ORDER BY sequence LIMIT 1")
                        approver = cursor.fetchone()

                    subject = 'Claim Approval'
                    msg = 'Dear ' + approver[0] + ',\n\nYou have a new claim to approve. Please check your claim release list.\n\n' + \
                        'Click this link to approve, revise, return or reject this claim.\n' + host.url + 'claim_release/view/' + str(_id) + '/0/' + \
                        '\n\nThank you.'
                    send_email(subject, msg, [email[0]])

                    # update mail sent to true
                    release = ClaimRelease.objects.filter(
                        claim_id=_id).order_by('sequence').first()
                    release.mail_sent = True
                    release.save()

                return HttpResponseRedirect(reverse('claim-view', args=[_tab, _id]))
    else:
        form = FormClaimUpdate(instance=claim)

    err = form.errors
    context = {
        'form': form,
        'data': claim,
        'program': program,
        'proposals': proposals,
        'add_proposals': add_proposals,
        'add_prop': add_prop,
        'difference': difference,
        'tab': _tab,
        'message': message,
        'err': err,
        'segment': 'claim',
        'group_segment': 'claim',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLAIM') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_delete(request, _tab, _id):
    claim = Claim.objects.get(claim_id=_id)
    proposal = Proposal.objects.get(proposal_id=claim.proposal.proposal_id)
    claim.delete()

    sum_amount = Claim.objects.filter(
        proposal_id=claim.proposal_id).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
    sum_add_amount = Claim.objects.filter(additional_proposal=claim.proposal_id).exclude(
        status__in=['REJECTED', 'DRAFT']).aggregate(Sum('additional_amount'))

    sum_amount2 = Claim.objects.filter(
        proposal_id=claim.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
    sum_add_amount2 = Claim.objects.filter(additional_proposal=claim.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(
        Sum('additional_amount'))

    amount = sum_amount.get('amount__sum') if sum_amount.get(
        'amount__sum') else 0
    additional_amount = sum_add_amount.get(
        'additional_amount__sum') if sum_add_amount.get('additional_amount__sum') else 0

    amount2 = sum_amount2.get('amount__sum') if sum_amount2.get(
        'amount__sum') else 0
    additional_amount2 = sum_add_amount2.get('additional_amount__sum') if sum_add_amount2.get(
        'additional_amount__sum') else 0

    proposal.proposal_claim = amount + additional_amount
    proposal.balance = proposal.total_cost - proposal.proposal_claim
    proposal.save()

    proposal2 = Proposal.objects.get(
        proposal_id=claim.additional_proposal) if claim.additional_proposal else None
    if proposal2:
        proposal2.proposal_claim = amount2 + additional_amount2
        proposal2.balance = proposal2.total_cost - proposal2.proposal_claim
        proposal2.save()

    return HttpResponseRedirect(reverse('claim-index', args=[_tab, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_claim.claim_id, apps_claim.claim_date, apps_distributor.distributor_name, apps_proposal.channel, apps_claim.total_claim, apps_claim.status, apps_claimrelease.sequence FROM apps_distributor INNER JOIN apps_budget ON apps_distributor.distributor_id = apps_budget.budget_distributor_id INNER JOIN apps_proposal ON apps_budget.budget_id = apps_proposal.budget_id INNER JOIN apps_claim ON apps_proposal.proposal_id = apps_claim.proposal_id INNER JOIN apps_claimrelease ON apps_claim.claim_id = apps_claimrelease.claim_id INNER JOIN (SELECT claim_id, MIN(sequence) AS seq FROM apps_claimrelease WHERE claim_approval_status = 'N' GROUP BY claim_id ORDER BY sequence ASC) AS q_group ON apps_claimrelease.claim_id = q_group.claim_id AND apps_claimrelease.sequence = q_group.seq WHERE (apps_claim.status = 'PENDING' OR apps_claim.status = 'IN APPROVAL') AND apps_claimrelease.claim_approval_id = '" + str(request.user.user_id) + "'")
        release = cursor.fetchall()

    context = {
        'data': release,
        'segment': 'claim_release',
        'group_segment': 'claim',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CLAIM-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/claim_release_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_view(request, _id, _is_revise):
    claim = Claim.objects.get(claim_id=_id)
    form = FormClaimView(instance=claim)
    approved = ClaimRelease.objects.get(
        claim_id=_id, claim_approval_id=request.user.user_id).claim_approval_status
    program = Program.objects.get(program_id=claim.program_id)

    context = {
        'form': form,
        'data': claim,
        'approved': approved,
        'program': program,
        'is_revise': _is_revise,
        'status': claim.status,
        'segment': 'claim_release',
        'group_segment': 'claim',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CLAIM-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
        'btn_release': ClaimRelease.objects.get(claim_id=_id, claim_approval_id=request.user.user_id),
    }
    return render(request, 'home/claim_release_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_update(request, _id):
    claim = Claim.objects.get(claim_id=_id)
    program = Program.objects.get(program_id=claim.program_id)
    proposal = Proposal.objects.get(proposal_id=claim.proposal.proposal_id)
    proposals = Proposal.objects.filter(
        status='OPEN', area=claim.area, balance__gt=0, budget__budget_distributor=claim.proposal.budget.budget_distributor).order_by('-proposal_id')
    message = '0'
    add_prop = '0'
    difference = 0
    add_proposals = None
    add_prop_before = claim.additional_proposal
    amount_before = claim.amount
    _invoice = claim.invoice
    _invoice_date = claim.invoice_date
    _due_date = claim.due_date
    _amount = claim.amount
    _remarks = claim.remarks
    _additional_proposal = claim.additional_proposal
    _additional_amount = claim.additional_amount

    if request.POST:
        form = FormClaimUpdate(
            request.POST, request.FILES, instance=claim)
        difference = int(request.POST.get('amount')) - \
            (int(proposal.balance) + int(claim.amount))
        if int(request.POST.get('amount')) > (int(proposal.balance) + int(claim.amount)) and request.POST.get('additional_proposal') == '':
            add_prop = '1'
            message = 'Claim amount is greater than proposal balance.'
            add_proposals = Proposal.objects.filter(status='OPEN', area=claim.area.area_id, channel=proposal.channel, balance__gte=difference, budget__budget_distributor=claim.proposal.budget.budget_distributor).exclude(
                proposal_id=proposal.proposal_id).order_by('-proposal_id')
        else:
            if form.is_valid():
                parent = form.save(commit=False)
                invoice = _invoice if form.cleaned_data['invoice'] != _invoice else None
                invoice_date = _invoice_date if form.cleaned_data[
                    'invoice_date'] != _invoice_date else None
                due_date = _due_date if form.cleaned_data['due_date'] != _due_date else None
                claim_amount = _amount if form.cleaned_data['amount'] != _amount else None
                remarks = _remarks if form.cleaned_data['remarks'] != _remarks else None
                additional_proposal = _additional_proposal if request.POST.get(
                    'additional_proposal') != _additional_proposal else None
                add_amount = _additional_amount if request.POST.get(
                    'additional_amount') != _additional_amount else None
                parent.total_claim = Decimal(request.POST.get('amount'))
                parent.amount = proposal.balance + amount_before if request.POST.get(
                    'additional_proposal') else Decimal(request.POST.get('amount'))
                if int(request.POST.get('amount')) > (int(proposal.balance) + int(amount_before)):
                    parent.additional_proposal_id = request.POST.get(
                        'additional_proposal')
                else:
                    parent.additional_proposal_id = None
                parent.additional_amount = difference if request.POST.get(
                    'additional_proposal') else 0
                parent.save()

                sum_amount = Claim.objects.filter(
                    proposal_id=parent.proposal_id).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount = Claim.objects.filter(additional_proposal=parent.proposal_id).exclude(
                    status__in=['REJECTED', 'DRAFT']).aggregate(Sum('additional_amount'))

                sum_amount2 = Claim.objects.filter(
                    proposal_id=parent.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount2 = Claim.objects.filter(additional_proposal=parent.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(
                    Sum('additional_amount'))

                amount = sum_amount.get('amount__sum') if sum_amount.get(
                    'amount__sum') else 0
                additional_amount = sum_add_amount.get(
                    'additional_amount__sum') if sum_add_amount.get('additional_amount__sum') else 0

                amount2 = sum_amount2.get('amount__sum') if sum_amount2.get(
                    'amount__sum') else 0
                additional_amount2 = sum_add_amount2.get('additional_amount__sum') if sum_add_amount2.get(
                    'additional_amount__sum') else 0

                proposal.proposal_claim = amount + additional_amount
                proposal.balance = proposal.total_cost - proposal.proposal_claim
                proposal.save()

                proposal2 = Proposal.objects.get(
                    proposal_id=parent.additional_proposal) if parent.additional_proposal else None
                if proposal2:
                    proposal2.proposal_claim = amount2 + additional_amount2
                    proposal2.balance = proposal2.total_cost - proposal2.proposal_claim
                    proposal2.save()
                else:
                    proposal3 = Proposal.objects.get(
                        proposal_id=add_prop_before) if add_prop_before else None
                    if proposal3:
                        proposal3.proposal_claim = amount2 + additional_amount2
                        proposal3.balance = proposal3.total_cost - proposal3.proposal_claim
                        proposal3.save()

                recipients = []

                release = ClaimRelease.objects.get(
                    claim_id=_id, claim_approval_id=request.user.user_id)
                release.revise_note = request.POST.get('revise_note')
                release.save()

                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.entry_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
                    entry_mail = cursor.fetchone()
                    if entry_mail:
                        recipients.append(entry_mail[1])

                    cursor.execute(
                        "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.update_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
                    update_mail = cursor.fetchone()
                    if update_mail:
                        recipients.append(update_mail[1])

                    cursor.execute(
                        "SELECT claim_id, claim_approval_email FROM apps_claimrelease WHERE claim_id = '" + str(_id) + "' AND claim_approval_status = 'Y'")
                    approver_mail = cursor.fetchall()
                    for mail in approver_mail:
                        recipients.append(mail[1])

                subject = 'Claim Revised'
                msg = 'Dear All,\n\nThe following is revised claim for Claim No. ' + \
                    str(_id) + ':\n'
                if invoice:
                    msg += '\nBEFORE\n'
                    msg += 'Invoice: ' + str(invoice) + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Invoice: ' + \
                        form.cleaned_data['invoice'] + '\n'

                if invoice_date:
                    msg += '\nBEFORE\n'
                    msg += 'Invoice Date: ' + \
                        invoice_date.strftime('%d %b %Y') + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Invoice Date: ' + \
                        form.cleaned_data['invoice_date'].strftime(
                            '%d %b %Y') + '\n'

                if due_date:
                    msg += '\nBEFORE\n'
                    msg += 'Due Date: ' + \
                        due_date.strftime('%d %b %Y') + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Due Date: ' + \
                        form.cleaned_data['due_date'].strftime(
                            '%d %b %Y') + '\n'

                if claim_amount:
                    msg += '\nBEFORE\n'
                    msg += 'Amount: ' + str(claim_amount) + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Amount: ' + \
                        str(form.cleaned_data['amount']) + '\n'

                if remarks:
                    msg += '\nBEFORE\n'
                    msg += 'Remarks: ' + str(remarks) + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Remarks: ' + \
                        form.cleaned_data['remarks'] + '\n'

                if additional_proposal:
                    msg += '\nBEFORE\n'
                    msg += 'Additional Proposal: ' + \
                        str(additional_proposal) + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Additional Proposal: ' + \
                        request.POST.get('additional_proposal') + '\n'

                if add_amount:
                    msg += '\nBEFORE\n'
                    msg += 'Additional Amount: ' + \
                        str(add_amount) + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Additional Amount: ' + \
                        request.POST.get('additional_amount') + '\n'

                msg += '\nNote: ' + \
                    str(release.revise_note) + '\n\nClick the following link to view the claim.\n' + host.url + 'claim/view/inapproval/' + str(_id) + '/' + \
                    '\n\nThank you.'

                recipient_list = list(dict.fromkeys(recipients))
                send_email(subject, msg, recipient_list)

                return HttpResponseRedirect(reverse('claim-release-view', args=[_id, 0]))
    else:
        form = FormClaimUpdate(instance=claim)

    # msg = form.errors
    context = {
        'form': form,
        'data': claim,
        'program': program,
        'message': message,
        'add_prop': add_prop,
        'add_proposals': add_proposals,
        'proposals': proposals,
        'difference': difference,
        'segment': 'claim_release',
        'group_segment': 'claim',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLAIM-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_release_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_approve(request, _id):
    claim = Claim.objects.get(claim_id=_id)
    release = ClaimRelease.objects.get(
        claim_id=_id, claim_approval_id=request.user.user_id)
    release.claim_approval_status = 'Y'
    release.claim_approval_date = timezone.now()
    release.save()

    highest_approval = ClaimRelease.objects.filter(
        claim_id=_id, limit__gt=claim.total_claim).aggregate(Min('sequence')) if ClaimRelease.objects.filter(claim_id=_id, limit__gt=claim.total_claim).count() > 0 else ClaimRelease.objects.filter(claim_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = ClaimRelease.objects.filter(
            claim_id=_id, sequence__lt=highest_sequence).order_by('sequence').last()
    else:
        approval = ClaimRelease.objects.filter(
            claim_id=_id).order_by('sequence').last()

    if release.sequence == approval.sequence:
        claim.status = 'OPEN'

        recipients = []

        maker = claim.entry_by
        maker_mail = User.objects.get(user_id=maker).email
        recipients.append(maker_mail)

        approvers = ClaimRelease.objects.filter(
            claim_id=_id, notif=True, claim_approval_status='Y')
        for i in approvers:
            recipients.append(i.claim_approval_email)

        subject = 'Claim Approved'
        msg = 'Dear All,\n\nClaim No. ' + str(_id) + ' has been approved.\n\nClick the following link to view the claim.\n' + host.url + 'claim/view/open/' + str(_id) + \
            '\n\nThank you.'
        recipient_list = list(dict.fromkeys(recipients))
        send_email(subject, msg, recipient_list)
    else:
        claim.status = 'IN APPROVAL'

        email = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='N').order_by(
            'sequence').values_list('claim_approval_email', flat=True)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT claim_approval_name FROM apps_claimrelease WHERE claim_id = '" + str(_id) + "' AND claim_approval_status = 'N' ORDER BY sequence LIMIT 1")
            approver = cursor.fetchone()

        subject = 'Claim Approval'
        msg = 'Dear ' + approver[0] + ',\n\nYou have a new claim to approve. Please check your claim release list.\n\n' + \
            'Click this link to approve, revise, return or reject this claim.\n' + host.url + 'claim_release/view/' + str(_id) + '/0/' + \
            '\n\nThank you.'
        send_email(subject, msg, [email[0]])

    claim.save()

    return HttpResponseRedirect(reverse('claim-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_return(request, _id):
    recipients = []
    draft = False

    try:
        return_to = ClaimRelease.objects.get(
            claim_id=_id, return_to=True, sequence__lt=ClaimRelease.objects.get(claim_id=_id, claim_approval_id=request.user.user_id).sequence)

        if return_to:
            approvers = ClaimRelease.objects.filter(
                claim_id=_id, sequence__gte=ClaimRelease.objects.get(claim_id=_id, return_to=True).sequence, sequence__lt=ClaimRelease.objects.get(claim_id=_id, claim_approval_id=request.user.user_id).sequence)
    except ClaimRelease.DoesNotExist:
        approvers = ClaimRelease.objects.filter(
            claim_id=_id, sequence__lte=ClaimRelease.objects.get(claim_id=_id, claim_approval_id=request.user.user_id).sequence)
        draft = True

    for i in approvers:
        recipients.append(i.claim_approval_email)
        i.claim_approval_status = 'N'
        i.claim_approval_date = None
        i.revise_note = ''
        i.return_note = ''
        i.reject_note = ''
        i.mail_sent = False
        i.save()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.entry_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.update_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

    note = ClaimRelease.objects.get(
        claim_id=_id, claim_approval_id=request.user.user_id)
    note.return_note = request.POST.get('return_note')
    note.save()

    subject = 'Claim Returned'
    msg = 'Dear All,\n\nClaim No. ' + str(_id) + ' has been returned.\n\nNote: ' + \
        str(note.return_note) + \
        '\n\nClick the following link to revise the claim.\n'

    if draft:
        claim = Claim.objects.get(claim_id=_id)
        claim.status = 'DRAFT'
        claim.save()
        msg += host.url + 'claim/view/pending/' + str(_id) + \
            '\n\nThank you.'
    else:
        msg += host.url + 'claim_release/view/' + \
            str(_id) + '/0/\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('claim-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_reject(request, _id):
    claim = Claim.objects.get(claim_id=_id)
    proposal = Proposal.objects.get(proposal_id=claim.proposal.proposal_id)
    recipients = []

    try:
        approvers = ClaimRelease.objects.filter(
            claim_id=_id, sequence__lt=ClaimRelease.objects.get(claim_id=_id, claim_approval_id=request.user.user_id).sequence)
    except ClaimRelease.DoesNotExist:
        pass

    for i in approvers:
        recipients.append(i.claim_approval_email)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.entry_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.update_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

    note = ClaimRelease.objects.get(
        claim_id=_id, claim_approval_id=request.user.user_id)
    note.reject_note = request.POST.get('reject_note')
    note.save()

    subject = 'Claim Rejected'
    msg = 'Dear All,\n\nClaim No. ' + str(_id) + ' has been rejected.\n\nNote: ' + \
        str(note.reject_note) + \
        '\n\nClick the following link to see the claim.\n'

    claim = Claim.objects.get(claim_id=_id)
    claim.status = 'REJECTED'
    claim.save()

    sum_amount = Claim.objects.filter(
        proposal_id=claim.proposal_id).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
    sum_add_amount = Claim.objects.filter(additional_proposal=claim.proposal_id).exclude(
        status__in=['REJECTED', 'DRAFT']).aggregate(Sum('additional_amount'))

    sum_amount2 = Claim.objects.filter(
        proposal_id=claim.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
    sum_add_amount2 = Claim.objects.filter(additional_proposal=claim.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(
        Sum('additional_amount'))

    amount = sum_amount.get('amount__sum') if sum_amount.get(
        'amount__sum') else 0
    additional_amount = sum_add_amount.get(
        'additional_amount__sum') if sum_add_amount.get('additional_amount__sum') else 0

    amount2 = sum_amount2.get('amount__sum') if sum_amount2.get(
        'amount__sum') else 0
    additional_amount2 = sum_add_amount2.get('additional_amount__sum') if sum_add_amount2.get(
        'additional_amount__sum') else 0

    proposal.proposal_claim = amount + additional_amount
    proposal.balance = proposal.total_cost - proposal.proposal_claim
    proposal.save()

    proposal2 = Proposal.objects.get(
        proposal_id=claim.additional_proposal) if claim.additional_proposal else None
    if proposal2:
        proposal2.proposal_claim = amount2 + additional_amount2
        proposal2.balance = proposal2.total_cost - proposal2.proposal_claim
        proposal2.save()

    msg += host.url + 'claim/view/reject/' + str(_id) + \
        '\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('claim-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_print(request, _id):
    claim = Claim.objects.get(claim_id=_id)
    claim_id = _id.replace('/', '-')

    # Create a new PDF file with landscape orientation
    filename = 'claim_' + claim_id + '.pdf'
    pdf_file = canvas.Canvas(filename, pagesize=landscape(A4))

    # Set the font and font size
    pdf_file.setFont('Helvetica-Bold', 11)

    # Add logo in the center of the page
    logo_path = 'https://aqiqahon.sahabataqiqah.co.id/apps/static/img/logo.png'
    logo_width = 60
    logo_height = 60
    page_width = landscape(A4)
    logo_x = (page_width[0] - logo_width) / 2
    pdf_file.drawImage(logo_path, logo_x, 515,
                       width=logo_width, height=logo_height)

    # Add title in the center of page width
    title = 'DEBIT NOTE'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 11)
    title_x = (page_width[0] - title_width) / 2
    pdf_file.setFont('Helvetica-Bold', 11)
    pdf_file.drawString(title_x, 500, title)

    # Write the claim details
    y = 450
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Claim No.')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(claim.claim_id))
    pdf_file.setFont('Helvetica-Bold', 8)
    y -= 10
    pdf_file.drawString(25, y, 'Claim Date')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, claim.claim_date.strftime('%d %b %Y'))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Proposal No.')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(claim.proposal.proposal_id))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Program Name')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(claim.proposal.program_name))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Invoice No.')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(claim.invoice))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Invoice Date')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, claim.invoice_date.strftime('%d %b %Y'))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Due Date')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, claim.due_date.strftime('%d %b %Y'))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Amount')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, '{:,}'.format(claim.total_claim))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Additional Proposal')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(
        claim.additional_proposal if claim.additional_proposal else '-'))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Additional Amount')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, '{:,}'.format(
        claim.additional_amount) if claim.additional_amount else '-')
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Tax')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, '{:,}'.format(claim.tax))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Total Amount')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, '{:,}'.format(claim.total))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Remarks')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(claim.remarks))

    y -= 50
    col_width = (page_width[0] - 50) / 11
    approver = ClaimRelease.objects.filter(
        claim_id=_id, claim_approval_status='Y', printed=True).order_by('sequence')
    verificator = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='verificator', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='verificator', printed=True).exists() else 0
    area_approver = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='area_approver', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='area_approver', printed=True).exists() else 0
    checker = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='checker', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='checker', printed=True).exists() else 0
    ho_approver = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='ho_approver', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='ho_approver', printed=True).exists() else 0
    validator = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='validator', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='validator', printed=True).exists() else 0
    finalizer = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='finalizer', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='finalizer', printed=True).exists() else 0

    verificator_count = verificator['id'] if verificator else 0
    area_approver_count = area_approver['id'] if area_approver else 0
    checker_count = checker['id'] if checker else 0
    ho_approver_count = ho_approver['id'] if ho_approver else 0
    validator_count = validator['id'] if validator else 0
    finalizer_count = finalizer['id'] if finalizer else 0

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25, y-5, col_width, 15, stroke=True)
    title = 'Prepared By'
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + col_width, y-5,
                  col_width * verificator_count, 15, stroke=True)
    title = 'Verified By' if verificator_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + col_width + \
        ((col_width * verificator_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + (col_width * (verificator_count + 1)), y-5,
                  col_width * area_approver_count, 15, stroke=True)
    title = 'Approved By' if area_approver_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width * (verificator_count + 1)) + \
        ((col_width * area_approver_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + (col_width * (verificator_count + area_approver_count + 1)),
                  y-5, col_width * checker_count, 15, stroke=True)
    title = 'Checked By' if checker_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width * (verificator_count + area_approver_count + 1)
                    ) + ((col_width * checker_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + (col_width * (verificator_count + area_approver_count +
                  checker_count + 1)), y-5, col_width * ho_approver_count, 15, stroke=True)
    title = 'Approved By' if ho_approver_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width * (verificator_count + area_approver_count +
                    checker_count + 1)) + ((col_width * ho_approver_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + (col_width * (verificator_count + area_approver_count + checker_count +
                  ho_approver_count + 1)), y-5, col_width * validator_count, 15, stroke=True)
    title = 'Validated By' if validator_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width * (verificator_count + area_approver_count + checker_count +
                    ho_approver_count + 1)) + ((col_width * validator_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + (col_width * (verificator_count + area_approver_count + checker_count +
                  ho_approver_count + validator_count + 1)), y-5, col_width * finalizer_count, 15, stroke=True)
    title = 'Approved By' if finalizer_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width * (verificator_count + area_approver_count + checker_count +
                    ho_approver_count + validator_count + 1)) + ((col_width * finalizer_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(25, y - 55, col_width, 50, stroke=True)
    sign_path = User.objects.get(user_id=claim.entry_by).signature.path if User.objects.get(
        user_id=claim.entry_by).signature else ''
    if sign_path:
        pdf_file.drawImage(sign_path, 30, y - 50,
                           width=col_width - 10, height=40)
    else:
        pass
    pdf_file.rect(25, y - 70, col_width, 15, stroke=True)
    title = claim.entry_pos
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 25 + (col_width - title_width) / 2
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(title_x, y - 65, title)
    pdf_file.rect(25, y - 85, col_width, 15, stroke=True)
    pdf_file.setFont("Helvetica", 8)
    title = 'Date: ' + claim.entry_date.strftime('%d/%m/%Y')
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width - title_width) / 2
    pdf_file.drawString(title_x, y - 80, title)

    for i in range(1, approver.count() + 1):
        pdf_file.rect(25 + (col_width * i), y - 55, col_width, 50, stroke=True)
        if approver:
            sign_path = User.objects.get(user_id=approver[i - 1].claim_approval_id).signature.path if User.objects.get(
                user_id=approver[i - 1].claim_approval_id).signature else ''
            if sign_path:
                pdf_file.drawImage(sign_path, 30 + (col_width * i), y - 50,
                                   width=col_width - 10, height=40)
            else:
                pass
            pdf_file.rect(25 + (col_width * i), y - 70,
                          col_width, 15, stroke=True)
            title = approver[i - 1].claim_approval_position
            title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
            title_x = 25 + (col_width * i) + (col_width - title_width) / 2
            pdf_file.setFont("Helvetica-Bold", 8)
            pdf_file.drawString(title_x, y - 65, title)
            pdf_file.rect(25 + (col_width * i), y - 85,
                          col_width, 15, stroke=True)
            pdf_file.setFont("Helvetica", 8)
            title = 'Date: ' + \
                approver[i - 1].claim_approval_date.strftime('%d/%m/%Y')
            title_width = pdf_file.stringWidth(title, "Helvetica", 8)
            title_x = 25 + (col_width * i) + (col_width - title_width) / 2
            pdf_file.drawString(title_x, y - 80, title)
        else:
            pass

    pdf_file.save()

    return FileResponse(open(filename, 'rb'), content_type='application/pdf')


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-ARCHIVE')
def claim_archive_index(request):
    rejects = Claim.objects.filter(status='REJECTED', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').all

    context = {
        'rejects': rejects,
        'segment': 'claim_archive',
        'group_segment': 'claim',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CLAIM-ARCHIVE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_archive.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-APPROVAL')
def claim_matrix_index(request):
    areas = AreaSales.objects.all()

    context = {
        'data': areas,
        'segment': 'claim_matrix',
        'group_segment': 'approval',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CLAIM-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_matrix_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-APPROVAL')
def claim_matrix_view(request, _id, _channel):
    area = AreaSales.objects.get(area_id=_id)
    channels = AreaChannelDetail.objects.filter(area_id=_id, status=1)
    approvers = ClaimMatrix.objects.filter(area_id=_id, channel_id=_channel)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, position_name, q_claimmatrix.approver_id FROM apps_user INNER JOIN apps_position ON apps_user.position_id = apps_position.position_id LEFT JOIN (SELECT * FROM apps_claimmatrix WHERE area_id = '" + str(_id) + "' AND channel_id = '" + str(_channel) + "') AS q_claimmatrix ON apps_user.user_id = q_claimmatrix.approver_id WHERE q_claimmatrix.approver_id IS NULL")
        users = cursor.fetchall()

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in users:
            if str(i[0]) in check:
                try:
                    approver = ClaimMatrix(
                        area_id=_id, channel_id=_channel, approver_id=i[0])
                    approver.save()
                except IntegrityError:
                    continue
            else:
                ClaimMatrix.objects.filter(
                    area_id=_id, channel_id=_channel, approver_id=i[0]).delete()

        return HttpResponseRedirect(reverse('claim-matrix-view', args=[_id, _channel]))

    context = {
        'data': area,
        'channels': channels,
        'users': users,
        'approvers': approvers,
        'channel': _channel,
        'segment': 'claim_matrix',
        'group_segment': 'approval',
        'tab': 'auth',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CLAIM-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_matrix_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-APPROVAL')
def claim_matrix_update(request, _id, _channel, _approver):
    approvers = ClaimMatrix.objects.get(
        area=_id, channel_id=_channel, approver_id=_approver)

    if request.POST:
        approvers.sequence = int(request.POST.get('sequence'))
        approvers.limit = int(request.POST.get('limit'))
        approvers.return_to = True if request.POST.get('return') else False
        approvers.approve = True if request.POST.get('approve') else False
        approvers.revise = True if request.POST.get('revise') else False
        approvers.returned = True if request.POST.get('returned') else False
        approvers.reject = True if request.POST.get('reject') else False
        approvers.notif = True if request.POST.get('notif') else False
        approvers.printed = True if request.POST.get('printed') else False
        approvers.as_approved = request.POST.get('as_approved')
        approvers.save()

        return HttpResponseRedirect(reverse('claim-matrix-view', args=[_id, _channel]))

    return render(request, 'home/claim_matrix_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-APPROVAL')
def claim_matrix_delete(request, _id, _channel, _arg):
    approvers = ClaimMatrix.objects.get(
        area=_id, channel_id=_channel, approver_id=_arg)
    approvers.delete()

    return HttpResponseRedirect(reverse('claim-matrix-view', args=[_id, _channel]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cl_index(request, _tab):
    cl = CL.objects.all()
    drafts = CL.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-cl_id').all
    draft_count = CL.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).count
    pendings = CL.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-cl_id').all
    pending_count = CL.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).count
    inapprovals = CL.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-cl_id').all
    inapproval_count = CL.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).count
    opens = CL.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-cl_id').all
    open_count = CL.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).count

    context = {
        'data': cl,
        'drafts': drafts,
        'draft_count': draft_count,
        'pendings': pendings,
        'pending_count': pending_count,
        'inapprovals': inapprovals,
        'inapproval_count': inapproval_count,
        'opens': opens,
        'open_count': open_count,
        'tab': _tab,
        'segment': 'cl',
        'group_segment': 'cl',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cl_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cl_add(request, _area, _distributor):
    selected_area = _area
    selected_distributor = _distributor
    area = AreaUser.objects.filter(user_id=request.user.user_id).values_list(
        'area_id', 'area__area_name')
    distributors = Claim.objects.filter(status='OPEN', area=selected_area).values_list(
        'proposal__budget__budget_distributor', 'proposal__budget__budget_distributor__distributor_name').distinct() if selected_area != '0' else None

    no_save = False
    message = ''

    if selected_area != '0' and selected_distributor != '0':
        approvers = CLMatrix.objects.filter(
            area_id=selected_area).order_by('sequence')
        if approvers.count() == 0:
            no_save = True
            message = "No communication letter's approver found for this area."

    try:
        _no = CL.objects.all().order_by('seq_number').last()
    except CL.DoesNotExist:
        _no = None
    if _no is None:
        format_no = '{:04d}'.format(1)
    else:
        format_no = '{:04d}'.format(_no.seq_number + 1)

    _id = 'LBS-5' + format_no + '/' + selected_area + \
        '/' + selected_distributor + '/' + datetime.datetime.now().strftime('%m/%Y')

    if selected_area != '0' and selected_distributor != '0' and not no_save:
        parent = CL(cl_id=_id, cl_date=datetime.datetime.now(), area_id=selected_area,
                    distributor_id=selected_distributor, entry_pos=request.user.position.position_id, seq_number=_no.seq_number + 1 if _no else 1)
        parent.save()

        for i in approvers:
            _cl = CL.objects.get(cl_id=_id)
            release = CLRelease(
                cl_id=_cl,
                cl_approval_id=i.approver_id,
                cl_approval_name=i.approver.username,
                cl_approval_email=i.approver.email,
                cl_approval_position=i.approver.position.position_id,
                sequence=i.sequence,
                limit=i.limit,
                return_to=i.return_to,
                approve=i.approve,
                revise=i.revise,
                returned=i.returned,
                reject=i.reject,
                notif=i.notif,
                printed=i.printed,
                as_approved=i.as_approved)
            release.save()

        return HttpResponseRedirect(reverse('cl-view', args=['draft', _id]))

    context = {
        'selected_area': selected_area,
        'selected_distributor': selected_distributor,
        'area': area,
        'distributors': distributors,
        'no_save': no_save,
        'message': message,
        'segment': 'cl',
        'group_segment': 'cl',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cl_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cl_view(request, _tab, _id):
    cl = CL.objects.get(cl_id=_id)
    cl_detail = CLDetail.objects.filter(cl_id=_id)
    claim = Claim.objects.filter(status='OPEN', area_id=cl.area_id, proposal__budget__budget_distributor=cl.distributor_id).exclude(
        cldetail__claim_id__in=CLDetail.objects.all().values_list('claim_id', flat=True)).values_list('claim_id', 'remarks', 'cldetail__claim_id')

    highest_approval = CLRelease.objects.filter(
        cl_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = CLRelease.objects.filter(
            cl_id=_id, sequence__lt=highest_sequence).order_by('sequence')
    else:
        approval = CLRelease.objects.filter(cl_id=_id).order_by('sequence')

    if request.POST:
        check = request.POST.getlist('checks[]')
        _cl = CL.objects.get(cl_id=_id)
        for i in claim:
            if str(i[0]) in check:
                try:
                    detail = CLDetail(cl_id=_cl, claim_id=i[0])
                    detail.save()
                except IntegrityError:
                    continue
            else:
                CLDetail.objects.filter(cl_id=_id, claim_id=i[0]).delete()

        cl.status = 'PENDING'
        cl.save()

        mail_sent = CLRelease.objects.filter(
            cl_id=_id).order_by('sequence').values_list('mail_sent', flat=True)
        if mail_sent[0] == False:
            email = CLRelease.objects.filter(
                cl_id=_id).order_by('sequence').values_list('cl_approval_email', flat=True)
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT username FROM apps_clrelease INNER JOIN apps_user ON apps_clrelease.cl_approval_id = apps_user.user_id WHERE cl_id_id = '" + str(_id) + "' AND cl_approval_status = 'N' ORDER BY sequence LIMIT 1")
                approver = cursor.fetchone()

            subject = 'CL Approval'
            msg = 'Dear ' + approver[0] + ',\n\nYou have a new CL to approve. Please check your CL release list.\n\n' + \
                'Click this link to approve, revise, return or reject this CL.\n' + host.url + 'cl_release/view/' + str(_id) + '/0/' + \
                '\n\nThank you.'
            send_email(subject, msg, [email[0]])

            # update mail sent to true
            release = CLRelease.objects.filter(
                cl_id=_id).order_by('sequence').first()
            release.mail_sent = True
            release.save()

        return HttpResponseRedirect(reverse('cl-view', args=[_tab, _id]))

    context = {
        'data': cl,
        'cl_detail': cl_detail,
        'claim': claim,
        'tab': _tab,
        'approval': approval,
        'status': cl.status,
        'segment': 'cl',
        'group_segment': 'cl',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CL') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cl_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cldetail_delete(request, _tab, _id):
    detail = CLDetail.objects.get(id=_id)
    detail.delete()

    return HttpResponseRedirect(reverse('cl-view', args=[_tab, detail.cl_id_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cldetail_release_delete(request, _id):
    detail = CLDetail.objects.get(id=_id)
    detail.delete()

    return HttpResponseRedirect(reverse('cl-release-view', args=[detail.cl_id_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cl_delete(request, _tab, _id):
    cl = CL.objects.get(cl_id=_id)

    cl.delete()
    return HttpResponseRedirect(reverse('cl-index', args=[_tab]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_cl.cl_id, apps_cl.cl_date, apps_cl.area_id, apps_distributor.distributor_name, apps_cl.status, apps_clrelease.sequence FROM apps_distributor INNER JOIN apps_cl ON apps_distributor.distributor_id = apps_cl.distributor_id INNER JOIN apps_clrelease ON apps_cl.cl_id = apps_clrelease.cl_id_id INNER JOIN (SELECT cl_id_id, MIN(sequence) AS seq FROM apps_clrelease WHERE cl_approval_status = 'N' GROUP BY cl_id_id ORDER BY sequence ASC) AS q_group ON apps_clrelease.cl_id_id = q_group.cl_id_id AND apps_clrelease.sequence = q_group.seq WHERE (apps_cl.status = 'PENDING' OR apps_cl.status = 'IN APPROVAL') AND apps_clrelease.cl_approval_id = '" + str(request.user.user_id) + "'")
        release = cursor.fetchall()

    context = {
        'data': release,
        'segment': 'cl_release',
        'group_segment': 'cl',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CL-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cl_release_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_view(request, _id, _is_revise):
    cl = CL.objects.get(cl_id=_id)
    cl_detail = CLDetail.objects.filter(cl_id=_id)
    approved = CLRelease.objects.get(
        cl_id=_id, cl_approval_id=request.user.user_id).cl_approval_status
    claim = Claim.objects.filter(status='OPEN', area_id=cl.area_id, proposal__budget__budget_distributor=cl.distributor_id).exclude(
        cldetail__claim_id__in=CLDetail.objects.all().values_list('claim_id', flat=True)).values_list('claim_id', 'remarks', 'cldetail__claim_id')

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in claim:
            if str(i[0]) in check:
                try:
                    detail = CLDetail(cl_id=_id, claim_id=i[0])
                    detail.save()
                except IntegrityError:
                    continue
            else:
                CLDetail.objects.filter(cl_id=_id, claim_id=i[0]).delete()

        return HttpResponseRedirect(reverse('cl-release-view', args=[_id, 0]))

    context = {
        'data': cl,
        'cl_detail': cl_detail,
        'claim': claim,
        'approved': approved,
        'is_revise': _is_revise,
        'segment': 'cl_release',
        'group_segment': 'cl',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CL-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
        'btn_release': CLRelease.objects.get(cl_id=_id, cl_approval_id=request.user.user_id) if not request.user.is_superuser else None,
    }
    return render(request, 'home/cl_release_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_update(request, _id):
    cl = CL.objects.get(cl_id=_id)
    cl_detail = CLDetail.objects.filter(cl_id=_id)
    claim = Claim.objects.filter(status='OPEN', area_id=cl.area_id, proposal__budget__budget_distributor=cl.distributor_id).exclude(
        cldetail__claim_id__in=CLDetail.objects.all().values_list('claim_id', flat=True)).values_list('claim_id', 'remarks', 'cldetail__claim_id')

    _add = ''
    _remove = ''

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in claim:
            if str(i[0]) in check:
                try:
                    detail = CLDetail(cl_id=_id, claim_id=i[0])
                    detail.save()
                    _add += i[0] + '\n'
                except IntegrityError:
                    continue
            else:
                CLDetail.objects.filter(cl_id=_id, claim_id=i[0]).delete()
                _remove += i[0] + '\n'

        recipients = []

        release = CLRelease.objects.get(
            cl_id=_id, cl_approval_id=request.user.user_id)
        release.revise_note = request.POST.get('revise_note')
        release.save()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.entry_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
            entry_mail = cursor.fetchone()
            if entry_mail:
                recipients.append(entry_mail[1])

            cursor.execute(
                "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.update_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
            update_mail = cursor.fetchone()
            if update_mail:
                recipients.append(update_mail[1])

            cursor.execute(
                "SELECT cl_id, cl_approval_email FROM apps_clrelease WHERE cl_id = '" + str(_id) + "' AND cl_approval_status = 'Y'")
            approver_mail = cursor.fetchall()
            for mail in approver_mail:
                recipients.append(mail[1])

        subject = 'CL Revised'
        msg = 'Dear All,\n\nThe following is revised CL for CL No. ' + \
            str(_id) + ':\n'
        msg += '\nCLAIM ADD:\n'
        msg += _add
        msg += '\nCLAIM REMOVE\n'
        msg += _remove

        msg += '\nNote: ' + \
            str(release.revise_note) + '\n\nClick the following link to view the CL.\n' + host.url + 'cl/view/inapproval/' + str(_id) + '/' + \
            '\n\nThank you.'

        recipient_list = list(dict.fromkeys(recipients))
        send_email(subject, msg, recipient_list)

        return HttpResponseRedirect(reverse('cl-release-view', args=[_id, 0]))

    context = {
        'data': cl,
        'cl_detail': cl_detail,
        'claim': claim,
        'segment': 'cl_release',
        'group_segment': 'cl',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CL-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cl_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_approve(request, _id):
    cl = CL.objects.get(cl_id=_id)
    release = CLRelease.objects.get(
        cl_id=_id, cl_approval_id=request.user.user_id)
    release.cl_approval_status = 'Y'
    release.cl_approval_date = timezone.now()
    release.save()

    highest_approval = CLRelease.objects.filter(
        cl_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = CLRelease.objects.filter(
            cl_id=_id, sequence__lt=highest_sequence).order_by('sequence').last()
    else:
        approval = CLRelease.objects.filter(
            cl_id=_id).order_by('sequence').last()

    if release.sequence == approval.sequence:
        cl.status = 'OPEN'

        recipients = []

        maker = cl.entry_by
        maker_mail = User.objects.get(user_id=maker).email
        recipients.append(maker_mail)

        approvers = CLRelease.objects.filter(
            cl_id=_id, notif=True, cl_approval_status='Y')
        for i in approvers:
            recipients.append(i.cl_approval_email)

        subject = 'CL Approved'
        msg = 'Dear All,\n\nCL No. ' + str(_id) + ' has been approved.\n\nClick the following link to view the CL.\n' + host.url + 'cl/view/open/' + str(_id) + \
            '\n\nThank you.'
        recipient_list = list(dict.fromkeys(recipients))
        send_email(subject, msg, recipient_list)
    else:
        cl.status = 'IN APPROVAL'

        email = CLRelease.objects.filter(cl_id=_id, cl_approval_status='N').order_by(
            'sequence').values_list('cl_approval_email', flat=True)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT cl_approval_name FROM apps_clrelease WHERE cl_id_id = '" + str(_id) + "' AND cl_approval_status = 'N' ORDER BY sequence LIMIT 1")
            approver = cursor.fetchone()

        subject = 'CL Approval'
        msg = 'Dear ' + approver[0] + ',\n\nYou have a new CL to approve. Please check your CL release list.\n\n' + \
            'Click this link to approve, revise, return or reject this CL.\n' + host.url + 'cl_release/view/' + str(_id) + '/0/' + \
            '\n\nThank you.'
        send_email(subject, msg, [email[0]])

    cl.save()

    return HttpResponseRedirect(reverse('cl-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_return(request, _id):
    recipients = []
    draft = False

    try:
        return_to = CLRelease.objects.get(
            cl_id=_id, return_to=True, sequence__lt=CLRelease.objects.get(cl_id=_id, cl_approval_id=request.user.user_id).sequence)

        if return_to:
            approvers = CLRelease.objects.filter(
                cl_id=_id, sequence__gte=CLRelease.objects.get(cl_id=_id, return_to=True).sequence, sequence__lt=CLRelease.objects.get(cl_id=_id, cl_approval_id=request.user.user_id).sequence)
    except CLRelease.DoesNotExist:
        approvers = CLRelease.objects.filter(
            claim_id=_id, sequence__lte=CLRelease.objects.get(cl_id=_id, cl_approval_id=request.user.user_id).sequence)
        draft = True

    for i in approvers:
        recipients.append(i.claim_approval_email)
        i.claim_approval_status = 'N'
        i.claim_approval_date = None
        i.revise_note = ''
        i.return_note = ''
        i.reject_note = ''
        i.mail_sent = False
        i.save()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.entry_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.update_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

    note = CLRelease.objects.get(
        cl_id=_id, cl_approval_id=request.user.user_id)
    note.return_note = request.POST.get('return_note')
    note.save()

    subject = 'CL Returned'
    msg = 'Dear All,\n\nCL No. ' + str(_id) + ' has been returned.\n\nNote: ' + \
        str(note.return_note) + \
        '\n\nClick the following link to revise the CL.\n'

    if draft:
        cl = CL.objects.get(claim_id=_id)
        cl.status = 'DRAFT'
        cl.save()
        msg += host.url + 'cl/view/pending/' + str(_id) + \
            '\n\nThank you.'
    else:
        msg += host.url + 'cl_release/view/' + \
            str(_id) + '/0/\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('claim-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_reject(request, _id):
    cl = CL.objects.get(cl_id=_id)
    recipients = []

    try:
        approvers = CLRelease.objects.filter(
            cl_id=_id, sequence__lt=CLRelease.objects.get(cl_id=_id, cl_approval_id=request.user.user_id).sequence)
    except CLRelease.DoesNotExist:
        pass

    for i in approvers:
        recipients.append(i.cl_approval_email)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.entry_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.update_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

    note = CLRelease.objects.get(
        cl_id=_id, cl_approval_id=request.user.user_id)
    note.reject_note = request.POST.get('reject_note')
    note.save()

    cl = CL.objects.get(cl_id=_id)
    cl.status = 'REJECTED'
    cl.save()

    subject = 'CL Rejected'
    msg = 'Dear All,\n\nCL No. ' + str(_id) + ' has been rejected.\n\nNote: ' + \
        str(note.reject_note) + \
        '\n\nClick the following link to see the CL.\n'
    msg += host.url + 'cl/view/reject/' + str(_id) + \
        '\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('cl-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-APPROVAL')
def cl_matrix_index(request):
    areas = AreaSales.objects.all()

    context = {
        'data': areas,
        'segment': 'cl_matrix',
        'group_segment': 'approval',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CL-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cl_matrix_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-APPROVAL')
def cl_matrix_view(request, _id):
    area = AreaSales.objects.get(area_id=_id)
    approvers = CLMatrix.objects.filter(area_id=_id)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, position_name, q_clmatrix.approver_id FROM apps_user INNER JOIN apps_position ON apps_user.position_id = apps_position.position_id LEFT JOIN (SELECT * FROM apps_clmatrix WHERE area_id = '" + str(_id) + "') AS q_clmatrix ON apps_user.user_id = q_clmatrix.approver_id WHERE q_clmatrix.approver_id IS NULL")
        users = cursor.fetchall()

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in users:
            if str(i[0]) in check:
                try:
                    approver = CLMatrix(area_id=_id, approver_id=i[0])
                    approver.save()
                except IntegrityError:
                    continue
            else:
                CLMatrix.objects.filter(area_id=_id, approver_id=i[0]).delete()

        return HttpResponseRedirect(reverse('cl-matrix-view', args=[_id]))

    context = {
        'data': area,
        'users': users,
        'approvers': approvers,
        'segment': 'cl_matrix',
        'group_segment': 'approval',
        'tab': 'auth',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CL-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cl_matrix_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-APPROVAL')
def cl_matrix_update(request, _id, _approver):
    approvers = CLMatrix.objects.get(area=_id, approver_id=_approver)

    if request.POST:
        approvers.sequence = int(request.POST.get('sequence'))
        # approvers.limit = int(request.POST.get('limit'))
        approvers.return_to = True if request.POST.get('return') else False
        approvers.approve = True if request.POST.get('approve') else False
        approvers.revise = True if request.POST.get('revise') else False
        approvers.returned = True if request.POST.get('returned') else False
        approvers.reject = True if request.POST.get('reject') else False
        approvers.notif = True if request.POST.get('notif') else False
        approvers.printed = True if request.POST.get('printed') else False
        approvers.as_approved = request.POST.get('as_approved')
        approvers.save()

        return HttpResponseRedirect(reverse('cl-matrix-view', args=[_id]))

    return render(request, 'home/cl_matrix_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-APPROVAL')
def cl_matrix_delete(request, _id, _arg):
    approvers = CLMatrix.objects.get(area=_id, approver_id=_arg)
    approvers.delete()

    return HttpResponseRedirect(reverse('cl-matrix-view', args=[_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cl_print(request, _id):
    cl = CL.objects.get(cl_id=_id)
    cl_detail = CLDetail.objects.filter(cl_id=_id)
    detail_sum = Claim.objects.filter(
        claim_id__in=cl_detail.values_list('claim_id')).aggregate(total=Sum('total_claim'))
    approver = CLRelease.objects.filter(
        cl_id=_id, cl_approval_status='Y', printed=True).order_by('sequence')
    cl_id = _id.replace('/', '-')

    # Create a new PDF file with landscape orientation
    filename = 'CL-' + cl_id + '.pdf'
    pdf_file = canvas.Canvas(filename, pagesize=landscape(A4))

    # Set the font and font size
    pdf_file.setFont('Helvetica-Bold', 8)

    # Add logo in the center of the page
    logo_path = 'https://aqiqahon.sahabataqiqah.co.id/apps/static/img/logo.png'
    logo_width = 60
    logo_height = 60
    page_width = landscape(A4)
    logo_x = (page_width[0] - logo_width) / 2
    pdf_file.drawImage(logo_path, logo_x, 515,
                       width=logo_width, height=logo_height)

    # Add header
    y = 500
    pdf_file.drawString(25, y, 'Jakarta, ' + cl.cl_date.strftime('%d %B %Y'))
    pdf_file.drawRightString(800, y, 'No. ' + cl.cl_id)

    y -= 25
    pdf_file.drawString(25, y, 'Kepada Yth.')
    y -= 10
    pdf_file.drawString(25, y, cl.distributor.distributor_name)
    y -= 10
    pdf_file.drawString(25, y, 'Di tempat')

    y -= 25
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(25, y, 'Dengan hormat,')

    y -= 25
    pdf_file.drawString(25, y, 'Bersama ini kami sampaikan daftar program yang akan memotong Budget Selisih Margin PT. ABC PI di ' +
                        cl.distributor.distributor_name + ' sebagai berikut:')

    y -= 20
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.rect(25, y - 5, 25, 15, stroke=True)
    title = 'No.'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 25 + (25 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(50, y-5, 150, 15, stroke=True)
    title = 'No. Klaim'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 50 + (150 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(200, y-5, 225, 15, stroke=True)
    title = 'Deskripsi'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 200 + (225 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(425, y-5, 75, 15, stroke=True)
    title = 'Nilai Klaim'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 425 + (75 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(500, y-5, 150, 15, stroke=True)
    title = 'No. Surat Program'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 500 + (150 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(650, y-5, 150, 15, stroke=True)
    title = 'No. Proposal'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 650 + (150 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont("Helvetica", 8)
    n = 0
    for i in cl_detail:
        y -= 15
        n += 1
        pdf_file.rect(25, y - 5, 25, 15, stroke=True)
        title = str(n)
        title_width = pdf_file.stringWidth(title, 'Helvetica', 8)
        title_x = 25 + (25 - title_width) / 2
        pdf_file.drawString(title_x, y, title)
        pdf_file.rect(50, y - 5, 150, 15, stroke=True)
        pdf_file.drawString(55, y, i.claim_id)
        pdf_file.rect(200, y - 5, 225, 15, stroke=True)
        remarks = Truncator(i.claim.remarks).chars(55)
        pdf_file.drawString(205, y, remarks)
        pdf_file.rect(425, y - 5, 75, 15, stroke=True)
        pdf_file.drawRightString(495, y, "{:,}".format(i.claim.total_claim))
        pdf_file.rect(500, y - 5, 150, 15, stroke=True)
        pdf_file.drawString(505, y, i.claim.program_id)
        pdf_file.rect(650, y - 5, 150, 15, stroke=True)
        pdf_file.drawString(655, y, i.claim.proposal_id)

    y -= 15
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.rect(25, y - 5, 775, 15, stroke=True)
    pdf_file.drawRightString(420, y, 'TOTAL')
    pdf_file.drawRightString(495, y, "{:,}".format(detail_sum['total']))

    y -= 25
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(
        25, y, 'Demikian surat konfirmasi ini kami sampaikan. Atas perhatian dan kerjasamanya kami ucapkann terima kasih.')

    y -= 25
    pdf_file.drawString(25, y, 'Hormat Kami,')

    col_width = (page_width[0] - 50) / 11
    for i in range(1, approver.count() + 1):
        if approver:
            sign_path = User.objects.get(user_id=approver[i - 1].cl_approval_id).signature.path if User.objects.get(
                user_id=approver[i - 1].cl_approval_id).signature else ''
            pos = User.objects.get(
                user_id=approver[i - 1].cl_approval_id).position
            if sign_path:
                pdf_file.drawImage(sign_path, 25 + ((col_width * 2) * (i - 1)), y - 50,
                                   width=col_width - 10, height=40)
            else:
                pass

            pdf_file.setFont("Helvetica-Bold", 8)
            pdf_file.drawString(25 + ((col_width * 2) * (i - 1)),
                                y - 60, approver[i - 1].cl_approval_name)
            pdf_file.setFont("Helvetica", 8)
            pdf_file.drawString(25 + ((col_width * 2) * (i - 1)),
                                y - 70, str(pos))

    y -= 95
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, 'Cc : Finance Department')

    pdf_file.save()

    return FileResponse(open(filename, 'rb'), content_type='application/pdf')


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_index(request):
    regions = Region.objects.all()

    context = {
        'data': regions,
        'segment': 'region',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='REGION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/region_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_add(request):
    if request.POST:
        form = FormRegion(request.POST)
        if form.is_valid():
            region = form.save(commit=False)
            region.region_id = form.cleaned_data['region_id'].replace(' ', '')
            region.save()

            return HttpResponseRedirect(reverse('region-view', args=[region.region_id]))
    else:
        form = FormRegion()

    message = form.errors
    context = {
        'form': form,
        'segment': 'region',
        'group_segment': 'master',
        'crud': 'add',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='REGION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/region_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_view(request, _id):
    region = Region.objects.get(region_id=_id)
    form = FormRegionView(instance=region)
    details = RegionDetail.objects.filter(region_id=_id)
    areas = AreaSales.objects.exclude(regiondetail__region_id=_id).values_list(
        'area_id', 'area_name', 'regiondetail__region_id')

    if request.POST:
        check = request.POST.getlist('checks[]')
        for area in areas:
            if str(area[0]) in check:
                try:
                    detail = RegionDetail(region_id=_id, area_id=area[0])
                    detail.save()
                except IntegrityError:
                    continue
            else:
                RegionDetail.objects.filter(
                    region_id=_id, area_id=area[0]).delete()

    context = {
        'form': form,
        'data': region,
        'areas': areas,
        'detail': details,
        'segment': 'region',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='REGION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/region_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_update(request, _id):
    region = Region.objects.get(region_id=_id)
    detail = RegionDetail.objects.filter(region_id=_id)

    if request.POST:
        form = FormRegionUpdate(request.POST, instance=region)
        if form.is_valid():
            region = form.save(commit=False)
            region.save()

            return HttpResponseRedirect(reverse('region-view', args=[_id]))
    else:
        form = FormRegionUpdate(instance=region)

    message = form.errors
    context = {
        'form': form,
        'data': region,
        'detail': detail,
        'segment': 'region',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='REGION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/region_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_delete(request, _id):
    region = Region.objects.get(region_id=_id)
    region.delete()

    return HttpResponseRedirect(reverse('region-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_detail_delete(request, _id, _area):
    detail = RegionDetail.objects.get(region_id=_id, area_id=_area)
    detail.delete()

    return HttpResponseRedirect(reverse('region-view', args=[_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_index(request):
    customers = Customer.objects.all()

    context = {
        'data': customers,
        'segment': 'customer',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUSTOMER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/customer_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_add(request):
    if request.POST:
        form = FormCustomer(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.save()

            return HttpResponseRedirect(reverse('customer-view', args=[customer.customer_id, '0']))
    else:
        form = FormCustomer()

    message = form.errors
    context = {
        'form': form,
        'segment': 'customer',
        'group_segment': 'master',
        'crud': 'add',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CUSTOMER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/customer_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_view(request, _id, _msg):
    customer = Customer.objects.get(customer_id=_id)
    form = FormCustomerView(instance=customer)
    form_detail = FormCustomerDetail(
        initial={'child_birth': datetime.date.today()})
    details = CustomerDetail.objects.filter(customer_id=_id)
    msg = _msg

    if request.POST:
        form_detail = FormCustomerDetail(request.POST)
        if form_detail.is_valid():
            try:
                detail = form_detail.save(commit=False)
                detail.customer_id = _id
                detail.child_sex = request.POST.get('child_sex')
                detail.save()
            except IntegrityError:
                msg = 'Nama anak sudah ada.'

            return HttpResponseRedirect(reverse('customer-view', args=[_id, msg]))

    context = {
        'form': form,
        'form_detail': form_detail,
        'data': customer,
        'details': details,
        'msg': msg,
        'segment': 'customer',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CUSTOMER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/customer_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_update(request, _id):
    customer = Customer.objects.get(customer_id=_id)

    if request.POST:
        form = FormCustomerUpdate(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.save()

            return HttpResponseRedirect(reverse('customer-view', args=[_id, '0']))
    else:
        form = FormCustomerUpdate(instance=customer)

    context = {
        'form': form,
        'data': customer,
        'msg': '0',
        'segment': 'customer',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CUSTOMER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/customer_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_delete(request, _id):
    customer = Customer.objects.get(customer_id=_id)
    customer.delete()

    return HttpResponseRedirect(reverse('customer-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_detail_update(request, _id, _child):
    detail = CustomerDetail.objects.get(id=_child)

    if request.POST:
        detail.child_name = request.POST.get('child_name')
        detail.child_birth = request.POST.get('child_birth')
        detail.child_sex = request.POST.get('child_sex')
        detail.child_father = request.POST.get('child_father')
        detail.child_mother = request.POST.get('child_mother')
        detail.save()

        return HttpResponseRedirect(reverse('customer-view', args=[_id, '0']))

    return render(request, 'home/customer_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_detail_delete(request, _id):
    detail = CustomerDetail.objects.get(id=_id)
    detail.delete()

    return HttpResponseRedirect(reverse('customer-view', args=[_id, '0']))


def order_add(request, _reg):
    try:
        _no = Order.objects.filter(
            order_date__year=datetime.datetime.now().year).latest('seq_number').seq_number
    except Order.DoesNotExist:
        _no = None
    if _no is None:
        format_no = '{:05d}'.format(1)
    else:
        format_no = '{:05d}'.format(_no + 1)

    _id = 'INV-1' + format_no + '/' + _reg.upper() + '/SA/' + str(datetime.datetime.now().strftime('%m')) + \
        '/' + str(datetime.datetime.now().year)

    if request.POST:
        form = FormOrder(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.order_id = _id
            order.regional_id = _reg
            order.seq_number = _no + 1 if _no else 1
            order.save()

            return HttpResponseRedirect(reverse('order-child-add', args=[_id, 0]))
    else:
        form = FormOrder(initial={'order_id': _id})

    msg = form.errors
    context = {
        'form': form,
        'crud': 'add',
        'reg': _reg,
        'msg': msg,
    }
    return render(request, 'home/order_add.html', context)


def order_update(request, _id):
    order = Order.objects.get(order_id=_id)

    if request.POST:
        form = FormOrderUpdate(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.save()

            child = OrderChild.objects.filter(order_id=_id)
            if child:
                return HttpResponseRedirect(reverse('order-child-update', args=[_id, child.first().id, 0]))
            else:
                return HttpResponseRedirect(reverse('order-child-add', args=[_id, 0]))
    else:
        form = FormOrderUpdate(instance=order)

    msg = form.errors

    context = {
        'form': form,
        'data': order,
        'msg': msg,
        'crud': 'update',
    }
    return render(request, 'home/order_update.html', context)


def order_child_add(request, _id, _add):
    try:
        last_child = OrderChild.objects.filter(order_id=_id).last()
    except OrderChild.DoesNotExist:
        last_child = None

    if request.POST:
        form = FormOrderChild(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.order_id = _id
            child.child_sex = request.POST.get('child_sex')
            child.save()

            package = OrderPackage.objects.filter(order_id=_id)
            if _add == 1:
                return HttpResponseRedirect(reverse('order-child-add', args=[_id, 0]))
            else:
                if package:
                    return HttpResponseRedirect(reverse('order-package-update', args=[_id, package[0].id, package[0].category_id, package[0].package_id, package[0].type, 0]))
                else:
                    return HttpResponseRedirect(reverse('order-package-add', args=[_id, '0', '0', '0', 0]))
    else:
        form = FormOrderChild(initial={'order': _id})

    msg = form.errors
    context = {
        'form': form,
        'crud': 'add',
        'last_child': last_child,
        'order_id': _id,
        'msg': msg,
    }
    return render(request, 'home/order_child_add.html', context)


def order_cs_child_add(request, _id):
    if request.POST:
        child = OrderChild(
            order_id=_id,
            child_name=request.POST.get('child_name'),
            child_birth=request.POST.get('child_birth'),
            child_sex=request.POST.get('child_sex'),
            child_father=request.POST.get('child_father'),
            child_mother=request.POST.get('child_mother'),
        )
        child.save()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_child_update(request, _id, _child, _add):
    child = OrderChild.objects.get(order_id=_id, id=_child)
    children = OrderChild.objects.filter(order_id=_id).order_by('id')

    first = False
    prev_id = 0

    first_child = OrderChild.objects.filter(order_id=_id).first()
    if first_child.id == _child:
        first = True

    for index, i in enumerate(children):
        if i.id == _child:
            n_child = index + 1

    for i in reversed(children):
        if i.id < _child:
            prev_id = i.id
            break

    if request.POST:
        form = FormOrderChildUpdate(request.POST, instance=child)
        if form.is_valid():
            child = form.save(commit=False)
            child.child_sex = request.POST.get('child_sex')
            child.save()

            last_child = OrderChild.objects.filter(order_id=_id).last()
            if _add == 1:
                return HttpResponseRedirect(reverse('order-child-add', args=[_id, 0]))
            else:
                if last_child.id == _child:
                    package = OrderPackage.objects.filter(order_id=_id)
                    if package:
                        return HttpResponseRedirect(reverse('order-package-update', args=[_id, package[0].id, package[0].category_id, package[0].package_id, package[0].type, 0]))
                    else:
                        return HttpResponseRedirect(reverse('order-package-add', args=[_id, '0', '0', '0', 0]))
                else:
                    for i in OrderChild.objects.filter(order_id=_id):
                        if i.id > _child:
                            return HttpResponseRedirect(reverse('order-child-update', args=[_id, i.id, 0]))
    else:
        form = FormOrderChildUpdate(instance=child)

    context = {
        'form': form,
        'data': child,
        'first_child': first,
        'n_child': n_child,
        'children': children,
        'prev_id': prev_id,
        'crud': 'update',
    }
    return render(request, 'home/order_child_update.html', context)


def order_child_cs_update(request, _id, _child):
    child = OrderChild.objects.get(order_id=_id, id=_child)

    if request.POST:
        child.child_name = request.POST.get('child_name')
        child.child_birth = request.POST.get('child_birth')
        child.child_sex = request.POST.get('child_sex')
        child.child_father = request.POST.get('child_father')
        child.child_mother = request.POST.get('child_mother')
        child.save()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_child_delete(request, _id, _child):
    child = OrderChild.objects.get(order_id=_id, id=_child)
    child.delete()

    first = OrderChild.objects.filter(order_id=_id).first()

    return HttpResponseRedirect(reverse('order-child-update', args=[_id, first.id, 0]))


def order_child_cs_delete(request, _id, _child):
    child = OrderChild.objects.get(order_id=_id, id=_child)
    child.delete()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_package_add(request, _id, _cat, _pack, _type, _add):
    categories = Category.objects.all()
    packages = Package.objects.filter(category=_cat).exclude(package_id__in=OrderPackage.objects.filter(
        order_id=_id).values_list('package_id', flat=True)) if _cat != '0' else None
    box_types = BoxType.objects.all()
    main_cuisines = MainCuisine.objects.filter(package=_pack)
    sub_cuisines = SubCuisine.objects.filter(package=_pack)
    side_cuisines1 = SideCuisine1.objects.filter(package=_pack)
    side_cuisines2 = SideCuisine2.objects.filter(package=_pack)
    side_cuisines3 = SideCuisine3.objects.filter(package=_pack)
    side_cuisines4 = SideCuisine4.objects.filter(package=_pack)
    side_cuisines5 = SideCuisine5.objects.filter(package=_pack)
    last_package = OrderPackage.objects.filter(order_id=_id).last(
    ) if OrderPackage.objects.filter(order_id=_id) else None
    selected_package = Package.objects.get(
        package_id=_pack) if _pack != '0' else None
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id).last()

    if request.POST:
        form = FormOrderPackage(request.POST)
        if form.is_valid():
            package = form.save(commit=False)
            package.order_id = _id
            package.category_id = _cat
            package.package_id = _pack
            package.type = _type
            package.box_type_id = request.POST.get('box_type')
            package.main_cuisine = request.POST.get('main_cuisine')
            package.sub_cuisine = request.POST.get('sub_cuisine')
            package.side_cuisine1 = request.POST.get('side_cuisine1')
            package.side_cuisine2 = request.POST.get('side_cuisine2')
            package.side_cuisine3 = request.POST.get('side_cuisine3')
            package.side_cuisine4 = request.POST.get('side_cuisine4')
            package.side_cuisine5 = request.POST.get('side_cuisine5')
            package.unit_price = selected_package.male_price if _type == 'Jantan' else selected_package.female_price
            package.save()

            total = OrderPackage.objects.filter(
                order_id=_id).aggregate(order=Sum('total_price'))
            order.total_order = total['order']
            order.save()

            if _add == 1:
                return HttpResponseRedirect(reverse('order-package-add', args=[_id, '0', '0', '0', 0]))
            else:
                return HttpResponseRedirect(reverse('order-confirm-update', args=[_id]))
    else:
        form = FormOrderPackage(initial={'order': _id})

    msg = form.errors
    context = {
        'form': form,
        'data': order,
        'crud': 'add',
        'cat': _cat,
        'pack': _pack,
        'type': _type,
        'categories': categories,
        'packages': packages,
        'box_types': box_types,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'last_package': last_package,
        'selected_package': selected_package,
        'order_id': _id,
        'child': child,
        'msg': msg,
    }
    return render(request, 'home/order_package_add.html', context)


def order_cs_package_add(request, _id, _cat, _pack, _type):
    package = Package.objects.get(package_id=_pack)
    if request.POST:
        package = OrderPackage(
            order_id=_id,
            category_id=_cat,
            package_id=_pack,
            type=_type,
            box_type_id=request.POST.get('box_type'),
            main_cuisine=request.POST.get('main_cuisine'),
            sub_cuisine=request.POST.get('sub_cuisine'),
            side_cuisine1=request.POST.get('side_cuisine1'),
            side_cuisine2=request.POST.get('side_cuisine2'),
            side_cuisine3=request.POST.get('side_cuisine3'),
            side_cuisine4=request.POST.get('side_cuisine4'),
            side_cuisine5=request.POST.get('side_cuisine5'),
            unit_price=package.male_price if _type == 'Jantan' else package.female_price
        )
        package.save()

        total = OrderPackage.objects.filter(
            order_id=_id).aggregate(order=Sum('total_price'))
        order = Order.objects.get(order_id=_id)
        order.total_order = total['order']
        order.save()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_package_update(request, _id, _package, _cat, _pack, _type, _add):
    categories = Category.objects.all()
    packages = Package.objects.filter(category=_cat).exclude(package_id__in=OrderPackage.objects.filter(
        order_id=_id).values_list('package_id', flat=True).exclude(package_id=_pack)) if _cat != '0' else None
    package = OrderPackage.objects.get(order_id=_id, id=_package)
    box_types = BoxType.objects.all()
    main_cuisines = MainCuisine.objects.filter(package=_pack)
    sub_cuisines = SubCuisine.objects.filter(package=_pack)
    side_cuisines1 = SideCuisine1.objects.filter(package=_pack)
    side_cuisines2 = SideCuisine2.objects.filter(package=_pack)
    side_cuisines3 = SideCuisine3.objects.filter(package=_pack)
    side_cuisines4 = SideCuisine4.objects.filter(package=_pack)
    side_cuisines5 = SideCuisine5.objects.filter(package=_pack)
    last_child = OrderChild.objects.filter(order_id=_id).last()
    selected_package = Package.objects.get(
        package_id=_pack) if _pack != '0' else None
    order = Order.objects.get(order_id=_id)
    orders = OrderPackage.objects.filter(order_id=_id)

    first = False
    prev_id = 0
    prev_cat = 0
    prev_pack = 0
    prev_type = 0

    first_package = OrderPackage.objects.filter(order_id=_id).first()
    if first_package.id == _package:
        first = True

    for index, i in enumerate(OrderPackage.objects.filter(order_id=_id)):
        if i.id == _package:
            n_package = index + 1

    for i in reversed(OrderPackage.objects.filter(order_id=_id)):
        if i.id < _package:
            prev_id = i.id
            prev_cat = i.category_id
            prev_pack = i.package_id
            prev_type = i.type
            break

    if request.POST:
        form = FormOrderPackage(request.POST, instance=package)
        if form.is_valid():
            package = form.save(commit=False)
            package.category_id = _cat
            package.package_id = _pack
            package.type = _type
            package.box_type_id = request.POST.get('box_type')
            package.main_cuisine = request.POST.get('main_cuisine')
            package.sub_cuisine = request.POST.get('sub_cuisine')
            package.side_cuisine1 = request.POST.get('side_cuisine1')
            package.side_cuisine2 = request.POST.get('side_cuisine2')
            package.side_cuisine3 = request.POST.get('side_cuisine3')
            package.side_cuisine4 = request.POST.get('side_cuisine4')
            package.side_cuisine5 = request.POST.get('side_cuisine5')
            package.unit_price = selected_package.male_price if _type == 'Jantan' else selected_package.female_price
            package.save()

            total = OrderPackage.objects.filter(
                order_id=_id).aggregate(order=Sum('total_price'))
            order.total_order = total['order']
            order.save()

            if _add == 1:
                return HttpResponseRedirect(reverse('order-package-add', args=[_id, '0', '0', '0', 0]))
            else:
                last_package = OrderPackage.objects.filter(order_id=_id).last()
                if last_package.id == _package:
                    return HttpResponseRedirect(reverse('order-confirm-update', args=[_id]))
                else:
                    for i in OrderPackage.objects.filter(order_id=_id):
                        if i.id > _package:
                            return HttpResponseRedirect(reverse('order-package-update', args=[_id, i.id, i.category_id, i.package_id, i.type, 0]))
    else:
        form = FormOrderPackage(instance=package)

    msg = form.errors

    context = {
        'form': form,
        'data': package,
        'first_package': first,
        'n_package': n_package,
        'orders': orders,
        'prev_id': prev_id,
        'prev_cat': prev_cat,
        'prev_pack': prev_pack,
        'prev_type': prev_type,
        'last_child': last_child,
        'cat': _cat,
        'pack': _pack,
        'type': _type,
        'crud': 'update',
        'categories': categories,
        'packages': packages,
        'box_types': box_types,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'selected_package': selected_package,
        'order_id': _id,
        'msg': msg,
    }
    return render(request, 'home/order_package_update.html', context)


def order_package_cs_update(request, _id, _cat, _pack, _type):
    package = OrderPackage.objects.get(order_id=_id, package=_pack)
    order = Order.objects.get(order_id=_id)
    selected_package = Package.objects.get(package_id=_pack)

    if request.POST:
        package.category_id = _cat
        package.package_id = _pack
        package.type = _type
        package.quantity = int(request.POST.get('quantity'))
        package.box_type_id = request.POST.get('box_type')
        package.main_cuisine = request.POST.get('main_cuisine')
        package.sub_cuisine = request.POST.get('sub_cuisine')
        package.side_cuisine1 = request.POST.get('side_cuisine1')
        package.side_cuisine2 = request.POST.get('side_cuisine2')
        package.side_cuisine3 = request.POST.get('side_cuisine3')
        package.side_cuisine4 = request.POST.get('side_cuisine4')
        package.side_cuisine5 = request.POST.get('side_cuisine5')
        package.unit_price = selected_package.male_price if _type == 'Jantan' else selected_package.female_price
        package.save()

        total = OrderPackage.objects.filter(
            order_id=_id).aggregate(order=Sum('total_price'))
        order.total_order = total['order']
        order.save()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_package_delete(request, _id, _package):
    package = OrderPackage.objects.get(order_id=_id, id=_package)
    package.delete()

    total = OrderPackage.objects.filter(
        order_id=_id).aggregate(order=Sum('total_price'))
    order = Order.objects.get(order_id=_id)
    order.total_order = total['order']
    order.save()

    first = OrderPackage.objects.filter(order_id=_id).first()

    return HttpResponseRedirect(reverse('order-package-update', args=[_id, first.id, first.category_id, first.package_id, first.type, 0]))


def order_package_cs_delete(request, _id, _pack):
    package = OrderPackage.objects.get(order_id=_id, id=_pack)
    package.delete()

    total = OrderPackage.objects.filter(
        order_id=_id).aggregate(order=Sum('total_price'))
    order = Order.objects.get(order_id=_id)
    order.total_order = total['order']
    order.save()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_confirm_update(request, _id):
    order = Order.objects.get(order_id=_id)
    last_package = OrderPackage.objects.filter(order_id=_id).last()

    if request.POST:
        form = FormOrderConfirmUpdate(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.use_photo = request.POST.get('use_photo')
            order.witnessed = request.POST.get('witnessed')
            order.info_source = request.POST.get('info_source')
            order.save()

            return HttpResponseRedirect(reverse('order-confirm', args=[_id]))
    else:
        form = FormOrderConfirmUpdate(instance=order)

    context = {
        'form': form,
        'data': order,
        'last_package': last_package,
        'crud': 'update',
    }
    return render(request, 'home/order_confirm_update.html', context)


def order_confirm(request, _id):
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)

    context = {
        'data': order,
        'child': child,
        'package': package,
        'crud': 'view',
    }
    return render(request, 'home/order_confirm.html', context)


def order_submit(request, _id):
    order = Order.objects.get(order_id=_id)
    order.order_status = 'DRAFT'
    order.save()

    link_form = AreaSales.objects.get(area_id=order.regional_id).form

    return render(request, 'home/order_thankyou.html', {'link_form': link_form})


def order_cancel(request, _id):
    order = Order.objects.get(order_id=_id)
    order.order_status = 'BATAL'
    order.save()

    return HttpResponseRedirect(reverse('order-index'))


def order_confirmed(request, _id):
    order = Order.objects.get(order_id=_id)
    order.order_status = 'CONFIRMED'
    order.cs = get_current_user().username
    order.save()

    return HttpResponseRedirect(reverse('order-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='FORM')
def form_index(request):
    area_sales = AreaSales.objects.all()

    context = {
        'data': area_sales,
        'segment': 'form',
        'group_segment': 'transaction',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='FORM') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/form_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_index(request):
    orders = Order.objects.filter(regional_id__in=AreaUser.objects.filter(user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-order_id', 'regional').exclude(order_status__in=[
        'PENDING', 'BATAL']) if request.user.position_id == 'CS' else Order.objects.filter(regional_id__in=AreaUser.objects.filter(user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-order_id', 'regional').exclude(order_status__in=['PENDING'])

    context = {
        'data': orders,
        'segment': 'order',
        'group_segment': 'transaction',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='ORDER') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/order_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_view(request, _id, _cat, _pack, _type, _crud):
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)
    form = FormOrderView(instance=order)
    formChild = FormOrderChild()
    category = Category.objects.all()
    packages = Package.objects.filter(category=_cat).exclude(package_id__in=OrderPackage.objects.filter(
        order_id=_id).values_list('package_id', flat=True)) if _cat != '0' else None
    packages_upd = Package.objects.filter(category=_cat).exclude(package_id__in=OrderPackage.objects.filter(
        order_id=_id).values_list('package_id', flat=True).exclude(package_id=_pack)) if _cat != '0' else None
    box = BoxType.objects.all()
    main_cuisines = MainCuisine.objects.filter(package=_pack)
    sub_cuisines = SubCuisine.objects.filter(package=_pack)
    side_cuisines1 = SideCuisine1.objects.filter(package=_pack)
    side_cuisines2 = SideCuisine2.objects.filter(package=_pack)
    side_cuisines3 = SideCuisine3.objects.filter(package=_pack)
    side_cuisines4 = SideCuisine4.objects.filter(package=_pack)
    side_cuisines5 = SideCuisine5.objects.filter(package=_pack)
    selected_package = Package.objects.get(
        package_id=_pack) if _pack != '0' else None
    upd_package = OrderPackage.objects.get(order_id=_id, id=_crud) if _crud not in [
        '0', 'add'] else None

    msg = form.errors
    context = {
        'form': form,
        'formChild': formChild,
        'data': order,
        'child': child,
        'package': package,
        'category': category,
        'packages': packages,
        'packages_upd': packages_upd,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'selected_package': selected_package,
        'upd_package': upd_package,
        'box': box,
        'cat': _cat,
        'pack': _pack,
        'type': _type,
        'crud_det': _crud,
        'msg': msg,
        'segment': 'order',
        'group_segment': 'transaction',
        'crud': 'view',
        'status': order.order_status,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='ORDER') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/order_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_cs_update(request, _id, _cat, _pack, _type):
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)

    if request.POST:
        form = FormOrderCSUpdate(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.customer_name = request.POST.get('customer_name')
            order.customer_phone = request.POST.get('customer_phone')
            order.customer_phone2 = request.POST.get('customer_phone2')
            order.customer_email = request.POST.get('customer_email')
            order.customer_address = request.POST.get('customer_address')
            order.customer_city = request.POST.get('customer_city')
            order.customer_district = request.POST.get('customer_district')
            order.customer_province = request.POST.get('customer_province')
            order.delivery_date = request.POST.get('delivery_date')
            order.time_arrival = request.POST.get('time_arrival')
            order.use_photo = request.POST.get('use_photo')
            order.witnessed = request.POST.get('witnessed')
            order.info_source = request.POST.get('info_source')
            order.order_note = request.POST.get('order_note')
            order.discount = int(request.POST.get('discount'))
            order.save()

        return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))
    else:
        form = FormOrderCSUpdate(instance=order)

    msg = form.errors

    context = {
        'form': form,
        'data': order,
        'child': child,
        'package': package,
        'cat': _cat,
        'pack': _pack,
        'type': _type,
        'crud_det': '0',
        'msg': msg,
        'segment': 'order',
        'group_segment': 'transaction',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='ORDER') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/order_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CASH-IN')
def cashin_index(request):
    cash_in = CashIn.objects.filter(order_id__regional_id__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-cashin_id')

    context = {
        'data': cash_in,
        'segment': 'cash-in',
        'group_segment': 'accounting',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CASH-IN') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cashin_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CASH-IN')
def cashin_add(request):
    orders = Order.objects.filter(order_status__in=['DP', 'CONFIRMED'], regional_id__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-order_id')

    if request.POST:
        form = FormCashIn(request.POST, request.FILES)
        if form.is_valid():
            cash_in = form.save(commit=False)
            cash_in.order_id = request.POST.get('order')
            cash_in.cashin_type = request.POST.get('cashin_type')
            cash_in.save()

            if not settings.DEBUG:
                cash_in = CashIn.objects.get(cashin_id=cash_in.cashin_id)
                my_file = cash_in.evidence
                filename = '../../www/aqiqahon/apps/media/' + my_file.name
                with open(filename, 'wb+') as temp_file:
                    for chunk in my_file.chunks():
                        temp_file.write(chunk)

            selected_order = Order.objects.get(
                order_id=request.POST.get('order'))
            if cash_in.cashin_amount == selected_order.pending_payment:
                selected_order.order_status = 'LUNAS'
            else:
                selected_order.order_status = 'DP'

            selected_order.down_payment += cash_in.cashin_amount
            selected_order.save()

            return HttpResponseRedirect(reverse('cashin-index'))
    else:
        form = FormCashIn()

    msg = form.errors
    context = {
        'form': form,
        'orders': orders,
        'segment': 'cash-in',
        'group_segment': 'accounting',
        'crud': 'add',
        'msg': msg,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CASH-IN') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cashin_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CASH-IN')
def cashin_view(request, _id):
    cash_in = CashIn.objects.get(cashin_id=_id)
    form = FormCashInView(instance=cash_in)
    orders = Order.objects.filter(order_status__in=['DP', 'CONFIRMED'], regional_id__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-order_id')

    context = {
        'data': cash_in,
        'form': form,
        'orders': orders,
        'segment': 'cash-in',
        'group_segment': 'accounting',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CASH-IN') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cashin_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CASH-IN')
def cashin_update(request, _id):
    cash_in = CashIn.objects.get(cashin_id=_id)

    if request.POST:
        form = FormCashInUpdate(request.POST, request.FILES, instance=cash_in)
        if form.is_valid():
            update = form.save(commit=False)
            update.order_id = request.POST.get('order')
            update.cashin_type = request.POST.get('cashin_type')
            update.save()

            selected_order = Order.objects.get(
                order_id=request.POST.get('order'))
            if cash_in.cashin_amount == selected_order.pending_payment:
                selected_order.order_status = 'LUNAS'
            else:
                selected_order.order_status = 'DP'

            selected_order.down_payment += cash_in.cashin_amount
            selected_order.save()

            return HttpResponseRedirect(reverse('cashin-index'))
    else:
        form = FormCashInUpdate(instance=cash_in)

    msg = form.errors
    context = {
        'form': form,
        'data': cash_in,
        'segment': 'cash-in',
        'group_segment': 'accounting',
        'crud': 'update',
        'msg': msg,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CASH-IN') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cashin_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_invoice(request, _id):
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)
    region = AreaSales.objects.get(area_id=order.regional_id)

    hari = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Ahad']
    bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
             'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    order_id = _id.replace('/', '-')
    customer_name = order.customer_name.replace(' ', '_')
    customer_name = customer_name.replace('/', '-')

    styles = getSampleStyleSheet()
    normalStyle = styles['Normal']
    normalStyle.fontSize = 8

    filename = 'INVOICE_' + customer_name + '_' + order_id + '.pdf'
    pdf_file = canvas.Canvas(filename)

    # Add logo in the top left corner
    logo_path = '../../www/aqiqahon/apps/static/img/logo.png'
    pdf_file.drawImage(logo_path, 35, 745, width=70, height=61)

    title = "INVOICE"
    title_width = pdf_file.stringWidth(
        title, "Helvetica-Bold", 12)  # Set font to bold
    page_width, _ = A4
    pdf_file.setFont("Helvetica-Bold", 12)  # Set font to bold
    # Calculate the x position for the title to be in the top right corner
    title_x = page_width - title_width - 35  # 25 is a margin from the right edge
    pdf_file.drawString(title_x, 795, title)

    # Add address below logo
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, 725, 'Regional :')

    # Add regional info beside regional title with bold font
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(74, 725, order.regional.area_name)
    pdf_file.setFont("Helvetica", 8)
    address = 'Kantor Pusat : Jl. KH. Maulana Hasanudin No.88'
    pdf_file.drawString(35, 713, address)
    city = 'Poris, Tangerang, 15122'
    pdf_file.drawString(35, 701, city)
    phone = 'Telp/Whatsapp : 0812 9658 9090'
    pdf_file.drawString(35, 689, phone)
    web = 'www.sahabataqiqah.co.id'
    pdf_file.drawString(35, 677, web)

    # Add title start from the middle of page
    pdf_file.setFont("Helvetica-Bold", 8)
    title = "No. Referensi"
    page_width, _ = A4
    title_x = (page_width / 2) - 35
    pdf_file.drawString(title_x, 770, title)
    # Add order_id below title
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(title_x, 758, order.order_id)
    # Add order date below order_id with higher space
    pdf_file.setFont("Helvetica-Bold", 8)
    title = "Tanggal Invoice"
    pdf_file.drawString(title_x, 740, title)

    months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
              'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Ahad']

    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(title_x, 728, days[order.order_date.weekday()] + order.order_date.strftime(
        ', %d ') + months[order.order_date.month - 1] + order.order_date.strftime(' %Y'))
    # Add delivery date below order date with higher space
    pdf_file.setFont("Helvetica-Bold", 8)
    title = "Tanggal Pengiriman"
    pdf_file.drawString(title_x, 710, title)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(title_x, 698, days[order.delivery_date.weekday()] + order.delivery_date.strftime(
        ', %d ') + months[order.delivery_date.month - 1] + order.delivery_date.strftime(' %Y'))
    # Add customer info below delivery date with higher space
    pdf_file.setFont("Helvetica-Bold", 8)
    title = "Nama Pemesan Aqiqah"
    pdf_file.drawString(title_x, 680, title)
    pdf_file.drawString(title_x, 668, order.customer_name)
    # Add customer phone below customer name
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(title_x, 656, order.customer_phone + ' / ' +
                        order.customer_phone2 if order.customer_phone2 else order.customer_phone)

    # Add customer address below customer phone
    y = 641
    address = order.customer_address.split('\n')
    for i, line in enumerate(address):
        address_width = pdf_file.stringWidth(address[i], "Helvetica", 8)
        rows = int(address_width) // 270
        for j in range(0, rows):
            y -= 13

    for line in address:
        address_paragraph = Paragraph(line, normalStyle)
        address_paragraph.wrapOn(pdf_file, 270, 0)
        address_paragraph.drawOn(pdf_file, title_x, y)
        y -= 10

    # Add customer district below customer address
    y += 1
    pdf_file.drawString(
        title_x, y, order.customer_district + ', ' + order.customer_city)
    # Add customer province below customer district
    y -= 13
    pdf_file.drawString(title_x, y, order.customer_province)

    y -= 30
    # Add table for order detail
    pdf_file.rect(35, y, 160, 15, stroke=True)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(40, y + 5, 'Produk')
    pdf_file.rect(195, y, 180, 15, stroke=True)
    pdf_file.drawString(200, y + 5, 'Deskripsi')
    pdf_file.rect(375, y, 30, 15, stroke=True)
    # Calculate the width of the string 'Qty'
    qty_width = pdf_file.stringWidth('Qty', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 375 + (30 - qty_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Qty')
    pdf_file.rect(405, y, 85, 15, stroke=True)
    # Calculate the width of the string 'Harga Satuan (Rp)'
    price_width = pdf_file.stringWidth(
        'Harga Satuan (Rp)', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 405 + (85 - price_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Harga Satuan (Rp)')
    pdf_file.rect(490, y, 65, 15, stroke=True)
    # Calculate the width of the string 'Jumlah (Rp)'
    total_width = pdf_file.stringWidth('Jumlah (Rp)', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 490 + (65 - total_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Jumlah (Rp)')

    y += 15
    total = 0
    for i in range(1, package.count() + 1):
        y -= 30
        pdf_file.rect(35, y - 15, 160, 30, stroke=True)
        pdf_file.setFont("Helvetica", 8)
        qty = ' - ' + str(package[i - 1].package.quantity) + \
            ' - ' if package[i - 1].package.quantity > 0 else ''
        pdf_file.drawString(
            40, y + 5, package[i - 1].category.category_name + ' - ' + package[i - 1].package.package_name + qty)
        if package[i - 1].package.quantity > 0:
            pdf_file.drawString(40, y - 5, 'Hewan ' + package[i - 1].type)
        pdf_file.rect(195, y - 15, 180, 30, stroke=True)

        cuisines = [package[i - 1].main_cuisine, package[i - 1].sub_cuisine,
                    package[i - 1].side_cuisine1, package[i - 1].side_cuisine2]
        row = []
        str_cuisine = ''

        for cuisine in cuisines:
            if cuisine:
                row.append(cuisine)

        for j in range(0, len(row)):
            str_cuisine += row[j] + ' - '

        pdf_file.drawString(200, y + 5, str_cuisine)

        cuisines = [package[i - 1].side_cuisine3,
                    package[i - 1].side_cuisine4, package[i - 1].side_cuisine5]
        row = []
        str_cuisine = ''
        str_box = ''

        for cuisine in cuisines:
            if cuisine:
                row.append(cuisine)

        for j in range(0, len(row)):
            str_cuisine += row[j]
            if j < len(row) - 1:
                str_cuisine += ' - '

        if str_cuisine != '' and package[i - 1].package.box > 0:
            str_box = ' - '
        str_box += str(package[i - 1].package.box) + ' Box (' + package[i -
                                                                        1].box_type.box_type_name + ')' if package[i - 1].package.box > 0 else ''

        pdf_file.drawString(200, y - 5, str_cuisine + str_box)
        pdf_file.rect(375, y - 15, 30, 30, stroke=True)
        pdf_file.setFont("Helvetica", 8)
        # Calculate the width of the string 'quantity'
        quantity_width = pdf_file.stringWidth(
            str(package[i - 1].quantity), "Helvetica", 8)
        # Calculate the center position of the rectangle
        center_x = 375 + (30 - quantity_width) / 2
        pdf_file.drawString(
            center_x, y + 5, str(package[i - 1].quantity))
        pdf_file.rect(405, y - 15, 85, 30, stroke=True)
        pdf_file.drawString(
            410, y + 5, "{:,}".format(package[i - 1].unit_price))
        pdf_file.rect(490, y - 15, 65, 30, stroke=True)
        total_price = package[i - 1].unit_price * package[i - 1].quantity
        total += total_price
        total_price_str = "{:,}".format(total_price)
        total_price_width = pdf_file.stringWidth(
            total_price_str, "Helvetica", 8)
        pdf_file.drawString(490 + 65 - total_price_width -
                            5, y + 5, total_price_str)

    y -= 30
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Sub Total'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(total)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Diskon'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.discount)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'DP'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.down_payment)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Jumlah Tertagih'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.pending_payment)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y2 = y
    y -= 30
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(35, y, 'Syarat & Ketentuan')
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, y - 15, 'Pengiriman')
    pdf_file.drawString(95, y - 15, ':')
    pdf_file.drawString(
        105, y - 15, hari[int(order.delivery_date.strftime('%w')) - 1] + ', ' + order.delivery_date.strftime('%-d ') + bulan[int(order.delivery_date.strftime('%-m')) - 1] + order.delivery_date.strftime(' %Y'))
    pdf_file.drawString(35, y - 27, 'Jam Berangkat')
    pdf_file.drawString(95, y - 27, ':')
    time_arrival_minus_one_hour = datetime.datetime.strptime(
        order.time_arrival, '%H:%M') - datetime.timedelta(hours=1)
    pdf_file.drawString(
        105, y - 27, time_arrival_minus_one_hour.strftime('%H:%M'))
    pdf_file.drawString(35, y - 39, 'Jam Tiba')
    pdf_file.drawString(95, y - 39, ':')
    pdf_file.drawString(105, y - 39, order.time_arrival)
    pdf_file.drawString(35, y - 51, 'Catatan')
    pdf_file.drawString(95, y - 51, ':')

    notes = order.order_note.split('\n') if order.order_note else ''
    for i, line in enumerate(notes):
        note_width = pdf_file.stringWidth(notes[i], "Helvetica", 8)
        rows = int(note_width) // 200
        for j in range(0, rows):
            y -= 13

    for line in notes:
        notes_paragraph = Paragraph(line, normalStyle)
        notes_paragraph.wrapOn(pdf_file, 200, 100)
        notes_paragraph.drawOn(pdf_file, 105, y - 55)
        y -= 10

    y2 -= 30
    pdf_file.setFont("Helvetica-Bold", 8)
    page_width = 595.27
    text = 'Anak yang di aqiqah'
    text_x = (page_width / 2) + 35
    pdf_file.drawString(text_x, y2, text)
    pdf_file.setFont("Helvetica", 8)
    y2 -= 15
    for i in range(1, child.count() + 1):
        pdf_file.drawString(text_x, y2, str(i) + '.')
        pdf_file.drawString(text_x + 10, y2, child[i - 1].child_name)
        y2 -= 12
        sex = 'Laki-laki' if child[i - 1].child_sex == '1' else 'Perempuan'
        pdf_file.drawString(
            text_x + 10, y2, '(' + child[i - 1].child_birth.strftime('%-d') + ' ' + bulan[int(child[i - 1].child_birth.strftime('%-m')) - 1] + ' ' + child[i - 1].child_birth.strftime('%Y') + ') | ' + sex)
        y2 -= 12

    y2 -= 15
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(text_x, y2, 'Anak dari')
    pdf_file.setFont("Helvetica", 8)
    y2 -= 15
    pdf_file.drawString(
        text_x, y2, child[0].child_father)
    y2 -= 12
    pdf_file.drawString(text_x, y2, child[0].child_mother)

    y -= 81
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(
        35, y, 'Sertifikat dan Kartu Ucapan pakai foto atau tidak?')
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(
        35, y - 12, 'YA' if order.use_photo == 1 else 'TIDAK')

    y -= 27
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(35, y, 'Penyembelihan disaksikan?')
    y -= 12
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, y, 'YA' if order.witnessed == 1 else 'TIDAK')

    y -= 15
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(35, y, 'Sumber Informasi?')
    y -= 12
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, y, order.info_source)

    y -= 30
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(35, y, '* DP minimal 30%')

    y -= 30
    pdf_file.drawString(
        35, y, 'Pembayaran dapat dilakukan melalui transfer ke rekening :')
    y -= 15
    bank = region.bank_account.split('\n')
    for line in bank:
        bank_paragraph = Paragraph(line, normalStyle)
        bank_paragraph.wrapOn(pdf_file, 200, 100)
        bank_paragraph.drawOn(pdf_file, 35, y)
        y -= 10

    y2 -= 30
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(text_x, y2, 'Tangerang, ' + order.order_date.strftime('%-d ') +
                        bulan[int(order.order_date.strftime('%-m')) - 1] + order.order_date.strftime(' %Y'))
    y2 -= 55
    gm = User.objects.get(position='GM')
    sign_path = gm.signature.path
    pdf_file.drawImage(sign_path, text_x, y2, width=100, height=50)

    y2 -= 15
    pdf_file.drawString(text_x, y2, gm.username)
    y2 -= 12
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(text_x, y2, gm.position.position_name)

    pdf_file.save()

    return FileResponse(open(filename, 'rb'), content_type='application/pdf')


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_bap(request, _id):
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)
    region = AreaSales.objects.get(area_id=order.regional_id)

    hari = ['Ahad', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu']
    bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
             'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    order_id = _id.replace('/', '-')
    customer_name = order.customer_name.replace(' ', '_')
    customer_name = customer_name.replace('/', '-')

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 8
    bold_style = styles['Normal']
    bold_style.fontSize = 8
    bold_style.fontName = 'Helvetica-Bold'

    filename = 'SURAT_JALAN_' + customer_name + '_' + order_id + '.pdf'
    pdf_file = canvas.Canvas(filename)

    # Add logo in the top center
    logo_path = '../../www/aqiqahon/apps/static/img/logo.png'
    pdf_file.drawImage(logo_path, 260, 745, width=70, height=61)

    y = 725
    title = "SURAT JALAN SAHABAT AQIQAH"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 12)
    page_width, _ = A4
    title_x = (page_width / 2) - (title_width / 2)
    pdf_file.setFont("Helvetica-Bold", 12)
    pdf_file.drawString(title_x, y, title)

    y -= 50
    y2 = y
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, y, 'Nama Shahibul Aqiqah (1)')
    pdf_file.drawString(135, y, ':')
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(145, y, child[0].child_name)
    y -= 12
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, y, 'Nama Pemesan')
    pdf_file.drawString(135, y, ':')
    pdf_file.drawString(145, y, order.customer_name)
    y -= 12
    pdf_file.drawString(35, y, 'No. Telepon')
    pdf_file.drawString(135, y, ':')
    pdf_file.drawString(145, y, order.customer_phone +
                        ' / ' + str(order.customer_phone2) if order.customer_phone2 else order.customer_phone)
    y -= 12
    pdf_file.drawString(35, y, 'Alamat')
    pdf_file.drawString(135, y, ':')

    y += 1
    address = order.customer_address.split('\n')
    for i, line in enumerate(address):
        address_width = pdf_file.stringWidth(
            address[i], "Helvetica", 8)
        rows = int(address_width) // 250
        for j in range(0, rows):
            y -= 13

    for line in address:
        address_paragraph = Paragraph(line, bold_style)
        address_paragraph.wrapOn(pdf_file, 250, 100)
        address_paragraph.drawOn(pdf_file, 145, y - 4)
        y -= 10

    y -= 2
    pdf_file.drawString(35, y, 'Tanggal Pengiriman')
    pdf_file.drawString(135, y, ':')
    pdf_file.drawString(145, y, order.delivery_date.strftime(
        '%-d ') + bulan[order.delivery_date.month - 1] + order.delivery_date.strftime(' %Y'))
    y -= 12
    pdf_file.drawString(35, y, 'Jam Tiba')
    pdf_file.drawString(135, y, ':')
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(145, y, order.time_arrival)

    # Add table right beside the customer info
    y2 -= 2
    pdf_file.rect(405, y2, 150, 15, stroke=True)
    pdf_file.setFont("Helvetica-Bold", 8)
    text = 'No. Order'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 150
    text_x = 405 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y2 + 5, text)
    pdf_file.rect(405, y2 - 15, 150, 15, stroke=True)
    pdf_file.setFont("Helvetica", 8)
    text = order.order_id
    text_width = pdf_file.stringWidth(text, "Helvetica", 8)
    text_x = 405 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y2 - 10, text)

    y -= 30
    # Add table for order detail
    pdf_file.rect(35, y, 160, 15, stroke=True)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(40, y + 5, 'Produk')
    pdf_file.rect(195, y, 180, 15, stroke=True)
    pdf_file.drawString(200, y + 5, 'Deskripsi')
    pdf_file.rect(375, y, 30, 15, stroke=True)
    # Calculate the width of the string 'Qty'
    qty_width = pdf_file.stringWidth('Qty', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 375 + (30 - qty_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Qty')
    pdf_file.rect(405, y, 85, 15, stroke=True)
    # Calculate the width of the string 'Harga Satuan (Rp)'
    price_width = pdf_file.stringWidth(
        'Harga Satuan (Rp)', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 405 + (85 - price_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Harga Satuan (Rp)')
    pdf_file.rect(490, y, 65, 15, stroke=True)
    # Calculate the width of the string 'Jumlah (Rp)'
    total_width = pdf_file.stringWidth('Jumlah (Rp)', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 490 + (65 - total_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Jumlah (Rp)')

    y += 15
    total = 0
    for i in range(1, package.count() + 1):
        y -= 30
        pdf_file.rect(35, y - 15, 160, 30, stroke=True)
        pdf_file.setFont("Helvetica", 8)
        qty = ' - ' + str(package[i - 1].package.quantity) + \
            ' - ' if package[i - 1].package.quantity > 0 else ''
        pdf_file.drawString(
            40, y + 5, package[i - 1].category.category_name + ' - ' + package[i - 1].package.package_name + qty)
        if package[i - 1].package.quantity > 0:
            pdf_file.drawString(40, y - 5, 'Hewan ' + package[i - 1].type)
        pdf_file.rect(195, y - 15, 180, 30, stroke=True)

        cuisines = [package[i - 1].main_cuisine, package[i - 1].sub_cuisine,
                    package[i - 1].side_cuisine1, package[i - 1].side_cuisine2]
        row = []
        str_cuisine = ''

        for cuisine in cuisines:
            if cuisine:
                row.append(cuisine)

        for j in range(0, len(row)):
            str_cuisine += row[j] + ' - '

        pdf_file.drawString(200, y + 5, str_cuisine)

        cuisines = [package[i - 1].side_cuisine3,
                    package[i - 1].side_cuisine4, package[i - 1].side_cuisine5]
        row = []
        str_cuisine = ''
        str_box = ''

        for cuisine in cuisines:
            if cuisine:
                row.append(cuisine)

        for j in range(0, len(row)):
            str_cuisine += row[j]
            if j < len(row) - 1:
                str_cuisine += ' - '

        if str_cuisine != '' and package[i - 1].package.box > 0:
            str_box = ' - '
        str_box += str(package[i - 1].package.box) + ' Box (' + package[i -
                                                                        1].box_type.box_type_name + ')' if package[i - 1].package.box > 0 else ''

        pdf_file.drawString(200, y - 5, str_cuisine + str_box)
        pdf_file.rect(375, y - 15, 30, 30, stroke=True)
        pdf_file.setFont("Helvetica", 8)
        # Calculate the width of the string 'quantity'
        quantity_width = pdf_file.stringWidth(
            str(package[i - 1].quantity), "Helvetica", 8)
        # Calculate the center position of the rectangle
        center_x = 375 + (30 - quantity_width) / 2
        pdf_file.drawString(
            center_x, y + 5, str(package[i - 1].quantity))
        pdf_file.rect(405, y - 15, 85, 30, stroke=True)
        pdf_file.drawString(
            410, y + 5, "{:,}".format(package[i - 1].unit_price))
        pdf_file.rect(490, y - 15, 65, 30, stroke=True)
        total_price = package[i - 1].unit_price * package[i - 1].quantity
        total += total_price
        total_price_str = "{:,}".format(total_price)
        total_price_width = pdf_file.stringWidth(
            total_price_str, "Helvetica", 8)
        pdf_file.drawString(490 + 65 - total_price_width -
                            5, y + 5, total_price_str)

    y -= 30
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Sub Total'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(total)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Diskon'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.discount)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'DP'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.down_payment)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Jumlah Tertagih'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.pending_payment)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 60
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.rect(35, y, 100, 15, stroke=False)
    text = 'GA'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 100
    text_x = 35 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y + 5, text)
    pdf_file.rect(135, y, 100, 15, stroke=False)
    text = 'Kurir'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 100
    text_x = 135 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y + 5, text)
    pdf_file.rect(35, y - 50, 100, 15, stroke=False)
    text = '( __________________ )'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 100
    text_x = 35 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y - 50, text)
    pdf_file.rect(135, y - 50, 100, 15, stroke=False)
    text = '( __________________ )'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 100
    text_x = 135 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y - 50, text)

    pdf_file.rect(250, y, 210, 15, stroke=True)
    pdf_file.setFont("Helvetica-Bold", 8)
    text = 'Dengan ini saya menyetujui :'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 210
    text_x = 250 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y + 5, text)
    pdf_file.rect(460, y, 45, 15, stroke=True)
    text = 'Checklist'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 45
    text_x = 460 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y + 5, text)
    pdf_file.rect(505, y, 50, 15, stroke=True)
    text = 'Penerima'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 50
    text_x = 505 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y + 5, text)

    y -= 15
    pdf_file.rect(250, y, 210, 15, stroke=True)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(
        255, y + 5, 'Kelengkapan isi box dari paketan sudah sesuai orderan')
    pdf_file.rect(460, y, 45, 15, stroke=True)
    pdf_file.rect(505, y - 40, 50, 55, stroke=True)
    y -= 15
    pdf_file.rect(250, y - 25, 210, 40, stroke=True)
    pdf_file.drawString(
        255, y + 5, 'Ketahanan makanan 3-4 jam setelah makanan tiba di')
    pdf_file.drawString(
        255, y - 5, 'lokasi (bersedia mengirimkan sampel basi setelah 3 jam')
    pdf_file.drawString(
        255, y - 15, 'via gosend *biaya ditanggung Sahabat Aqiqah)')
    pdf_file.rect(460, y - 25, 45, 40, stroke=True)

    pdf_file.save()

    return FileResponse(open(filename, 'rb'), content_type='application/pdf')


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_checklist(request, _id):
    order = Order.objects.get(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)

    bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
             'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    order_id = _id.replace('/', '-')
    customer_name = order.customer_name.replace(' ', '_')
    customer_name = customer_name.replace('/', '-')

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 8

    filename = 'CHECKLIST_' + customer_name + '_' + order_id + '.pdf'
    pdf_file = canvas.Canvas(filename)

    # Add logo in the top left corner
    logo_path = '../../www/aqiqahon/apps/static/img/logo.png'
    pdf_file.drawImage(logo_path, 35, 745, width=70, height=61)

    title = "CHECKLIST FORM"
    title_width = pdf_file.stringWidth(
        title, "Helvetica-Bold", 12)  # Set font to bold
    page_width, _ = A4
    pdf_file.setFont("Helvetica-Bold", 12)  # Set font to bold
    # Calculate the x position for the title to be in the top right corner
    title_x = page_width - title_width - 35  # 25 is a margin from the right edge
    pdf_file.drawString(title_x, 795, title)

    # Add address below logo
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, 725, 'Regional :')

    # Add regional info beside regional title with bold font
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(74, 725, order.regional.area_name)
    pdf_file.setFont("Helvetica", 8)
    address = 'Kantor Pusat : Jl. KH. Maulana Hasanudin No.88'
    pdf_file.drawString(35, 713, address)
    city = 'Poris, Tangerang, 15122'
    pdf_file.drawString(35, 701, city)
    phone = 'Telp/Whatsapp : 0812 9658 9090'
    pdf_file.drawString(35, 689, phone)
    web = 'www.sahabataqiqah.co.id'
    pdf_file.drawString(35, 677, web)

    y = 745
    # Add title start from the middle of page
    title = "No. Invoice"
    page_width, _ = A4
    title_x = (page_width / 2) + 35
    pdf_file.drawString(title_x, y, title)
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(title_x + 90, y, order.order_id)
    y -= 12
    pdf_file.drawString(title_x, y, "Nama Pemesan")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(title_x + 90, y, order.customer_name)
    y -= 12
    pdf_file.drawString(title_x, y, "Tanggal Delivery")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(title_x + 90, y, order.delivery_date.strftime(
        '%-d ') + bulan[order.delivery_date.month - 1] + order.delivery_date.strftime(' %Y'))
    y -= 12
    pdf_file.drawString(title_x, y, "Checker")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(title_x + 90, y, '______________________')
    y -= 12
    pdf_file.drawString(title_x, y, "Driver")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(title_x + 90, y, '______________________')
    y -= 12
    pdf_file.drawString(title_x, y, "Menu")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(
        title_x + 90, y, package[0].category.category_name + ' - ' + package[0].package.package_name)
    y -= 12
    pdf_file.drawString(title_x, y, "Jumlah Box")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(
        title_x + 90, y, str(package[0].package.box) + ' Box (' + package[0].box_type.box_type_name + ')')

    y -= 30
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.line(35, y, page_width - 35, y)
    y -= 15
    y2 = y
    pdf_file.drawString(40, y, 'DI ISI OLEH DRIVER')
    pdf_file.drawString(140, y, 'DI ISI OLEH CHECKER')
    y -= 10
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(140, y + 5, 'Nasi Kebuli / Nasi Kuning / Nasi Putih')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    if package[0].main_cuisine:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].main_cuisine)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].sub_cuisine:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].sub_cuisine)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].side_cuisine1:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].side_cuisine1)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].side_cuisine2:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].side_cuisine2)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].side_cuisine3:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].side_cuisine3)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].side_cuisine4:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].side_cuisine4)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].side_cuisine5:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].side_cuisine5)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Kerupuk')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Acar')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Mr. Jussie / Air Mineral / Kosong')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Telor Pindang / Telor Balado')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Sertifikat')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Kantong Plastik / Tas Serut')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Boneka Panda / Boneka Domba / Mug')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'BAP & Kwitansi')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Sisa Masakan Olahan Daging ......')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(
        140, y + 5, 'Sisa Masakan Olahan Tulangan & Jeroan ......')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)

    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(title_x, y2, 'CATATAN LAINNYA')
    y2 -= 30
    pdf_file.rect(title_x, y2, 80, 15, stroke=True)
    y2 -= 25
    pdf_file.rect(title_x, y2, 80, 15, stroke=True)
    y2 -= 25
    pdf_file.rect(title_x, y2, 80, 15, stroke=True)

    y -= 60
    title = "TTD CHECKER"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    pdf_file.rect(35, y, (page_width - 2*35) / 2, 15, stroke=False)
    pdf_file.drawString(35 + (((page_width / 2 - 35) -
                        title_width) / 2), y + 5, title)
    string = '( __________________ )'
    string_width = pdf_file.stringWidth(string, "Helvetica-Bold", 8)
    pdf_file.drawString(35 + (((page_width / 2 - 35) -
                        string_width) / 2), y - 80, string)
    title = "TTD DRIVER"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    pdf_file.rect(35 + (page_width - 2*35) / 2, y,
                  (page_width - 2*35) / 2, 15, stroke=False)
    pdf_file.drawString(35 + (page_width - 2*35) / 2 +
                        ((page_width - 2*35) / 2 - title_width) / 2, y + 5, title)
    pdf_file.drawString(35 + (page_width - 2*35) / 2 +
                        ((page_width - 2*35) / 2 - string_width) / 2, y - 80, string)

    pdf_file.save()

    return FileResponse(open(filename, 'rb'), content_type='application/pdf')
