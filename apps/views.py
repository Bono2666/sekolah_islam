from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import connection, IntegrityError
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.forms.models import modelformset_factory
from django.db import transaction
from django.core.paginator import Paginator
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
from xhtml2pdf import pisa
from io import BytesIO
from django.http import FileResponse
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4
from django.db.models import Count
from PyPDF2 import PdfMerger
from django.conf import settings
# from xhtml2pdf import pisa
from django.template.loader import get_template
from django.utils.text import Truncator
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from crum import get_current_user
import os
import re
import uuid
import zipfile
import csv
import json
import xml.etree.ElementTree as ET
# from apps.notifications import order_notification


XLSX_NS = {
    'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'rel': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'pkg_rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
}


IMPORT_MASTER_CONFIG = {
    'district': {
        'title': 'Import Kabupaten/Kota',
        'segment': 'district',
        'menu_id': 'KABUPATEN-KOTA',
        'allowed_role': 'KABUPATEN-KOTA',
        'index_url': 'district-index',
        'fields': [
            ('district_name', 'Nama Kabupaten/Kota'),
        ],
    },
    'sub_district': {
        'title': 'Import Kecamatan',
        'segment': 'sub-district',
        'menu_id': 'KECAMATAN',
        'allowed_role': 'KECAMATAN',
        'index_url': 'sub-district-index',
        'fields': [
            ('sub_district_name', 'Nama Kecamatan'),
        ],
    },
    'village': {
        'title': 'Import Desa/Kelurahan',
        'segment': 'village',
        'menu_id': 'DESA-KELURAHAN',
        'allowed_role': 'DESA-KELURAHAN',
        'index_url': 'village-index',
        'fields': [
            ('village_name', 'Nama Desa/Kelurahan'),
        ],
    },
}

IMPORT_FIELD_ALIASES = {
    'district_name': [
        'district_name', 'district', 'kabupaten', 'kabupaten kota',
        'kabupaten/kota', 'kab kota', 'kab/kota', 'kota', 'nama kabupaten',
        'nama kota', 'nama kabupaten kota', 'nama kabupaten/kota',
    ],
    'sub_district_name': [
        'sub_district_name', 'sub district', 'subdistrict', 'kecamatan',
        'nama kecamatan',
    ],
    'village_name': [
        'village_name', 'village', 'desa', 'kelurahan', 'desa kelurahan',
        'desa/kelurahan', 'nama desa', 'nama kelurahan',
        'nama desa kelurahan', 'nama desa/kelurahan',
    ],
}


def _import_session_key(master_key):
    return f'import_master_{master_key}'


def _column_letter_to_index(column_letters):
    index = 0
    for char in column_letters:
        index = index * 26 + (ord(char.upper()) - ord('A') + 1)
    return index - 1


def _get_xlsx_shared_strings(zip_file):
    if 'xl/sharedStrings.xml' not in zip_file.namelist():
        return []

    root = ET.fromstring(zip_file.read('xl/sharedStrings.xml'))
    values = []
    for item in root.findall('main:si', XLSX_NS):
        parts = []
        for text_node in item.findall('.//main:t', XLSX_NS):
            parts.append(text_node.text or '')
        values.append(''.join(parts))
    return values


def _get_first_sheet_path(zip_file):
    workbook_root = ET.fromstring(zip_file.read('xl/workbook.xml'))
    first_sheet = workbook_root.find('main:sheets/main:sheet', XLSX_NS)
    if first_sheet is None:
        raise ValueError('Sheet pertama tidak ditemukan.')

    relation_id = first_sheet.attrib.get(
        '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
    rels_root = ET.fromstring(zip_file.read('xl/_rels/workbook.xml.rels'))
    for relation in rels_root.findall('pkg_rel:Relationship', XLSX_NS):
        if relation.attrib.get('Id') == relation_id:
            target = relation.attrib.get('Target', '')
            return f"xl/{target}"

    raise ValueError('Relasi sheet Excel tidak ditemukan.')


def _cell_value(cell, shared_strings):
    cell_type = cell.attrib.get('t')
    if cell_type == 'inlineStr':
        return ''.join([
            text_node.text or ''
            for text_node in cell.findall('.//main:t', XLSX_NS)
        ])

    value_node = cell.find('main:v', XLSX_NS)
    if value_node is None or value_node.text is None:
        return ''

    value = value_node.text
    if cell_type == 's':
        try:
            return shared_strings[int(value)]
        except (ValueError, IndexError):
            return value

    return value


def _read_xlsx_rows(file_path):
    with zipfile.ZipFile(file_path, 'r') as zip_file:
        shared_strings = _get_xlsx_shared_strings(zip_file)
        sheet_path = _get_first_sheet_path(zip_file)
        sheet_root = ET.fromstring(zip_file.read(sheet_path))

    rows = []
    for row_node in sheet_root.findall('.//main:sheetData/main:row', XLSX_NS):
        row_values = {}
        max_index = -1
        for cell in row_node.findall('main:c', XLSX_NS):
            reference = cell.attrib.get('r', '')
            match = re.match(r'([A-Z]+)', reference)
            if not match:
                continue

            column_index = _column_letter_to_index(match.group(1))
            row_values[column_index] = _cell_value(cell, shared_strings)
            max_index = max(max_index, column_index)

        if max_index < 0:
            rows.append([])
            continue

        rows.append([
            row_values.get(index, '').strip()
            for index in range(max_index + 1)
        ])

    return rows


def _normalize_headers(header_row):
    headers = []
    seen = {}
    for index, header in enumerate(header_row):
        base_header = (header or '').strip() or f'Kolom {index + 1}'
        counter = seen.get(base_header, 0) + 1
        seen[base_header] = counter
        headers.append(
            base_header if counter == 1 else f'{base_header} ({counter})'
        )
    return headers


def _normalize_import_key(value):
    normalized = (value or '').strip().lower()
    normalized = normalized.replace('/', ' ')
    normalized = normalized.replace('-', ' ')
    normalized = normalized.replace('_', ' ')
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def _parse_rows(rows, empty_message):
    if not rows:
        raise ValueError(empty_message)

    headers = _normalize_headers(rows[0])
    data_rows = []
    for row in rows[1:]:
        normalized_row = list(row[:len(headers)])
        if len(normalized_row) < len(headers):
            normalized_row.extend([''] * (len(headers) - len(normalized_row)))
        data_rows.append(normalized_row)

    return headers, data_rows


def _parse_xlsx_file(file_path):
    rows = _read_xlsx_rows(file_path)
    return _parse_rows(rows, 'File Excel tidak berisi data.')


def _read_csv_rows(file_path):
    for encoding in ['utf-8-sig', 'utf-8', 'latin-1']:
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as csv_file:
                sample = csv_file.read(4096)
                csv_file.seek(0)
                dialect = csv.Sniffer().sniff(sample or ',')
                reader = csv.reader(csv_file, dialect)
                return [[(cell or '').strip() for cell in row] for row in reader]
        except UnicodeDecodeError:
            continue
        except csv.Error:
            with open(file_path, 'r', encoding=encoding, newline='') as csv_file:
                reader = csv.reader(csv_file)
                return [[(cell or '').strip() for cell in row] for row in reader]

    raise ValueError(
        'File CSV tidak dapat dibaca. Pastikan encoding file valid.')


def _parse_csv_file(file_path):
    rows = _read_csv_rows(file_path)
    return _parse_rows(rows, 'File CSV tidak berisi data.')


def _parse_import_file(file_path, extension):
    if extension == '.xlsx':
        return _parse_xlsx_file(file_path)
    if extension == '.csv':
        return _parse_csv_file(file_path)
    raise ValueError('Format file harus .xlsx atau .csv')


def _get_import_storage_dir():
    storage_dir = os.path.join(settings.MEDIA_ROOT, 'import_temp')
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir


def _save_uploaded_import_file(uploaded_file):
    extension = os.path.splitext(uploaded_file.name or '')[1].lower()
    if extension not in ['.xlsx', '.csv']:
        raise ValueError('Format file harus .xlsx atau .csv')

    filename = f"import_{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(_get_import_storage_dir(), filename)
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    return file_path, extension


def _remove_import_file(import_state):
    if not import_state:
        return

    file_path = import_state.get('file_path')
    if file_path and os.path.exists(file_path):
        os.remove(file_path)


def _suggest_import_mappings(field_options, headers):
    normalized_headers = {
        header: _normalize_import_key(header)
        for header in headers
    }
    used_headers = set()
    suggestions = {}

    for field_name, _field_label in field_options:
        aliases = [
            _normalize_import_key(alias)
            for alias in IMPORT_FIELD_ALIASES.get(field_name, [field_name])
        ]

        exact_match = None
        partial_match = None
        for header, normalized_header in normalized_headers.items():
            if header in used_headers:
                continue
            if normalized_header in aliases:
                exact_match = header
                break
            if any(alias in normalized_header or normalized_header in alias for alias in aliases):
                if partial_match is None:
                    partial_match = header

        selected_header = exact_match or partial_match
        if selected_header:
            suggestions[field_name] = selected_header
            used_headers.add(selected_header)

    return suggestions


def _resolve_auto_selected_fields(selected_mappings, suggested_mappings):
    auto_selected_fields = []
    for field_name, suggested_header in suggested_mappings.items():
        if suggested_header and selected_mappings.get(field_name) == suggested_header:
            auto_selected_fields.append(field_name)
    return auto_selected_fields


def _build_import_context(request, master_key, extra=None):
    config = IMPORT_MASTER_CONFIG[master_key]
    selected_mappings = (extra or {}).get('selected_mappings', {})
    auto_selected_fields = set((extra or {}).get('auto_selected_fields', []))
    mapping_fields = [
        {
            'name': field_name,
            'label': field_label,
            'selected': selected_mappings.get(field_name, ''),
            'auto_selected': field_name in auto_selected_fields,
        }
        for field_name, field_label in config['fields']
    ]
    context = {
        'segment': config['segment'],
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id=config['menu_id']) if not request.user.is_superuser else Auth.objects.all(),
        'master_key': master_key,
        'title': config['title'],
        'field_options': config['fields'],
        'mapping_fields': mapping_fields,
        'index_url': config['index_url'],
    }
    if extra:
        context.update(extra)
    return context


def _process_import_rows(master_key, mappings, headers, data_rows):
    results = {
        'created': 0,
        'existing': 0,
        'skipped': 0,
        'errors': [],
    }

    with transaction.atomic():
        for row_number, row in enumerate(data_rows, start=2):
            row_map = {
                headers[index]: (row[index] if index <
                                 len(row) else '').strip()
                for index in range(len(headers))
            }

            if not any(row_map.values()):
                results['skipped'] += 1
                continue

            try:
                if master_key == 'district':
                    district_name = row_map.get(
                        mappings['district_name'], '').strip()
                    if not district_name:
                        results['skipped'] += 1
                        continue

                    _, created = District.objects.get_or_create(
                        district_name=district_name
                    )

                elif master_key == 'sub_district':
                    sub_district_name = row_map.get(
                        mappings['sub_district_name'], '').strip()
                    if not sub_district_name:
                        results['skipped'] += 1
                        continue

                    _, created = SubDistrict.objects.get_or_create(
                        sub_district_name=sub_district_name,
                    )

                else:
                    village_name = row_map.get(
                        mappings['village_name'], '').strip()
                    if not village_name:
                        results['skipped'] += 1
                        continue

                    _, created = Village.objects.get_or_create(
                        village_name=village_name,
                    )

                if created:
                    results['created'] += 1
                else:
                    results['existing'] += 1

            except Exception as exc:
                results['errors'].append(f'Baris {row_number}: {exc}')

    return results


def _master_import_view(request, master_key):
    import_state = request.session.get(_import_session_key(master_key))
    context_extra = {'step': 'upload'}

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'upload':
            _remove_import_file(import_state)
            request.session.pop(_import_session_key(master_key), None)

            upload_file = request.FILES.get('import_file')
            if not upload_file:
                context_extra.update({
                    'message': 'Silakan pilih file .xlsx atau .csv terlebih dahulu.',
                    'message_type': 'danger',
                })
            else:
                file_path = None
                try:
                    file_path, extension = _save_uploaded_import_file(
                        upload_file)
                    headers, data_rows = _parse_import_file(
                        file_path, extension)
                    import_state = {
                        'extension': extension,
                        'headers': headers,
                        'data_rows': data_rows,
                        'original_name': upload_file.name,
                    }
                    _remove_import_file({'file_path': file_path})
                    selected_mappings = _suggest_import_mappings(
                        IMPORT_MASTER_CONFIG[master_key]['fields'],
                        headers
                    )
                    request.session[_import_session_key(
                        master_key)] = import_state
                    context_extra.update({
                        'step': 'mapping',
                        'headers': headers,
                        'preview_rows': data_rows[:5],
                        'total_rows': len(data_rows),
                        'file_name': upload_file.name,
                        'selected_mappings': selected_mappings,
                        'auto_selected_fields': list(selected_mappings.keys()),
                    })
                except Exception as exc:
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                    context_extra.update({
                        'message': str(exc),
                        'message_type': 'danger',
                    })

        elif action == 'import':
            if not import_state:
                context_extra.update({
                    'message': 'Sesi import sudah habis. Silakan upload ulang file .xlsx atau .csv.',
                    'message_type': 'danger',
                })
            else:
                config = IMPORT_MASTER_CONFIG[master_key]
                mappings = {}
                missing = []
                for field_name, field_label in config['fields']:
                    selected_header = request.POST.get(
                        f'map_{field_name}', '').strip()
                    mappings[field_name] = selected_header
                    if not selected_header:
                        missing.append(field_label)

                try:
                    headers = import_state.get('headers', [])
                    data_rows = import_state.get('data_rows', [])
                    if not headers:
                        raise ValueError(
                            'Data import tidak ditemukan di sesi. Silakan upload ulang file Anda.')
                    suggested_mappings = _suggest_import_mappings(
                        IMPORT_MASTER_CONFIG[master_key]['fields'],
                        headers
                    )
                    if missing:
                        context_extra.update({
                            'step': 'mapping',
                            'headers': import_state['headers'],
                            'preview_rows': data_rows[:5],
                            'total_rows': len(data_rows),
                            'file_name': import_state.get('original_name'),
                            'selected_mappings': mappings,
                            'auto_selected_fields': _resolve_auto_selected_fields(
                                mappings, suggested_mappings
                            ),
                            'message': 'Mapping wajib diisi untuk: ' + ', '.join(missing),
                            'message_type': 'danger',
                        })
                    else:
                        results = _process_import_rows(
                            master_key, mappings, headers, data_rows)
                        summary = (
                            f"Import selesai. Data baru: {results['created']}, "
                            f"sudah ada: {results['existing']}, "
                            f"dilewati: {results['skipped']}."
                        )
                        if results['errors']:
                            summary += f" Error: {len(results['errors'])} baris."

                        _remove_import_file(import_state)
                        request.session.pop(
                            _import_session_key(master_key), None)

                        context_extra.update({
                            'message': summary,
                            'message_type': 'success' if not results['errors'] else 'warning',
                            'import_errors': results['errors'][:20],
                        })
                except Exception as exc:
                    context_extra.update({
                        'message': str(exc),
                        'message_type': 'danger',
                    })

    if import_state and context_extra.get('step') != 'mapping':
        try:
            headers = import_state.get('headers', [])
            data_rows = import_state.get('data_rows', [])
            if not headers:
                raise ValueError(
                    'Data import tidak ditemukan di sesi. Silakan upload ulang file Anda.')
            selected_mappings = _suggest_import_mappings(
                IMPORT_MASTER_CONFIG[master_key]['fields'],
                headers
            )
            context_extra.update({
                'step': 'mapping',
                'headers': headers,
                'preview_rows': data_rows[:5],
                'total_rows': len(data_rows),
                'file_name': import_state.get('original_name'),
                'selected_mappings': selected_mappings,
                'auto_selected_fields': list(selected_mappings.keys()),
            })
        except Exception as exc:
            _remove_import_file(import_state)
            request.session.pop(_import_session_key(master_key), None)
            context_extra.update({
                'step': 'upload',
                'message': str(exc),
                'message_type': 'danger',
            })

    return render(
        request,
        'home/master_import.html',
        _build_import_context(request, master_key, context_extra)
    )


@login_required(login_url='/login/')
def home(request):
    context = {
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
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
                # 'notif': order_notification(request),
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
            # 'notif': order_notification(request),
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
    # area = AreaUser.objects.filter(user_id=_id)
    form = FormUserView(instance=users)
    position = Position.objects.all()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_menu.menu_id, menu_name, q_auth.menu_id FROM apps_menu LEFT JOIN (SELECT * FROM apps_auth WHERE user_id = '" + str(_id) + "') AS q_auth ON apps_menu.menu_id = q_auth.menu_id WHERE q_auth.menu_id IS NULL")
        menu = cursor.fetchall()
    # with connection.cursor() as cursor:
    #     cursor.execute(
    #         "SELECT apps_areasales.area_id, area_name, q_area.area_id FROM apps_areasales LEFT JOIN (SELECT * FROM apps_areauser WHERE user_id = '" + str(_id) + "') AS q_area ON apps_areasales.area_id = q_area.area_id WHERE q_area.area_id IS NULL")
    #     item_area = cursor.fetchall()

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
        # 'area': area,
        # 'item_area': item_area,
        'positions': position,
        # 'notif': order_notification(request),
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
# def user_area_view(request, _id):
#     users = User.objects.get(user_id=_id)
#     auth = Auth.objects.filter(user_id=_id)
#     area = AreaUser.objects.filter(user_id=_id)
#     form = FormUserView(instance=users)
#     position = Position.objects.all()
#     with connection.cursor() as cursor:
#         cursor.execute(
#             "SELECT apps_menu.menu_id, menu_name, q_auth.menu_id FROM apps_menu LEFT JOIN (SELECT * FROM apps_auth WHERE user_id = '" + str(_id) + "') AS q_auth ON apps_menu.menu_id = q_auth.menu_id WHERE q_auth.menu_id IS NULL")
#         menu = cursor.fetchall()
#     with connection.cursor() as cursor:
#         cursor.execute(
#             "SELECT apps_areasales.area_id, area_name, q_area.area_id FROM apps_areasales LEFT JOIN (SELECT * FROM apps_areauser WHERE user_id = '" + str(_id) + "') AS q_area ON apps_areasales.area_id = q_area.area_id WHERE q_area.area_id IS NULL")
#         item_area = cursor.fetchall()
#     if request.POST:
#         area_check = request.POST.getlist('area[]')
#         for i in item_area:
#             if str(i[0]) in area_check:
#                 try:
#                     area = AreaUser(user_id=_id, area_id=i[0])
#                     area.save()
#                 except IntegrityError:
#                     continue
#             else:
#                 AreaUser.objects.filter(user_id=_id, area_id=i[0]).delete()
#         return HttpResponseRedirect(reverse('user-area-view', args=[_id, ]))
#     context = {
#         'form': form,
#         'formAuth': form,
#         'data': users,
#         'auth': auth,
#         'menu': menu,
#         'area': area,
#         'item_area': item_area,
#         'positions': position,
#         'notif': order_notification(request),
#         'segment': 'user',
#         'group_segment': 'master',
#         'tab': 'area',
#         'crud': 'view',
#         'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
#         'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
#     }
#     return render(request, 'home/user_view.html', context)
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
# def area_user_delete(request, _id, _area):
#     area = AreaUser.objects.filter(user=_id, area=_area)
#     area.delete()
#     return HttpResponseRedirect(reverse('user-area-view', args=[_id, ]))
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
    # area = AreaUser.objects.filter(user_id=_id)

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
        # 'area': area,
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
        'segment': 'user',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_set_password.html', context)


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
                # 'notif': order_notification(request),
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
            # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
        'segment': 'position',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/position_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='STATUS-GURU')
def teacher_status_add(request):
    if request.POST:
        form = FormTeacherStatus(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('teacher-status-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'teacher-status',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='STATUS-GURU') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/teacher_status_add.html', context)
    else:
        form = FormTeacherStatus()
        context = {
            'form': form,
            'segment': 'teacher-status',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='STATUS-GURU') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/teacher_status_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='STATUS-GURU')
def teacher_status_index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT status_id, status_name FROM apps_teacherstatus")
        statuses = cursor.fetchall()

    context = {
        'data': statuses,
        'segment': 'teacher-status',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='STATUS-GURU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_status_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='STATUS-GURU')
def teacher_status_update(request, _id):
    teacher_status = TeacherStatus.objects.get(status_id=_id)
    if request.POST:
        form = FormTeacherStatusUpdate(
            request.POST, request.FILES, instance=teacher_status)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('teacher-status-view', args=[_id, ]))
    else:
        form = FormTeacherStatusUpdate(instance=teacher_status)

    message = form.errors
    context = {
        'form': form,
        'data': teacher_status,
        'segment': 'teacher-status',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='STATUS-GURU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_status_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='STATUS-GURU')
def teacher_status_delete(request, _id):
    teacher_status = TeacherStatus.objects.get(status_id=_id)
    teacher_status.delete()
    return HttpResponseRedirect(reverse('teacher-status-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='STATUS-GURU')
def teacher_status_view(request, _id):
    teacher_status = TeacherStatus.objects.get(status_id=_id)
    form = FormTeacherStatusView(instance=teacher_status)

    context = {
        'form': form,
        'data': teacher_status,
        'segment': 'teacher-status',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='STATUS-GURU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_status_view.html', context)


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
                # 'notif': order_notification(request),
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
            # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
        'segment': 'menu',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/menu_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLOSING-PERIOD')
def closing_index(request):
    periods = Closing.objects.all()

    context = {
        'data': periods,
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
        'segment': 'closing_period',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLOSING-PERIOD') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/closing_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DIVISION')
def division_index(request):
    divisions = Division.objects.all()

    context = {
        'data': divisions,
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
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
        # 'notif': order_notification(request),
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
@role_required(allowed_roles='LEVEL')
def level_index(request):
    levels = Level.objects.all()

    context = {
        'data': levels,
        # 'notif': order_notification(request),
        'segment': 'level',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='LEVEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/level_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='LEVEL')
def level_add(request):
    if request.POST:
        form = FormLevel(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('level-index'))
    else:
        form = FormLevel()

    context = {
        'form': form,
        # 'notif': order_notification(request),
        'segment': 'level',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='LEVEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/level_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='LEVEL')
def level_update(request, _id):
    level = Level.objects.get(level_id=_id)

    if request.POST:
        form = FormLevelUpdate(request.POST, request.FILES, instance=level)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('level-index'))
    else:
        form = FormLevelUpdate(instance=level)

    context = {
        'form': form,
        'data': level,
        # 'notif': order_notification(request),
        'segment': 'level',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='LEVEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/level_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='LEVEL')
def level_delete(request, _id):
    level = Level.objects.get(level_id=_id)
    level.delete()

    return HttpResponseRedirect(reverse('level-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='LEVEL')
def level_view(request, _id):
    level = Level.objects.get(level_id=_id)
    form = FormLevelView(instance=level)

    context = {
        'data': level,
        'form': form,
        # 'notif': order_notification(request),
        'segment': 'level',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='LEVEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/level_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GRADE')
def grade_index(request):
    grades = Grade.objects.all().order_by('grade', 'sub_grade', 'grade_name')

    context = {
        'data': grades,
        'segment': 'grade',
        'group_segment': 'kurikulum',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GRADE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/grade_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GRADE')
def grade_add(request):
    if request.POST:
        form = FormGrade(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('grade-index'))
    else:
        form = FormGrade()

    context = {
        'form': form,
        'segment': 'grade',
        'group_segment': 'kurikulum',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GRADE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/grade_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GRADE')
def grade_update(request, _id):
    grade = Grade.objects.get(grade_id=_id)

    if request.POST:
        form = FormGradeUpdate(request.POST, request.FILES, instance=grade)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('grade-index'))
    else:
        form = FormGradeUpdate(instance=grade)

    context = {
        'form': form,
        'data': grade,
        'segment': 'grade',
        'group_segment': 'kurikulum',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GRADE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/grade_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GRADE')
def grade_delete(request, _id):
    grade = Grade.objects.get(grade_id=_id)
    grade.delete()

    return HttpResponseRedirect(reverse('grade-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='GRADE')
def grade_view(request, _id):
    grade = Grade.objects.get(grade_id=_id)
    form = FormGradeView(instance=grade)

    context = {
        'data': grade,
        'form': form,
        'segment': 'grade',
        'group_segment': 'kurikulum',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GRADE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/grade_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def student_by_grade(request):
    grades = Grade.objects.select_related('school_year', 'level').annotate(
        student_count=models.Count('student')
    ).order_by('school_year__school_year_name', 'grade', 'sub_grade', 'grade_name')

    context = {
        'data': grades,
        'segment': 'kelas-santri',
        'group_segment': 'santri',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DATA-SANTRI') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/student_by_grade.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def grade_detail_view(request, _id):
    grade = Grade.objects.select_related(
        'level', 'school_year',
        'class_leader', 'vice_class_leader', 'secretary', 'treasurer'
    ).get(grade_id=_id)
    students = Student.objects.filter(grade=grade).order_by('name')
    unassigned_students = Student.objects.filter(grade__isnull=True).order_by('name')
    form = FormGradeView(instance=grade)

    context = {
        'data': grade,
        'form': form,
        'students': students,
        'unassigned_students': unassigned_students,
        'segment': 'kelas-santri',
        'group_segment': 'santri',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                menu_id='KELAS-SANTRI').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/grade_detail.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def grade_detail_update(request, _id):
    grade = Grade.objects.select_related(
        'level', 'school_year',
        'class_leader', 'vice_class_leader', 'secretary', 'treasurer'
    ).get(grade_id=_id)
    students = Student.objects.filter(grade=grade).order_by('name')
    unassigned_students = Student.objects.filter(grade__isnull=True).order_by('name')

    if request.POST:
        form = FormGradeUpdate(request.POST, instance=grade)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('grade-detail-view', args=[_id]))
    else:
        form = FormGradeUpdate(instance=grade)

    context = {
        'data': grade,
        'form': form,
        'students': students,
        'unassigned_students': unassigned_students,
        'segment': 'kelas-santri',
        'group_segment': 'santri',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                menu_id='KELAS-SANTRI').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/grade_detail.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def grade_remove_student(request, grade_id, student_id):
    """Lepas santri dari kelas (set grade ke null, data santri tetap ada)."""
    try:
        student = Student.objects.get(student_id=student_id, grade_id=grade_id)
        student.grade = None
        student.save()
    except Student.DoesNotExist:
        pass
    return HttpResponseRedirect(reverse('grade-detail-view', args=[grade_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def grade_add_student(request, grade_id):
    """Masukkan santri ke dalam kelas."""
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        if student_ids:
            Student.objects.filter(
                student_id__in=student_ids
            ).update(grade_id=grade_id)
    return HttpResponseRedirect(reverse('grade-detail-view', args=[grade_id]))


# ── Student by Hostel Views ───────────────────────────────────────────────────

@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def student_by_hostel(request):
    hostels = Hostel.objects.annotate(
        student_count=Count('student')
    ).order_by('hostel_name')
    context = {
        'data': hostels,
        'segment': 'asrama-santri',
        'group_segment': 'santri',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DATA-SANTRI') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/student_by_hostel.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-TAHFIDZ')
def student_by_halaqoh_tahfidz(request):
    data = HalaqohTahfidz.objects.select_related(
        'teacher__user', 'grade__school_year'
    ).annotate(member_count=Count('members')).order_by(
        '-grade__school_year__school_year_name', 'teacher__user__username')
    context = {
        'data': data,
        'segment': 'santri-tahfidz',
        'group_segment': 'santri',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                   menu_id='HALAQOH-TAHFIDZ').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/student_by_halaqoh_tahfidz.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-LUGHOH')
def student_by_halaqoh_lughoh(request):
    data = HalaqohLughoh.objects.select_related(
        'teacher__user', 'grade__school_year'
    ).annotate(member_count=Count('members')).order_by(
        '-grade__school_year__school_year_name', 'teacher__user__username')
    context = {
        'data': data,
        'segment': 'santri-lughoh',
        'group_segment': 'santri',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                   menu_id='HALAQOH-LUGHOH').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/student_by_halaqoh_lughoh.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def hostel_detail_view(request, _id):
    hostel = Hostel.objects.get(hostel_id=_id)
    students = Student.objects.filter(hostel=hostel).order_by('name')
    non_members = Student.objects.filter(hostel__isnull=True).order_by('name')
    context = {
        'data': hostel,
        'students': students,
        'non_members': non_members,
        'segment': 'asrama-santri',
        'group_segment': 'santri',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                menu_id='ASRAMA-SANTRI').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/hostel_detail.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def hostel_add_student(request, hostel_id):
    """Masukkan santri ke dalam asrama."""
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        if student_ids:
            Student.objects.filter(
                student_id__in=student_ids
            ).update(hostel_id=hostel_id)
    return HttpResponseRedirect(reverse('hostel-detail-view', args=[hostel_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def hostel_remove_student(request, hostel_id, student_id):
    """Lepas santri dari asrama (set hostel ke null)."""
    try:
        student = Student.objects.get(student_id=student_id, hostel_id=hostel_id)
        student.hostel = None
        student.save()
    except Student.DoesNotExist:
        pass
    return HttpResponseRedirect(reverse('hostel-detail-view', args=[hostel_id]))


# ── Study Group Views ─────────────────────────────────────────────────────────

def _study_group_context(request, extra=None):
    base = {
        'segment': 'kelompok-belajar',
        'group_segment': 'santri',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DATA-SANTRI') if not request.user.is_superuser else Auth.objects.all(),
    }
    if extra:
        base.update(extra)
    return base


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def study_group_index(request):
    groups = StudyGroup.objects.select_related('school_year').annotate(
        member_count=Count('members')
    ).order_by('-school_year__school_year_name', 'group_name')
    ctx = _study_group_context(request, {'data': groups, 'crud': 'index'})
    return render(request, 'home/study_group_index.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def study_group_add(request):
    if request.POST:
        form = FormStudyGroup(request.POST)
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(reverse('study-group-detail-view', args=[instance.study_group_id]))
    else:
        form = FormStudyGroup()
    ctx = _study_group_context(request, {'form': form, 'crud': 'add'})
    return render(request, 'home/study_group_add.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def study_group_detail_view(request, _id):
    group = StudyGroup.objects.select_related('school_year').get(study_group_id=_id)
    members = StudyGroupMember.objects.filter(
        study_group=group).select_related('student').order_by('student__name')
    non_members = Student.objects.exclude(
        study_group_memberships__study_group=group
    ).order_by('name')
    form = FormStudyGroupView(instance=group)
    ctx = _study_group_context(request, {
        'data': group, 'form': form,
        'members': members, 'non_members': non_members, 'crud': 'view',
    })
    return render(request, 'home/study_group_detail.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def study_group_detail_update(request, _id):
    group = StudyGroup.objects.select_related('school_year').get(study_group_id=_id)
    members = StudyGroupMember.objects.filter(
        study_group=group).select_related('student').order_by('student__name')
    non_members = Student.objects.exclude(
        study_group_memberships__study_group=group
    ).order_by('name')
    if request.POST:
        form = FormStudyGroupUpdate(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('study-group-detail-view', args=[_id]))
    else:
        form = FormStudyGroupUpdate(instance=group)
    ctx = _study_group_context(request, {
        'data': group, 'form': form,
        'members': members, 'non_members': non_members, 'crud': 'update',
    })
    return render(request, 'home/study_group_detail.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def study_group_delete(request, _id):
    StudyGroup.objects.get(study_group_id=_id).delete()
    return HttpResponseRedirect(reverse('study-group-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def study_group_add_student(request, group_id):
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        group = StudyGroup.objects.get(study_group_id=group_id)
        for sid in student_ids:
            StudyGroupMember.objects.get_or_create(study_group=group, student_id=sid)
    return HttpResponseRedirect(reverse('study-group-detail-view', args=[group_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def study_group_remove_student(request, group_id, student_id):
    StudyGroupMember.objects.filter(
        study_group_id=group_id, student_id=student_id
    ).delete()
    return HttpResponseRedirect(reverse('study-group-detail-view', args=[group_id]))


# ── Teacher (Guru) Views ───────────────────────────────────────────────────────

@login_required(login_url='/login/')
@role_required(allowed_roles='GURU')
def teacher_index(request):
    teachers = Teacher.objects.select_related('user', 'status').order_by('user__username')
    context = {
        'data': teachers,
        'segment': 'guru',
        'group_segment': 'kurikulum',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GURU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GURU')
def teacher_add(request):
    if request.POST:
        form = FormTeacher(request.POST)
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(reverse('teacher-view', args=[instance.teacher_id]))
    else:
        form = FormTeacher()
    context = {
        'form': form,
        'segment': 'guru',
        'group_segment': 'kurikulum',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GURU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GURU')
def teacher_view(request, _id):
    teacher = Teacher.objects.select_related('user').get(teacher_id=_id)
    form = FormTeacherView(instance=teacher)
    context = {
        'data': teacher,
        'form': form,
        'segment': 'guru',
        'group_segment': 'kurikulum',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GURU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GURU')
def teacher_update(request, _id):
    teacher = Teacher.objects.select_related('user').get(teacher_id=_id)
    if request.POST:
        form = FormTeacherUpdate(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('teacher-view', args=[_id]))
    else:
        form = FormTeacherUpdate(instance=teacher)
    context = {
        'data': teacher,
        'form': form,
        'segment': 'guru',
        'group_segment': 'kurikulum',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GURU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GURU')
def teacher_delete(request, _id):
    Teacher.objects.get(teacher_id=_id).delete()
    return HttpResponseRedirect(reverse('teacher-index'))


# ── Halaqoh Tahfidz Views ──────────────────────────────────────────────────────

def _halaqoh_context(request, menu_id, segment, extra=None):
    base = {
        'segment': segment,
        'group_segment': 'santri',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                   menu_id=menu_id).first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    if extra:
        base.update(extra)
    return base


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-TAHFIDZ')
def halaqoh_tahfidz_index(request):
    data = HalaqohTahfidz.objects.select_related(
        'teacher__user', 'grade__school_year'
    ).annotate(member_count=Count('members')).order_by(
        '-grade__school_year__school_year_name', 'teacher__user__username')
    ctx = _halaqoh_context(request, 'HALAQOH-TAHFIDZ', 'halaqoh-tahfidz',
                           {'data': data, 'crud': 'index'})
    return render(request, 'home/halaqoh_tahfidz_index.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-TAHFIDZ')
def halaqoh_tahfidz_add(request):
    if request.POST:
        form = FormHalaqohTahfidz(request.POST)
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(reverse('halaqoh-tahfidz-detail', args=[instance.halaqoh_id]))
    else:
        form = FormHalaqohTahfidz()
    ctx = _halaqoh_context(request, 'HALAQOH-TAHFIDZ', 'halaqoh-tahfidz',
                           {'form': form, 'crud': 'add'})
    return render(request, 'home/halaqoh_tahfidz_add.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-TAHFIDZ')
def halaqoh_tahfidz_student_view(request, _id):
    halaqoh = HalaqohTahfidz.objects.select_related('teacher__user', 'grade__school_year').get(halaqoh_id=_id)
    members = HalaqohTahfidzMember.objects.filter(halaqoh=halaqoh).select_related('student').order_by('student__name')
    non_members = Student.objects.exclude(halaqoh_tahfidz_memberships__halaqoh=halaqoh).order_by('name')
    context = {
        'data': halaqoh,
        'members': members,
        'non_members': non_members,
        'segment': 'santri-tahfidz',
        'group_segment': 'santri',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                   menu_id='SANTRI-TAHFIDZ').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/halaqoh_tahfidz_student_detail.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-LUGHOH')
def halaqoh_lughoh_student_view(request, _id):
    halaqoh = HalaqohLughoh.objects.select_related('teacher__user', 'grade__school_year').get(halaqoh_id=_id)
    members = HalaqohLughohMember.objects.filter(halaqoh=halaqoh).select_related('student').order_by('student__name')
    non_members = Student.objects.exclude(halaqoh_lughoh_memberships__halaqoh=halaqoh).order_by('name')
    context = {
        'data': halaqoh,
        'members': members,
        'non_members': non_members,
        'segment': 'santri-lughoh',
        'group_segment': 'santri',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                   menu_id='SANTRI-LUGHOH').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/halaqoh_lughoh_student_detail.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-TAHFIDZ')
def halaqoh_tahfidz_detail(request, _id):
    halaqoh = HalaqohTahfidz.objects.select_related('teacher__user', 'grade__school_year').get(halaqoh_id=_id)
    members = HalaqohTahfidzMember.objects.filter(halaqoh=halaqoh).select_related('student').order_by('student__name')
    non_members = Student.objects.exclude(halaqoh_tahfidz_memberships__halaqoh=halaqoh).order_by('name')
    ctx = _halaqoh_context(request, 'HALAQOH-TAHFIDZ', 'halaqoh-tahfidz',
                           {'data': halaqoh, 'members': members, 'non_members': non_members, 'crud': 'view'})
    return render(request, 'home/halaqoh_tahfidz_detail.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-TAHFIDZ')
def halaqoh_tahfidz_update(request, _id):
    halaqoh = HalaqohTahfidz.objects.select_related('teacher__user', 'grade__school_year').get(halaqoh_id=_id)
    members = HalaqohTahfidzMember.objects.filter(halaqoh=halaqoh).select_related('student').order_by('student__name')
    non_members = Student.objects.exclude(halaqoh_tahfidz_memberships__halaqoh=halaqoh).order_by('name')
    if request.POST:
        form = FormHalaqohTahfidzUpdate(request.POST, instance=halaqoh)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('halaqoh-tahfidz-detail', args=[_id]))
    else:
        form = FormHalaqohTahfidzUpdate(instance=halaqoh)
    ctx = _halaqoh_context(request, 'HALAQOH-TAHFIDZ', 'halaqoh-tahfidz',
                           {'data': halaqoh, 'form': form, 'members': members,
                            'non_members': non_members, 'crud': 'update'})
    return render(request, 'home/halaqoh_tahfidz_detail.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-TAHFIDZ')
def halaqoh_tahfidz_delete(request, _id):
    HalaqohTahfidz.objects.get(halaqoh_id=_id).delete()
    return HttpResponseRedirect(reverse('halaqoh-tahfidz-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-TAHFIDZ')
def halaqoh_tahfidz_add_student(request, halaqoh_id):
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        halaqoh = HalaqohTahfidz.objects.get(halaqoh_id=halaqoh_id)
        for sid in student_ids:
            HalaqohTahfidzMember.objects.get_or_create(halaqoh=halaqoh, student_id=sid)
    # Redirect ke student view jika dari santri, ke detail jika dari kurikulum
    referer = request.META.get('HTTP_REFERER', '')
    if 'per-halaqoh-tahfidz' in referer:
        return HttpResponseRedirect(reverse('halaqoh-tahfidz-student-view', args=[halaqoh_id]))
    return HttpResponseRedirect(reverse('halaqoh-tahfidz-detail', args=[halaqoh_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-TAHFIDZ')
def halaqoh_tahfidz_remove_student(request, halaqoh_id, student_id):
    HalaqohTahfidzMember.objects.filter(halaqoh_id=halaqoh_id, student_id=student_id).delete()
    referer = request.META.get('HTTP_REFERER', '')
    if 'per-halaqoh-tahfidz' in referer:
        return HttpResponseRedirect(reverse('halaqoh-tahfidz-student-view', args=[halaqoh_id]))
    return HttpResponseRedirect(reverse('halaqoh-tahfidz-detail', args=[halaqoh_id]))


# ── Halaqoh Lughoh Views ───────────────────────────────────────────────────────

@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-LUGHOH')
def halaqoh_lughoh_index(request):
    data = HalaqohLughoh.objects.select_related(
        'teacher__user', 'grade__school_year'
    ).annotate(member_count=Count('members')).order_by(
        '-grade__school_year__school_year_name', 'teacher__user__username')
    ctx = _halaqoh_context(request, 'HALAQOH-LUGHOH', 'halaqoh-lughoh',
                           {'data': data, 'crud': 'index'})
    return render(request, 'home/halaqoh_lughoh_index.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-LUGHOH')
def halaqoh_lughoh_add(request):
    if request.POST:
        form = FormHalaqohLughoh(request.POST)
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(reverse('halaqoh-lughoh-detail', args=[instance.halaqoh_id]))
    else:
        form = FormHalaqohLughoh()
    ctx = _halaqoh_context(request, 'HALAQOH-LUGHOH', 'halaqoh-lughoh',
                           {'form': form, 'crud': 'add'})
    return render(request, 'home/halaqoh_lughoh_add.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-LUGHOH')
def halaqoh_lughoh_detail(request, _id):
    halaqoh = HalaqohLughoh.objects.select_related('teacher__user', 'grade__school_year').get(halaqoh_id=_id)
    members = HalaqohLughohMember.objects.filter(halaqoh=halaqoh).select_related('student').order_by('student__name')
    non_members = Student.objects.exclude(halaqoh_lughoh_memberships__halaqoh=halaqoh).order_by('name')
    ctx = _halaqoh_context(request, 'HALAQOH-LUGHOH', 'halaqoh-lughoh',
                           {'data': halaqoh, 'members': members, 'non_members': non_members, 'crud': 'view'})
    return render(request, 'home/halaqoh_lughoh_detail.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-LUGHOH')
def halaqoh_lughoh_update(request, _id):
    halaqoh = HalaqohLughoh.objects.select_related('teacher__user', 'grade__school_year').get(halaqoh_id=_id)
    members = HalaqohLughohMember.objects.filter(halaqoh=halaqoh).select_related('student').order_by('student__name')
    non_members = Student.objects.exclude(halaqoh_lughoh_memberships__halaqoh=halaqoh).order_by('name')
    if request.POST:
        form = FormHalaqohLughohUpdate(request.POST, instance=halaqoh)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('halaqoh-lughoh-detail', args=[_id]))
    else:
        form = FormHalaqohLughohUpdate(instance=halaqoh)
    ctx = _halaqoh_context(request, 'HALAQOH-LUGHOH', 'halaqoh-lughoh',
                           {'data': halaqoh, 'form': form, 'members': members,
                            'non_members': non_members, 'crud': 'update'})
    return render(request, 'home/halaqoh_lughoh_detail.html', ctx)


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-LUGHOH')
def halaqoh_lughoh_delete(request, _id):
    HalaqohLughoh.objects.get(halaqoh_id=_id).delete()
    return HttpResponseRedirect(reverse('halaqoh-lughoh-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-LUGHOH')
def halaqoh_lughoh_add_student(request, halaqoh_id):
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        halaqoh = HalaqohLughoh.objects.get(halaqoh_id=halaqoh_id)
        for sid in student_ids:
            HalaqohLughohMember.objects.get_or_create(halaqoh=halaqoh, student_id=sid)
    # Redirect ke student view jika dari santri, ke detail jika dari kurikulum
    referer = request.META.get('HTTP_REFERER', '')
    if 'per-halaqoh-lughoh' in referer:
        return HttpResponseRedirect(reverse('halaqoh-lughoh-student-view', args=[halaqoh_id]))
    return HttpResponseRedirect(reverse('halaqoh-lughoh-detail', args=[halaqoh_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='HALAQOH-LUGHOH')
def halaqoh_lughoh_remove_student(request, halaqoh_id, student_id):
    HalaqohLughohMember.objects.filter(halaqoh_id=halaqoh_id, student_id=student_id).delete()
    referer = request.META.get('HTTP_REFERER', '')
    if 'per-halaqoh-lughoh' in referer:
        return HttpResponseRedirect(reverse('halaqoh-lughoh-student-view', args=[halaqoh_id]))
    return HttpResponseRedirect(reverse('halaqoh-lughoh-detail', args=[halaqoh_id]))


# ── Extracurricular Views ──────────────────────────────────────────────────────

@login_required(login_url='/login/')
@role_required(allowed_roles='EKSKUL')
def extracurricular_index(request):
    data = Extracurricular.objects.select_related('teacher__user').order_by('name')
    context = {
        'data': data,
        'segment': 'ekskul',
        'group_segment': 'kurikulum',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                   menu_id='EKSKUL').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/extracurricular_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='EKSKUL')
def extracurricular_add(request):
    if request.POST:
        form = FormExtracurricular(request.POST)
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(reverse('extracurricular-view', args=[instance.extracurricular_id]))
    else:
        form = FormExtracurricular()
    context = {
        'form': form,
        'segment': 'ekskul',
        'group_segment': 'kurikulum',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                   menu_id='EKSKUL').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/extracurricular_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='EKSKUL')
def extracurricular_view(request, _id):
    ekskul = Extracurricular.objects.select_related('teacher__user').get(extracurricular_id=_id)
    form = FormExtracurricularView(instance=ekskul)
    context = {
        'data': ekskul,
        'form': form,
        'segment': 'ekskul',
        'group_segment': 'kurikulum',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                   menu_id='EKSKUL').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/extracurricular_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='EKSKUL')
def extracurricular_update(request, _id):
    ekskul = Extracurricular.objects.select_related('teacher__user').get(extracurricular_id=_id)
    if request.POST:
        form = FormExtracurricularUpdate(request.POST, instance=ekskul)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('extracurricular-view', args=[_id]))
    else:
        form = FormExtracurricularUpdate(instance=ekskul)
    context = {
        'data': ekskul,
        'form': form,
        'segment': 'ekskul',
        'group_segment': 'kurikulum',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                   menu_id='EKSKUL').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/extracurricular_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='EKSKUL')
def extracurricular_delete(request, _id):
    Extracurricular.objects.get(extracurricular_id=_id).delete()
    return HttpResponseRedirect(reverse('extracurricular-index'))


# ── Santri Per Ekskul Views ────────────────────────────────────────────────────

@login_required(login_url='/login/')
@role_required(allowed_roles='EKSKUL-SANTRI')
def student_by_extracurricular(request):
    data = Extracurricular.objects.select_related('teacher__user').annotate(
        member_count=Count('members')
    ).order_by('name')
    context = {
        'data': data,
        'segment': 'ekskul-santri',
        'group_segment': 'santri',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                   menu_id='EKSKUL-SANTRI').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/student_by_extracurricular.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='EKSKUL-SANTRI')
def extracurricular_student_view(request, _id):
    ekskul = Extracurricular.objects.select_related('teacher__user').get(extracurricular_id=_id)
    members = ExtracurricularMember.objects.filter(
        extracurricular=ekskul).select_related('student').order_by('student__name')
    non_members = Student.objects.exclude(
        extracurricular_memberships__extracurricular=ekskul).order_by('name')
    context = {
        'data': ekskul,
        'members': members,
        'non_members': non_members,
        'segment': 'ekskul-santri',
        'group_segment': 'santri',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.filter(user_id=request.user.user_id,
                                   menu_id='EKSKUL-SANTRI').first() or Auth() if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/extracurricular_student_detail.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='EKSKUL-SANTRI')
def extracurricular_add_student(request, ekskul_id):
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        ekskul = Extracurricular.objects.get(extracurricular_id=ekskul_id)
        for sid in student_ids:
            ExtracurricularMember.objects.get_or_create(extracurricular=ekskul, student_id=sid)
    return HttpResponseRedirect(reverse('extracurricular-student-view', args=[ekskul_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='EKSKUL-SANTRI')
def extracurricular_remove_student(request, ekskul_id, student_id):
    ExtracurricularMember.objects.filter(
        extracurricular_id=ekskul_id, student_id=student_id).delete()
    return HttpResponseRedirect(reverse('extracurricular-student-view', args=[ekskul_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def student_index(request):
    students = Student.objects.select_related(
        'grade', 'hostel', 'religion', 'residence_type',
        'district', 'sub_district', 'village').all().order_by('name')

    context = {
        'data': students,
        'segment': 'data-santri',
        'group_segment': 'santri',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DATA-SANTRI') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/student_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def student_add(request):
    if request.POST:
        form = FormStudent(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('student-index'))
    else:
        form = FormStudent()

    context = {
        'form': form,
        'segment': 'data-santri',
        'group_segment': 'santri',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DATA-SANTRI') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/student_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def student_update(request, _id):
    student = Student.objects.get(student_id=_id)

    if request.POST:
        form = FormStudent(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('student-view', args=[_id, ]))
    else:
        form = FormStudent(instance=student)

    context = {
        'form': form,
        'data': student,
        'segment': 'data-santri',
        'group_segment': 'santri',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DATA-SANTRI') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/student_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def student_delete(request, _id):
    student = Student.objects.get(student_id=_id)
    student.delete()

    return HttpResponseRedirect(reverse('student-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def student_view(request, _id):
    student = Student.objects.get(student_id=_id)
    form = FormStudent(instance=student)

    for field in form.fields.values():
        if hasattr(field.widget, 'attrs'):
            field.widget.attrs['disabled'] = 'disabled'

    context = {
        'data': student,
        'form': form,
        'segment': 'data-santri',
        'group_segment': 'santri',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DATA-SANTRI') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/student_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='AGAMA')
def religion_index(request):
    religions = Religion.objects.all().order_by('religion_name')

    context = {
        'data': religions,
        'segment': 'religion',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='AGAMA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/religion_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='AGAMA')
def religion_add(request):
    if request.POST:
        form = FormReligion(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('religion-index'))
    else:
        form = FormReligion()

    context = {
        'form': form,
        'segment': 'religion',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='AGAMA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/religion_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='AGAMA')
def religion_update(request, _id):
    religion = Religion.objects.get(religion_id=_id)

    if request.POST:
        form = FormReligionUpdate(
            request.POST, request.FILES, instance=religion)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('religion-index'))
    else:
        form = FormReligionUpdate(instance=religion)

    context = {
        'form': form,
        'data': religion,
        'segment': 'religion',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='AGAMA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/religion_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='AGAMA')
def religion_delete(request, _id):
    religion = Religion.objects.get(religion_id=_id)
    try:
        religion.delete()
    except ProtectedError:
        form = FormReligionView(instance=religion)
        context = {
            'data': religion,
            'form': form,
            'segment': 'religion',
            'group_segment': 'master',
            'crud': 'view',
            'message': 'Agama ini sudah dipakai pada data santri dan tidak bisa dihapus.',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
                'menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id,
                                    menu_id='AGAMA') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/religion_view.html', context)

    return HttpResponseRedirect(reverse('religion-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='AGAMA')
def religion_view(request, _id):
    religion = Religion.objects.get(religion_id=_id)
    form = FormReligionView(instance=religion)

    context = {
        'data': religion,
        'form': form,
        'segment': 'religion',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='AGAMA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/religion_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='KABUPATEN-KOTA')
def district_import(request):
    return _master_import_view(request, 'district')


@login_required(login_url='/login/')
@role_required(allowed_roles='KABUPATEN-KOTA')
def district_index(request):
    districts = District.objects.all().order_by('district_name')

    context = {
        'data': districts,
        'segment': 'district',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='KABUPATEN-KOTA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/district_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='KABUPATEN-KOTA')
def district_add(request):
    if request.POST:
        form = FormDistrict(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('district-index'))
    else:
        form = FormDistrict()

    context = {
        'form': form,
        'segment': 'district',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='KABUPATEN-KOTA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/district_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='KABUPATEN-KOTA')
def district_update(request, _id):
    district = District.objects.get(district_id=_id)

    if request.POST:
        form = FormDistrictUpdate(
            request.POST, request.FILES, instance=district)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('district-index'))
    else:
        form = FormDistrictUpdate(instance=district)

    context = {
        'form': form,
        'data': district,
        'segment': 'district',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='KABUPATEN-KOTA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/district_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='KABUPATEN-KOTA')
def district_delete(request, _id):
    district = District.objects.get(district_id=_id)
    try:
        district.delete()
    except ProtectedError:
        form = FormDistrictView(instance=district)
        context = {
            'data': district,
            'form': form,
            'segment': 'district',
            'group_segment': 'master',
            'crud': 'view',
            'message': 'Kabupaten/Kota ini sudah dipakai pada data lain dan tidak bisa dihapus.',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
                'menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id,
                                    menu_id='KABUPATEN-KOTA') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/district_view.html', context)

    return HttpResponseRedirect(reverse('district-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='KABUPATEN-KOTA')
def district_view(request, _id):
    district = District.objects.get(district_id=_id)
    form = FormDistrictView(instance=district)

    context = {
        'data': district,
        'form': form,
        'segment': 'district',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='KABUPATEN-KOTA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/district_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='TAHUN-AJARAN')
def school_year_index(request):
    school_years = SchoolYear.objects.all().order_by('-school_year_name')

    context = {
        'data': school_years,
        'segment': 'school-year',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='TAHUN-AJARAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/school_year_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='TAHUN-AJARAN')
def school_year_add(request):
    if request.POST:
        form = FormSchoolYear(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('school-year-index'))
    else:
        form = FormSchoolYear()

    context = {
        'form': form,
        'segment': 'school-year',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='TAHUN-AJARAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/school_year_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='TAHUN-AJARAN')
def school_year_update(request, _id):
    school_year = SchoolYear.objects.get(school_year_id=_id)

    if request.POST:
        form = FormSchoolYearUpdate(
            request.POST, request.FILES, instance=school_year)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('school-year-index'))
    else:
        form = FormSchoolYearUpdate(instance=school_year)

    context = {
        'form': form,
        'data': school_year,
        'segment': 'school-year',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='TAHUN-AJARAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/school_year_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='TAHUN-AJARAN')
def school_year_delete(request, _id):
    school_year = SchoolYear.objects.get(school_year_id=_id)
    try:
        school_year.delete()
    except ProtectedError:
        form = FormSchoolYearView(instance=school_year)
        context = {
            'data': school_year,
            'form': form,
            'segment': 'school-year',
            'group_segment': 'master',
            'crud': 'view',
            'message': 'Tahun Ajaran ini sudah dipakai pada data lain dan tidak bisa dihapus.',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
                'menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id,
                                    menu_id='TAHUN-AJARAN') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/school_year_view.html', context)

    return HttpResponseRedirect(reverse('school-year-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='TAHUN-AJARAN')
def school_year_view(request, _id):
    school_year = SchoolYear.objects.get(school_year_id=_id)
    form = FormSchoolYearView(instance=school_year)

    context = {
        'data': school_year,
        'form': form,
        'segment': 'school-year',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='TAHUN-AJARAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/school_year_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='KECAMATAN')
def sub_district_import(request):
    return _master_import_view(request, 'sub_district')


@login_required(login_url='/login/')
@role_required(allowed_roles='KECAMATAN')
def sub_district_index(request):
    sub_districts = SubDistrict.objects.all().order_by('sub_district_name')

    context = {
        'data': sub_districts,
        'segment': 'sub-district',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='KECAMATAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/sub_district_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='KECAMATAN')
def sub_district_add(request):
    if request.POST:
        form = FormSubDistrict(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('sub-district-index'))
    else:
        form = FormSubDistrict()

    context = {
        'form': form,
        'segment': 'sub-district',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='KECAMATAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/sub_district_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='KECAMATAN')
def sub_district_update(request, _id):
    sub_district = SubDistrict.objects.get(sub_district_id=_id)

    if request.POST:
        form = FormSubDistrictUpdate(
            request.POST, request.FILES, instance=sub_district)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('sub-district-index'))
    else:
        form = FormSubDistrictUpdate(instance=sub_district)

    context = {
        'form': form,
        'data': sub_district,
        'segment': 'sub-district',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='KECAMATAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/sub_district_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='KECAMATAN')
def sub_district_delete(request, _id):
    sub_district = SubDistrict.objects.get(sub_district_id=_id)
    try:
        sub_district.delete()
    except ProtectedError:
        form = FormSubDistrictView(instance=sub_district)
        context = {
            'data': sub_district,
            'form': form,
            'segment': 'sub-district',
            'group_segment': 'master',
            'crud': 'view',
            'message': 'Kecamatan ini sudah dipakai pada data lain dan tidak bisa dihapus.',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
                'menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id,
                                    menu_id='KECAMATAN') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/sub_district_view.html', context)

    return HttpResponseRedirect(reverse('sub-district-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='KECAMATAN')
def sub_district_view(request, _id):
    sub_district = SubDistrict.objects.get(sub_district_id=_id)
    form = FormSubDistrictView(instance=sub_district)

    context = {
        'data': sub_district,
        'form': form,
        'segment': 'sub-district',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='KECAMATAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/sub_district_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DESA-KELURAHAN')
def village_import(request):
    return _master_import_view(request, 'village')


@login_required(login_url='/login/')
@role_required(allowed_roles='DESA-KELURAHAN')
def village_index(request):
    context = {
        'data': [],
        'segment': 'village',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DESA-KELURAHAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/village_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DESA-KELURAHAN')
def village_data(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 25))
    search_value = request.GET.get('search[value]', '').strip()
    order_column = request.GET.get('order[0][column]', '1')
    order_dir = request.GET.get('order[0][dir]', 'asc')

    queryset = Village.objects.all()
    total_count = queryset.count()

    if search_value:
        queryset = queryset.filter(village_name__icontains=search_value)

    filtered_count = queryset.count()

    order_map = {
        '0': 'village_id',
        '1': 'village_name',
    }
    order_field = order_map.get(order_column, 'village_name')
    if order_dir == 'desc':
        order_field = '-' + order_field

    queryset = queryset.order_by(order_field)
    rows = queryset[start:start + length]

    data = [
        {
            'id': item.village_id,
            'name': item.village_name,
            'url': reverse('village-view', args=[item.village_id])
        }
        for item in rows
    ]

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_count,
        'recordsFiltered': filtered_count,
        'data': data,
    })


@login_required(login_url='/login/')
@role_required(allowed_roles='DESA-KELURAHAN')
def village_add(request):
    if request.POST:
        form = FormVillage(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('village-index'))
    else:
        form = FormVillage()

    context = {
        'form': form,
        'segment': 'village',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DESA-KELURAHAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/village_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DESA-KELURAHAN')
def village_update(request, _id):
    village = Village.objects.get(village_id=_id)

    if request.POST:
        form = FormVillageUpdate(request.POST, request.FILES, instance=village)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('village-index'))
    else:
        form = FormVillageUpdate(instance=village)

    context = {
        'form': form,
        'data': village,
        'segment': 'village',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DESA-KELURAHAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/village_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DESA-KELURAHAN')
def village_delete(request, _id):
    village = Village.objects.get(village_id=_id)
    try:
        village.delete()
    except ProtectedError:
        form = FormVillageView(instance=village)
        context = {
            'data': village,
            'form': form,
            'segment': 'village',
            'group_segment': 'master',
            'crud': 'view',
            'message': 'Desa/Kelurahan ini sudah dipakai pada data lain dan tidak bisa dihapus.',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
                'menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id,
                                    menu_id='DESA-KELURAHAN') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/village_view.html', context)

    return HttpResponseRedirect(reverse('village-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='DESA-KELURAHAN')
def village_view(request, _id):
    village = Village.objects.get(village_id=_id)
    form = FormVillageView(instance=village)

    context = {
        'data': village,
        'form': form,
        'segment': 'village',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DESA-KELURAHAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/village_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def sub_district_options(request):
    district_id = request.GET.get('district_id')
    if not district_id:
        return JsonResponse({'results': []})

    sub_districts = SubDistrict.objects.filter(district_id=district_id).order_by(
        'sub_district_name')
    return JsonResponse({
        'results': [
            {'id': item.sub_district_id, 'name': item.sub_district_name}
            for item in sub_districts
        ]
    })


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def village_options(request):
    sub_district_id = request.GET.get('sub_district_id')
    if not sub_district_id:
        return JsonResponse({'results': []})

    villages = Village.objects.filter(sub_district_id=sub_district_id).order_by(
        'village_name')
    return JsonResponse({
        'results': [
            {'id': item.village_id, 'name': item.village_name}
            for item in villages
        ]
    })


@login_required(login_url='/login/')
def district_list(request):
    districts = District.objects.all().order_by('district_name')
    return JsonResponse([
        {'id': item.district_id, 'name': item.district_name}
        for item in districts
    ], safe=False)


@login_required(login_url='/login/')
def district_data(request):
    """Server-side DataTable endpoint for District (Kabupaten/Kota) picker."""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 25))
    search_value = request.GET.get('search[value]', '').strip()
    order_column = request.GET.get('order[0][column]', '0')
    order_dir = request.GET.get('order[0][dir]', 'asc')

    queryset = District.objects.all()
    total_count = queryset.count()

    if search_value:
        queryset = queryset.filter(district_name__icontains=search_value)

    filtered_count = queryset.count()

    order_field = 'district_name' if order_dir == 'asc' else '-district_name'
    queryset = queryset.order_by(order_field)
    rows = queryset[start:start + length]

    data = [
        {'id': item.district_id, 'name': item.district_name}
        for item in rows
    ]

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_count,
        'recordsFiltered': filtered_count,
        'data': data,
    })


@login_required(login_url='/login/')
def sub_district_list(request):
    sub_districts = SubDistrict.objects.all().order_by('sub_district_name')
    return JsonResponse([
        {'id': item.sub_district_id, 'name': item.sub_district_name}
        for item in sub_districts
    ], safe=False)


@login_required(login_url='/login/')
def sub_district_data(request):
    """Server-side DataTable endpoint for SubDistrict (Kecamatan) picker."""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 25))
    search_value = request.GET.get('search[value]', '').strip()
    order_column = request.GET.get('order[0][column]', '0')
    order_dir = request.GET.get('order[0][dir]', 'asc')

    queryset = SubDistrict.objects.all()
    total_count = queryset.count()

    if search_value:
        queryset = queryset.filter(sub_district_name__icontains=search_value)

    filtered_count = queryset.count()

    order_field = 'sub_district_name' if order_dir == 'asc' else '-sub_district_name'
    queryset = queryset.order_by(order_field)
    rows = queryset[start:start + length]

    data = [
        {'id': item.sub_district_id, 'name': item.sub_district_name}
        for item in rows
    ]

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_count,
        'recordsFiltered': filtered_count,
        'data': data,
    })


@login_required(login_url='/login/')
def village_list(request):
    villages = Village.objects.all().order_by('village_name')
    return JsonResponse([
        {'id': item.village_id, 'name': item.village_name}
        for item in villages
    ], safe=False)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def district_autocomplete(request):
    term = request.GET.get('term', '')
    districts = District.objects.filter(
        district_name__icontains=term).order_by('district_name')[:10]
    return JsonResponse([{'id': district.pk, 'text': district.district_name} for district in districts], safe=False)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def sub_district_autocomplete(request):
    term = request.GET.get('term', '')
    sub_districts = SubDistrict.objects.filter(
        sub_district_name__icontains=term).order_by('sub_district_name')[:10]
    return JsonResponse([{'id': sub_district.pk, 'text': sub_district.sub_district_name} for sub_district in sub_districts], safe=False)


@login_required(login_url='/login/')
@role_required(allowed_roles='DATA-SANTRI')
def village_autocomplete(request):
    term = request.GET.get('term', '')
    villages = Village.objects.filter(
        village_name__icontains=term).order_by('village_name')[:10]
    return JsonResponse([{'id': village.pk, 'text': village.village_name} for village in villages], safe=False)


@login_required(login_url='/login/')
@role_required(allowed_roles='ASRAMA')
def hostel_index(request):
    hostels = Hostel.objects.all().order_by('hostel_name')

    context = {
        'data': hostels,
        'segment': 'asrama',
        'group_segment': 'keasramaan',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='ASRAMA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/hostel_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='ASRAMA')
def hostel_add(request):
    if request.POST:
        form = FormHostel(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('hostel-index'))
    else:
        form = FormHostel()

    context = {
        'form': form,
        'segment': 'asrama',
        'group_segment': 'keasramaan',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='ASRAMA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/hostel_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='ASRAMA')
def hostel_update(request, _id):
    hostel = Hostel.objects.get(hostel_id=_id)

    if request.POST:
        form = FormHostelUpdate(
            request.POST, request.FILES, instance=hostel)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('hostel-index'))
    else:
        form = FormHostelUpdate(instance=hostel)

    context = {
        'form': form,
        'data': hostel,
        'segment': 'asrama',
        'group_segment': 'keasramaan',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='ASRAMA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/hostel_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='ASRAMA')
def hostel_delete(request, _id):
    hostel = Hostel.objects.get(hostel_id=_id)
    try:
        hostel.delete()
    except ProtectedError:
        form = FormHostelView(instance=hostel)
        context = {
            'data': hostel,
            'form': form,
            'segment': 'asrama',
            'group_segment': 'keasramaan',
            'crud': 'view',
            'message': 'Asrama ini sudah dipakai pada data santri dan tidak bisa dihapus.',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
                'menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id,
                                    menu_id='ASRAMA') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/hostel_view.html', context)

    return HttpResponseRedirect(reverse('hostel-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='ASRAMA')
def hostel_view(request, _id):
    hostel = Hostel.objects.get(hostel_id=_id)
    form = FormHostelView(instance=hostel)

    context = {
        'data': hostel,
        'form': form,
        'segment': 'asrama',
        'group_segment': 'keasramaan',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='ASRAMA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/hostel_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JENIS-TINGGAL')
def residence_type_index(request):
    residence_types = ResidenceType.objects.all().order_by('residence_type_name')

    context = {
        'data': residence_types,
        'segment': 'residence-type',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='JENIS-TINGGAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/residence_type_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JENIS-TINGGAL')
def residence_type_add(request):
    if request.POST:
        form = FormResidenceType(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('residence-type-index'))
    else:
        form = FormResidenceType()

    context = {
        'form': form,
        'segment': 'residence-type',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='JENIS-TINGGAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/residence_type_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JENIS-TINGGAL')
def residence_type_update(request, _id):
    residence_type = ResidenceType.objects.get(residence_type_id=_id)

    if request.POST:
        form = FormResidenceTypeUpdate(
            request.POST, request.FILES, instance=residence_type)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('residence-type-index'))
    else:
        form = FormResidenceTypeUpdate(instance=residence_type)

    context = {
        'form': form,
        'data': residence_type,
        'segment': 'residence-type',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='JENIS-TINGGAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/residence_type_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JENIS-TINGGAL')
def residence_type_delete(request, _id):
    residence_type = ResidenceType.objects.get(residence_type_id=_id)
    try:
        residence_type.delete()
    except ProtectedError:
        form = FormResidenceTypeView(instance=residence_type)
        context = {
            'data': residence_type,
            'form': form,
            'segment': 'residence-type',
            'group_segment': 'master',
            'crud': 'view',
            'message': 'Jenis tinggal ini sudah dipakai pada data santri dan tidak bisa dihapus.',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
                'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='JENIS-TINGGAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/residence_type_view.html', context)


# ============================================================
# AJAX: GradeSubject by Grade
# ============================================================

@login_required(login_url='/login/')
def grade_subject_by_grade(request):
    grade_id = request.GET.get('grade_id')

    # Filter: hanya GradeSubject yang belum punya guru
    grade_subjects_with_teacher = TeacherSubject.objects.values_list('grade_subject', flat=True).distinct()

    grade_subjects = GradeSubject.objects.filter(
        grade_id=grade_id
    ).exclude(
        grade_subject_id__in=grade_subjects_with_teacher
    ).select_related('subject').order_by('subject__subject_name')

    data = [
        {
            'id': gs.grade_subject_id,
            'text': gs.subject.subject_name
        }
        for gs in grade_subjects
    ]
    return JsonResponse({'results': data})


def available_subjects_by_grade(request):
    """AJAX endpoint: return subjects not yet registered for a given grade."""
    grade_id = request.GET.get('grade_id')
    grade_subject_id = request.GET.get('grade_subject_id')
    if not grade_id:
        return JsonResponse({'results': []})

    registered_subject_ids = GradeSubject.objects.filter(
        grade_id=grade_id
    )
    
    # Exclude current grade_subject_id when updating
    if grade_subject_id:
        registered_subject_ids = registered_subject_ids.exclude(
            grade_subject_id=grade_subject_id
        )
    
    registered_subject_ids = registered_subject_ids.values_list('subject_id', flat=True)

    subjects = Subject.objects.select_related('group').exclude(
        subject_id__in=registered_subject_ids
    ).order_by('subject_name')

    data = [
        {'id': s.subject_id, 'text': s.subject_name}
        for s in subjects
    ]
    return JsonResponse({'results': data})


# ============================================================
# TeacherSubject CRUD (Guru Per Mapel)
# ============================================================

@login_required(login_url='/login/')
@role_required(allowed_roles='GURU-MAPEL')
def teacher_subject_index(request):
    teacher_subjects = TeacherSubject.objects.select_related(
        'grade_subject__grade__level', 'grade_subject__grade__school_year',
        'grade_subject__subject', 'teacher__user'
    ).all().order_by('grade_subject__grade__grade', 'grade_subject__grade__sub_grade', 'grade_subject__subject__subject_name')

    context = {
        'data': teacher_subjects,
        'segment': 'guru-mapel',
        'group_segment': 'kurikulum',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GURU-MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_subject_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GURU-MAPEL')
def teacher_subject_add(request):
    if request.POST:
        form = FormTeacherSubject(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('teacher-subject-index'))
    else:
        form = FormTeacherSubject()

    # Filter grades: hanya kelas yang masih punya mapel tanpa guru
    # 1. Dapatkan semua GradeSubject yang sudah punya guru
    grade_subjects_with_teacher = TeacherSubject.objects.values_list('grade_subject', flat=True).distinct()

    # 2. Dapatkan Grade IDs yang memiliki setidaknya satu GradeSubject tanpa guru
    grades_with_subjects_without_teacher = Grade.objects.filter(
        gradesubject__grade_subject_id__in=GradeSubject.objects.exclude(
            grade_subject_id__in=grade_subjects_with_teacher
        ).values_list('grade_subject_id', flat=True)
    ).distinct()

    grades = grades_with_subjects_without_teacher.select_related(
        'level', 'school_year').order_by('grade', 'sub_grade')

    context = {
        'form': form,
        'grades': grades,
        'segment': 'guru-mapel',
        'group_segment': 'kurikulum',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GURU-MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_subject_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GURU-MAPEL')
def teacher_subject_update(request, _id):
    teacher_subject = TeacherSubject.objects.get(teacher_subject_id=_id)

    if request.POST:
        form = FormTeacherSubjectUpdate(
            request.POST, request.FILES, instance=teacher_subject)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('teacher-subject-index'))
    else:
        form = FormTeacherSubjectUpdate(instance=teacher_subject)

    # Filter grades: kelas yang masih punya mapel tanpa guru + kelas dari data yang sedang diedit
    grade_subjects_with_teacher = TeacherSubject.objects.exclude(
        teacher_subject_id=_id
    ).values_list('grade_subject', flat=True).distinct()

    # Grade dari teacher_subject yang sedang diedit (selalu tampilkan)
    current_grade_id = teacher_subject.grade_subject.grade_id

    grades = Grade.objects.filter(
        Q(gradesubject__grade_subject_id__in=GradeSubject.objects.exclude(
            grade_subject_id__in=grade_subjects_with_teacher
        ).values_list('grade_subject_id', flat=True)) |
        Q(grade_id=current_grade_id)
    ).distinct().select_related(
        'level', 'school_year').order_by('grade', 'sub_grade')

    context = {
        'form': form,
        'data': teacher_subject,
        'grades': grades,
        'segment': 'guru-mapel',
        'group_segment': 'kurikulum',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GURU-MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_subject_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GURU-MAPEL')
def teacher_subject_delete(request, _id):
    teacher_subject = TeacherSubject.objects.get(teacher_subject_id=_id)
    try:
        teacher_subject.delete()
    except ProtectedError:
        form = FormTeacherSubjectView(instance=teacher_subject)
        context = {
            'data': teacher_subject,
            'form': form,
            'segment': 'guru-mapel',
            'group_segment': 'kurikulum',
            'crud': 'view',
            'message': 'Data penugasan guru ini sudah dipakai pada data lain dan tidak bisa dihapus.',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
                'menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id,
                                    menu_id='GURU-MAPEL') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/teacher_subject_view.html', context)

    return HttpResponseRedirect(reverse('teacher-subject-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='GURU-MAPEL')
def teacher_subject_view(request, _id):
    teacher_subject = TeacherSubject.objects.get(teacher_subject_id=_id)
    form = FormTeacherSubjectView(instance=teacher_subject)

    context = {
        'data': teacher_subject,
        'form': form,
        'segment': 'guru-mapel',
        'group_segment': 'kurikulum',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GURU-MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_subject_view.html', context)


# ============================================================
# GradeSubject CRUD (Mapel Per Kelas)
# ============================================================

@login_required(login_url='/login/')
@role_required(allowed_roles='MAPEL-KELAS')
def grade_subject_index(request):
    grade_subjects = GradeSubject.objects.select_related(
        'grade__level', 'grade__school_year', 'subject'
    ).prefetch_related('teacher_subjects__teacher__user').all()

    grade_id = request.GET.get('grade_id')
    semester = request.GET.get('semester')

    if grade_id:
        grade_subjects = grade_subjects.filter(grade__grade_id=grade_id)
    if semester:
        grade_subjects = grade_subjects.filter(grade__semester=semester)

    grade_subjects = grade_subjects.order_by(
        'grade__grade', 'grade__sub_grade', 'subject__subject_name')

    grades = Grade.objects.select_related(
        'level', 'school_year').order_by('grade', 'sub_grade')

    context = {
        'data': grade_subjects,
        'grades': grades,
        'selected_grade': grade_id,
        'selected_semester': semester,
        'segment': 'mapel-kelas',
        'group_segment': 'kurikulum',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='MAPEL-KELAS') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/grade_subject_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='MAPEL-KELAS')
def grade_subject_add(request):
    if request.POST:
        form = FormGradeSubject(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('grade-subject-index'))
    else:
        form = FormGradeSubject()

    context = {
        'form': form,
        'segment': 'mapel-kelas',
        'group_segment': 'kurikulum',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='MAPEL-KELAS') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/grade_subject_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='MAPEL-KELAS')
def grade_subject_update(request, _id):
    grade_subject = GradeSubject.objects.get(grade_subject_id=_id)

    if request.POST:
        form = FormGradeSubjectUpdate(
            request.POST, request.FILES, instance=grade_subject)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('grade-subject-index'))
    else:
        form = FormGradeSubjectUpdate(instance=grade_subject)

    context = {
        'form': form,
        'data': grade_subject,
        'segment': 'mapel-kelas',
        'group_segment': 'kurikulum',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='MAPEL-KELAS') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/grade_subject_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='MAPEL-KELAS')
def grade_subject_delete(request, _id):
    grade_subject = GradeSubject.objects.get(grade_subject_id=_id)
    try:
        grade_subject.delete()
    except ProtectedError:
        form = FormGradeSubjectView(instance=grade_subject)
        context = {
            'data': grade_subject,
            'form': form,
            'segment': 'mapel-kelas',
            'group_segment': 'kurikulum',
            'crud': 'view',
            'message': 'Data mapel per kelas ini sudah dipakai pada data lain dan tidak bisa dihapus.',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
                'menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id,
                                    menu_id='MAPEL-KELAS') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/grade_subject_view.html', context)

    return HttpResponseRedirect(reverse('grade-subject-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='MAPEL-KELAS')
def grade_subject_view(request, _id):
    grade_subject = GradeSubject.objects.select_related(
        'grade__level', 'grade__school_year', 'subject'
    ).prefetch_related('teacher_subjects__teacher__user').get(grade_subject_id=_id)
    form = FormGradeSubjectView(instance=grade_subject)
    teachers = grade_subject.teacher_subjects.select_related('teacher__user').all()

    context = {
        'data': grade_subject,
        'form': form,
        'teachers': teachers,
        'segment': 'mapel-kelas',
        'group_segment': 'kurikulum',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='MAPEL-KELAS') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/grade_subject_view.html', context)

@login_required(login_url='/login/')
@role_required(allowed_roles='GROUP-MAPEL')
def subject_group_index(request):
    subject_groups = SubjectGroup.objects.all().order_by('group_code')

    context = {
        'data': subject_groups,
        'segment': 'group-mapel',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GROUP-MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/subject_group_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GROUP-MAPEL')
def subject_group_add(request):
    if request.POST:
        form = FormSubjectGroup(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('subject-group-index'))
    else:
        form = FormSubjectGroup()

    context = {
        'form': form,
        'segment': 'group-mapel',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GROUP-MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/subject_group_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GROUP-MAPEL')
def subject_group_update(request, _id):
    subject_group = SubjectGroup.objects.get(group_id=_id)

    if request.POST:
        form = FormSubjectGroupUpdate(
            request.POST, request.FILES, instance=subject_group)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('subject-group-index'))
    else:
        form = FormSubjectGroupUpdate(instance=subject_group)

    context = {
        'form': form,
        'data': subject_group,
        'segment': 'group-mapel',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GROUP-MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/subject_group_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='GROUP-MAPEL')
def subject_group_delete(request, _id):
    subject_group = SubjectGroup.objects.get(group_id=_id)
    try:
        subject_group.delete()
    except ProtectedError:
        form = FormSubjectGroupView(instance=subject_group)
        context = {
            'data': subject_group,
            'form': form,
            'segment': 'group-mapel',
            'group_segment': 'master',
            'crud': 'view',
            'message': 'Group ini sudah dipakai pada data mata pelajaran dan tidak bisa dihapus.',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
                'menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id,
                                    menu_id='GROUP-MAPEL') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/subject_group_view.html', context)

    return HttpResponseRedirect(reverse('subject-group-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='GROUP-MAPEL')
def subject_group_view(request, _id):
    subject_group = SubjectGroup.objects.get(group_id=_id)
    form = FormSubjectGroupView(instance=subject_group)

    context = {
        'data': subject_group,
        'form': form,
        'segment': 'group-mapel',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='GROUP-MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/subject_group_view.html', context)


# ============================================================
# Subject CRUD
# ============================================================

@login_required(login_url='/login/')
@role_required(allowed_roles='MAPEL')
def subject_index(request):
    subjects = Subject.objects.select_related('group').all().order_by('subject_name')

    context = {
        'data': subjects,
        'segment': 'mapel',
        'group_segment': 'kurikulum',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/subject_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='MAPEL')
def subject_add(request):
    if request.POST:
        form = FormSubject(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('subject-index'))
    else:
        form = FormSubject()

    context = {
        'form': form,
        'segment': 'mapel',
        'group_segment': 'kurikulum',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/subject_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='MAPEL')
def subject_update(request, _id):
    subject = Subject.objects.get(subject_id=_id)

    if request.POST:
        form = FormSubjectUpdate(
            request.POST, request.FILES, instance=subject)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('subject-index'))
    else:
        form = FormSubjectUpdate(instance=subject)

    context = {
        'form': form,
        'data': subject,
        'segment': 'mapel',
        'group_segment': 'kurikulum',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/subject_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='MAPEL')
def subject_delete(request, _id):
    subject = Subject.objects.get(subject_id=_id)
    try:
        subject.delete()
    except ProtectedError:
        form = FormSubjectView(instance=subject)
        context = {
            'data': subject,
            'form': form,
            'segment': 'mapel',
            'group_segment': 'kurikulum',
            'crud': 'view',
            'message': 'Mata pelajaran ini sudah dipakai pada data lain dan tidak bisa dihapus.',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
                'menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id,
                                    menu_id='MAPEL') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/subject_view.html', context)

    return HttpResponseRedirect(reverse('subject-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='MAPEL')
def subject_view(request, _id):
    subject = Subject.objects.get(subject_id=_id)
    form = FormSubjectView(instance=subject)

    context = {
        'data': subject,
        'form': form,
        'segment': 'mapel',
        'group_segment': 'kurikulum',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='MAPEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/subject_view.html', context)

    return HttpResponseRedirect(reverse('residence-type-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='JENIS-TINGGAL')
def residence_type_view(request, _id):
    residence_type = ResidenceType.objects.get(residence_type_id=_id)
    form = FormResidenceTypeView(instance=residence_type)

    context = {
        'data': residence_type,
        'form': form,
        'segment': 'residence-type',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='JENIS-TINGGAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/residence_type_view.html', context)


# =============================================================================
# SCHEDULE / JADWAL PELAJARAN VIEWS
# =============================================================================

# --- Room CRUD ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def room_index(request):
    rooms = Room.objects.all().order_by('room_name')
    context = {
        'data': rooms,
        'segment': 'ruangan',
        'group_segment': 'kurikulum',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='RUANGAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/room_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def room_add(request):
    if request.POST:
        form = FormRoom(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('room-index'))
    else:
        form = FormRoom()

    context = {
        'form': form,
        'segment': 'ruangan',
        'group_segment': 'kurikulum',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='RUANGAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/room_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def room_view(request, _id):
    room = Room.objects.get(room_id=_id)
    form = FormRoomView(instance=room)

    context = {
        'data': room,
        'form': form,
        'segment': 'ruangan',
        'group_segment': 'kurikulum',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='RUANGAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/room_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def room_update(request, _id):
    room = Room.objects.get(room_id=_id)
    if request.POST:
        form = FormRoomUpdate(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('room-index'))
    else:
        form = FormRoomUpdate(instance=room)

    context = {
        'data': room,
        'form': form,
        'segment': 'ruangan',
        'group_segment': 'kurikulum',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='RUANGAN') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/room_update.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def room_delete(request, _id):
    try:
        room = Room.objects.get(room_id=_id)
        room.delete()
    except ProtectedError:
        pass
    return HttpResponseRedirect(reverse('room-index'))


# --- Timetable CRUD ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_index(request):
    timetables = Timetable.objects.select_related('school_year').all().order_by('-entry_date')
    
    if timetables.exists():
        return HttpResponseRedirect(reverse('timetable-view', args=[timetables.first().timetable_id]))
    
    school_year = SchoolYear.objects.order_by('-school_year_name').first()
    timetable = Timetable.objects.create(
        name='Jadwal Pelajaran',
        school_year=school_year,
        status='draft'
    )
    return HttpResponseRedirect(reverse('timetable-view', args=[timetable.timetable_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_add(request):
    if request.POST:
        form = FormTimetable(request.POST)
        if form.is_valid():
            timetable = form.save()
            return HttpResponseRedirect(reverse('timetable-view', args=[timetable.timetable_id]))
    else:
        form = FormTimetable()

    context = {
        'form': form,
        'segment': 'jadwal',
        'group_segment': 'kurikulum',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='JADWAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/timetable_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_view(request, _id):
    timetable = Timetable.objects.select_related('school_year').get(timetable_id=_id)
    
    # Custom day order mapping
    day_order = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}
    periods = list(timetable.periods.all())
    periods.sort(key=lambda p: (day_order.get(p.day, 99), p.order))
    
    lessons = timetable.lessons.select_related(
        'grade_subject__grade', 'grade_subject__subject', 'teacher__user'
    ).all()
    slots = timetable.slots.select_related(
        'lesson__grade_subject__grade', 'lesson__grade_subject__subject',
        'lesson__teacher__user', 'period', 'room'
    ).all()
    
    # Data dari Mapel Per Kelas (GradeSubject) - filter by school_year + semester timetable
    grade_subjects = GradeSubject.objects.select_related(
        'grade__school_year', 'subject', 'room'
    ).prefetch_related('teacher_subjects__teacher__user').filter(
        grade__school_year=timetable.school_year,
        grade__semester=timetable.semester,
    ).order_by('grade__grade', 'grade__sub_grade', 'subject__subject_name')
    
    # Data guru - hanya guru yang punya TeacherSubject di school_year + semester ini
    teacher_ids = TeacherSubject.objects.filter(
        grade_subject__grade__school_year=timetable.school_year,
        grade_subject__grade__semester=timetable.semester,
    ).values_list('teacher_id', flat=True).distinct()
    teachers = Teacher.objects.select_related('user').filter(
        teacher_id__in=teacher_ids
    ).order_by('user__username')
    teacher_availabilities = TeacherAvailability.objects.filter(
        timetable=timetable
    ).select_related('teacher', 'period')
    
    # Organize availability data by teacher_id -> day -> [period_ids]
    # Convert teacher_id keys to strings for JSON compatibility
    availability_data = {}
    for avail in teacher_availabilities:
        teacher_id = str(avail.teacher_id)
        day = avail.day
        if teacher_id not in availability_data:
            availability_data[teacher_id] = {}
        if day not in availability_data[teacher_id]:
            availability_data[teacher_id][day] = []
        if avail.period_id and avail.is_available:
            availability_data[teacher_id][day].append(avail.period_id)
    
    # Data ruangan dan ketersediaan
    rooms = Room.objects.all().order_by('room_name')
    room_availabilities = RoomAvailability.objects.filter(
        timetable=timetable
    ).select_related('room', 'period')
    
    # Organize room availability data by room_id -> day -> [period_ids]
    room_availability_data = {}
    for avail in room_availabilities:
        room_id = str(avail.room_id)
        day = avail.day
        if room_id not in room_availability_data:
            room_availability_data[room_id] = {}
        if day not in room_availability_data[room_id]:
            room_availability_data[room_id][day] = []
        if avail.period_id and avail.is_available:
            room_availability_data[room_id][day].append(avail.period_id)
    
    # Data kelas - filter by school_year + semester timetable
    grades = Grade.objects.filter(
        school_year=timetable.school_year,
        semester=timetable.semester,
    ).order_by('grade', 'sub_grade')
    grade_availabilities = GradeAvailability.objects.filter(
        timetable=timetable
    ).select_related('grade', 'period')
    
    # Organize grade availability data by grade_id -> day -> [period_ids]
    grade_availability_data = {}
    for avail in grade_availabilities:
        grade_id = str(avail.grade_id)
        day = avail.day
        if grade_id not in grade_availability_data:
            grade_availability_data[grade_id] = {}
        if day not in grade_availability_data[grade_id]:
            grade_availability_data[grade_id][day] = []
        if avail.period_id and avail.is_available:
            grade_availability_data[grade_id][day].append(avail.period_id)
    
    # Periods data for JSON serialization - group by order
    periods_by_order = {}
    for p in periods:
        if p.order not in periods_by_order:
            periods_by_order[p.order] = {
                'order': p.order,
                'name': p.break_name if p.is_break else f"Periode {p.order}",
                'start_time': p.start_time.strftime('%H.%M'),
                'end_time': p.end_time.strftime('%H.%M'),
                'is_break': p.is_break,
                'days': {}
            }
        periods_by_order[p.order]['days'][p.day] = p.period_id
    
    periods_json = list(periods_by_order.values())

    # --- Workload Analysis ---
    # Total unique non-break periods in this timetable
    total_periods = len(set(
        (p.day, p.order) for p in periods if not p.is_break
    ))

    # Count scheduled slots per grade
    grade_slot_counts = {}
    for slot in slots:
        gid = slot.lesson.grade_subject.grade.grade_id
        grade_slot_counts[gid] = grade_slot_counts.get(gid, 0) + 1

    # Count scheduled slots per teacher
    teacher_slot_counts = {}
    for slot in slots:
        tid = slot.lesson.teacher.teacher_id
        teacher_slot_counts[tid] = teacher_slot_counts.get(tid, 0) + 1

    # Count scheduled slots per room
    room_slot_counts = {}
    for slot in slots:
        if slot.room_id:
            room_slot_counts[slot.room_id] = room_slot_counts.get(slot.room_id, 0) + 1

    # Time-off periods per grade (periods marked unavailable via GradeAvailability)
    grade_timeoff_counts = {}
    for avail in GradeAvailability.objects.filter(timetable=timetable, is_available=False):
        gid = avail.grade_id
        if avail.period_id:
            grade_timeoff_counts[gid] = grade_timeoff_counts.get(gid, 0) + 1

    # Time-off periods per teacher
    teacher_timeoff_counts = {}
    for avail in TeacherAvailability.objects.filter(timetable=timetable, is_available=False):
        tid = avail.teacher_id
        if avail.period_id:
            teacher_timeoff_counts[tid] = teacher_timeoff_counts.get(tid, 0) + 1

    # Time-off periods per room
    room_timeoff_counts = {}
    for avail in RoomAvailability.objects.filter(timetable=timetable, is_available=False):
        rid = avail.room_id
        if avail.period_id:
            room_timeoff_counts[rid] = room_timeoff_counts.get(rid, 0) + 1

    # Build workload lists
    grade_workload = []
    for g in grades:
        scheduled = grade_slot_counts.get(g.grade_id, 0)
        timeoff = grade_timeoff_counts.get(g.grade_id, 0)
        available = total_periods - timeoff
        util = round((scheduled / total_periods) * 100, 1) if total_periods > 0 else 0
        grade_workload.append({
            'name': f"{g.grade}{g.sub_grade or ''}",
            'scheduled': scheduled,
            'available': available,
            'total': total_periods,
            'timeoff': timeoff,
            'utilization': util,
        })

    teacher_workload = []
    for t in teachers:
        scheduled = teacher_slot_counts.get(t.teacher_id, 0)
        timeoff = teacher_timeoff_counts.get(t.teacher_id, 0)
        available = total_periods - timeoff
        util = round((scheduled / total_periods) * 100, 1) if total_periods > 0 else 0
        teacher_workload.append({
            'name': t.user.username,
            'scheduled': scheduled,
            'available': available,
            'total': total_periods,
            'timeoff': timeoff,
            'utilization': util,
        })

    room_workload = []
    for r in rooms:
        scheduled = room_slot_counts.get(r.room_id, 0)
        timeoff = room_timeoff_counts.get(r.room_id, 0)
        available = total_periods - timeoff
        util = round((scheduled / total_periods) * 100, 1) if total_periods > 0 else 0
        if scheduled > 0:
            room_workload.append({
                'name': r.room_name,
                'scheduled': scheduled,
                'available': available,
                'total': total_periods,
                'timeoff': timeoff,
                'utilization': util,
            })

    context = {
        'data': timetable,
        'periods': periods,
        'lessons': lessons,
        'slots': slots,
        'grade_subjects': grade_subjects,
        'teachers': teachers,
        'availability_data': availability_data,
        'rooms': rooms,
        'room_availability_data': room_availability_data,
        'grades': grades,
        'grade_availability_data': grade_availability_data,
        'periods_json': periods_json,
        'day_choices': Period.DAY_CHOICES,
        'school_years': SchoolYear.objects.all().order_by('-school_year_name'),
        'grade_workload': grade_workload,
        'teacher_workload': teacher_workload,
        'room_workload': room_workload,
        'total_periods': total_periods,
        'segment': 'jadwal',
        'group_segment': 'kurikulum',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='JADWAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/timetable_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_update(request, _id):
    timetable = Timetable.objects.get(timetable_id=_id)
    if request.POST:
        form = FormTimetableUpdate(request.POST, instance=timetable)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('timetable-view', args=[_id]))
    else:
        form = FormTimetableUpdate(instance=timetable)

    context = {
        'data': timetable,
        'form': form,
        'segment': 'jadwal',
        'group_segment': 'kurikulum',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='JADWAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/timetable_update.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_delete(request, _id):
    try:
        timetable = Timetable.objects.get(timetable_id=_id)
        timetable.delete()
    except ProtectedError:
        pass
    return HttpResponseRedirect(reverse('timetable-index'))


# --- Save Teacher Availability (AJAX) ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_save_availability(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    try:
        data = json.loads(request.body)
        timetable_id = data.get('timetable_id')
        availabilities = data.get('availabilities', [])
        
        timetable = Timetable.objects.get(timetable_id=timetable_id)
        
        user = get_current_user()
        user_id = user.user_id if user else None

        # Delete existing availability for this teacher and timetable only
        target_teacher_id = None
        for avail in availabilities:
            tid = avail.get('teacher_id')
            if tid:
                target_teacher_id = int(tid)
                break
        
        if target_teacher_id:
            TeacherAvailability.objects.filter(timetable=timetable, teacher_id=target_teacher_id).delete()
        else:
            TeacherAvailability.objects.filter(timetable=timetable).delete()
        
        # Create new availability records
        created_count = 0
        for avail in availabilities:
            teacher_id = avail.get('teacher_id')
            day = avail.get('day')
            period_id = avail.get('period_id')
            is_available = avail.get('is_available', True)
            
            if teacher_id and day and period_id:
                TeacherAvailability.objects.create(
                    teacher_id=int(teacher_id),
                    timetable=timetable,
                    day=day,
                    period_id=int(period_id),
                    is_available=is_available,
                    entry_by=user_id,
                    entry_date=timezone.now()
                )
                created_count += 1
        
        return JsonResponse({'success': True, 'count': created_count})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_save_room_availability(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    try:
        data = json.loads(request.body)
        timetable_id = data.get('timetable_id')
        availabilities = data.get('availabilities', [])
        
        timetable = Timetable.objects.get(timetable_id=timetable_id)
        
        user = get_current_user()
        user_id = user.user_id if user else None

        # Delete existing availability for this room and timetable only
        target_room_id = None
        for avail in availabilities:
            rid = avail.get('room_id')
            if rid:
                target_room_id = int(rid)
                break
        
        if target_room_id:
            RoomAvailability.objects.filter(timetable=timetable, room_id=target_room_id).delete()
        else:
            RoomAvailability.objects.filter(timetable=timetable).delete()
        
        # Create new availability records
        created_count = 0
        for avail in availabilities:
            room_id = avail.get('room_id')
            day = avail.get('day')
            period_id = avail.get('period_id')
            is_available = avail.get('is_available', True)
            
            if room_id and day and period_id:
                RoomAvailability.objects.create(
                    room_id=int(room_id),
                    timetable=timetable,
                    day=day,
                    period_id=int(period_id),
                    is_available=is_available,
                    entry_by=user_id,
                    entry_date=timezone.now()
                )
                created_count += 1
        
        return JsonResponse({'success': True, 'count': created_count})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_save_grade_availability(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    try:
        data = json.loads(request.body)
        timetable_id = data.get('timetable_id')
        availabilities = data.get('availabilities', [])
        
        timetable = Timetable.objects.get(timetable_id=timetable_id)
        
        user = get_current_user()
        user_id = user.user_id if user else None

        # Delete existing availability for this grade and timetable only
        target_grade_id = None
        for avail in availabilities:
            gid = avail.get('grade_id')
            if gid:
                target_grade_id = gid
                break
        
        if target_grade_id:
            GradeAvailability.objects.filter(timetable=timetable, grade_id=target_grade_id).delete()
        else:
            GradeAvailability.objects.filter(timetable=timetable).delete()
        
        # Create new availability records
        created_count = 0
        for avail in availabilities:
            grade_id = avail.get('grade_id')
            day = avail.get('day')
            period_id = avail.get('period_id')
            is_available = avail.get('is_available', True)
            
            if grade_id and day and period_id:
                GradeAvailability.objects.create(
                    grade_id=grade_id,
                    timetable=timetable,
                    day=day,
                    period_id=int(period_id),
                    is_available=is_available,
                    entry_by=user_id,
                    entry_date=timezone.now()
                )
                created_count += 1
        
        return JsonResponse({'success': True, 'count': created_count})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# --- Timetable Grid View ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_grid(request, _id):
    timetable = Timetable.objects.get(timetable_id=_id)
    
    # Custom day order mapping
    day_order = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}
    periods = list(timetable.periods.all())
    periods.sort(key=lambda p: (day_order.get(p.day, 99), p.order))
    
    slots = timetable.slots.select_related(
        'lesson__grade_subject__grade', 'lesson__grade_subject__subject',
        'lesson__teacher__user', 'period', 'room'
    ).all()
    grades = Grade.objects.filter(
        school_year=timetable.school_year,
        semester=timetable.semester,
        gradesubject__teacher_subjects__isnull=False,
    ).distinct().order_by('grade', 'sub_grade')

    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    grid = {}
    for slot in slots:
        day = slot.period.day
        order = slot.period.order
        grade_key = f"{slot.lesson.grade_subject.grade.grade}{slot.lesson.grade_subject.grade.sub_grade or ''}"
        if grade_key not in grid:
            grid[grade_key] = {}
        if day not in grid[grade_key]:
            grid[grade_key][day] = {}
        grid[grade_key][day][order] = {
            'subject': slot.lesson.grade_subject.subject.subject_name,
            'teacher': slot.lesson.teacher.user.username,
            'room': slot.room.room_name if slot.room else '',
            'slot_id': slot.slot_id,
        }

    days_display = dict(Period.DAY_CHOICES)

    from django.db.models import Count

    # Count scheduled slots per (teacher, grade_subject)
    scheduled_counts = TimetableSlot.objects.filter(
        timetable=timetable
    ).values(
        'lesson__teacher__teacher_id',
        'lesson__grade_subject__grade_subject_id',
    ).annotate(
        cnt=Count('slot_id')
    )

    sched_map = {}
    for sc in scheduled_counts:
        key = (sc['lesson__teacher__teacher_id'], sc['lesson__grade_subject__grade_subject_id'])
        sched_map[key] = sc['cnt']

    # Find TeacherSubjects with remaining hours - filter by school_year + semester timetable
    ts_list = TeacherSubject.objects.select_related(
        'grade_subject__grade', 'grade_subject__subject', 'teacher__user'
    ).filter(
        grade_subject__grade__school_year=timetable.school_year,
        grade_subject__grade__semester=timetable.semester,
    )

    unscheduled_teacher_subjects = []
    for ts in ts_list:
        scheduled = sched_map.get((ts.teacher_id, ts.grade_subject_id), 0)
        remaining = ts.hours - scheduled
        if remaining > 0:
            ts.remaining_hours = remaining
            unscheduled_teacher_subjects.append(ts)
    unscheduled_teacher_subjects.sort(key=lambda x: (x.grade_subject.grade.grade, x.grade_subject.grade.sub_grade or '', x.grade_subject.subject.subject_name))

    # Build header data for merged day names - from sorted periods directly
    header_days = []  # [{code, name, colspan}, ...]
    current_day = None
    count = 0
    for p in periods:
        if p.day != current_day:
            if current_day is not None:
                header_days.append({
                    'code': current_day,
                    'name': days_display.get(current_day, current_day),
                    'colspan': count,
                })
            current_day = p.day
            count = 1
        else:
            count += 1
    if current_day is not None:
        header_days.append({
            'code': current_day,
            'name': days_display.get(current_day, current_day),
            'colspan': count,
        })

    # Generate color map for subjects
    subject_colors = {}
    color_palette = [
        {'bg': '#e3f2fd', 'border': '#1976d2', 'text': '#1565c0'},
        {'bg': '#e8f5e9', 'border': '#388e3c', 'text': '#2e7d32'},
        {'bg': '#fff3e0', 'border': '#f57c00', 'text': '#ef6c00'},
        {'bg': '#fce4ec', 'border': '#c2185b', 'text': '#c2185b'},
        {'bg': '#f3e5f5', 'border': '#7b1fa2', 'text': '#6a1b9a'},
        {'bg': '#e0f7fa', 'border': '#00838f', 'text': '#00838f'},
        {'bg': '#fffde7', 'border': '#f9a825', 'text': '#f57f17'},
        {'bg': '#e8eaf6', 'border': '#303f9f', 'text': '#283593'},
        {'bg': '#fbe9e7', 'border': '#d84315', 'text': '#bf360c'},
        {'bg': '#f1f8e9', 'border': '#689f38', 'text': '#558b2f'},
        {'bg': '#ede7f6', 'border': '#512da8', 'text': '#4527a0'},
        {'bg': '#e1f5fe', 'border': '#0277bd', 'text': '#01579b'},
    ]
    subjects = Subject.objects.all().order_by('subject_name')
    for idx, subject in enumerate(subjects):
        subject_colors[subject.subject_id] = color_palette[idx % len(color_palette)]

    # Unique periods for compact view (one column per time slot)
    seen_orders = set()
    periods_unique = []
    for p in periods:
        if p.order not in seen_orders:
            seen_orders.add(p.order)
            periods_unique.append(p)

    # Active days (days that have periods defined)
    active_days = sorted(set(p.day for p in periods), key=lambda d: day_order.get(d, 99))

    # Teachers that have slots in this timetable
    teachers = Teacher.objects.filter(
        lesson__slots__timetable=timetable
    ).distinct().order_by('user__username')

    # Rooms that have slots in this timetable
    rooms = Room.objects.filter(
        timetableslot__timetable=timetable
    ).distinct().order_by('room_name')

    context = {
        'data': timetable,
        'periods': periods,
        'periods_unique': periods_unique,
        'active_days': active_days,
        'header_days': header_days,
        'slots': slots,
        'grades': grades,
        'teachers': teachers,
        'rooms': rooms,
        'days_display': days_display,
        'subject_colors': subject_colors,
        'unscheduled_teacher_subjects': unscheduled_teacher_subjects,
        'segment': 'jadwal',
        'group_segment': 'kurikulum',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='JADWAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/timetable_grid.html', context)


# --- Automatic Scheduling Engine (AJAX) ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_generate(request, _id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    timetable = Timetable.objects.get(timetable_id=_id)

    if not timetable.school_year or not timetable.semester:
        return JsonResponse(
            {'error': 'Tahun ajaran dan semester harus diatur terlebih dahulu'},
            status=400)

    # Replace: clear existing slots
    timetable.slots.all().delete()

    # Custom day order mapping
    day_order = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

    # Group non-break periods per day, sorted by order
    periods_by_day = {}
    for p in timetable.periods.filter(is_break=False):
        periods_by_day.setdefault(p.day, []).append(p)
    for day in periods_by_day:
        periods_by_day[day].sort(key=lambda x: x.order)
    active_days = [d for d in day_order if d in periods_by_day]

    if not active_days:
        return JsonResponse(
            {'error': 'Belum ada periode jam pelajaran yang diatur'},
            status=400)

    break_orders_by_day = {d: set() for d in active_days}
    for p in timetable.periods.filter(is_break=True):
        if p.day in break_orders_by_day:
            break_orders_by_day[p.day].add(p.order)

    day_pos = {d: i for i, d in enumerate(active_days)}

    # PRD §8 step 1-2: explicit GradeSubject for (school_year, semester),
    # then TeacherSubject for those GradeSubjects
    grade_subjects = GradeSubject.objects.filter(
        grade__school_year=timetable.school_year,
        grade__semester=timetable.semester,
    ).select_related('grade', 'subject', 'room')
    teacher_subjects = list(TeacherSubject.objects.filter(
        grade_subject__in=grade_subjects,
    ).select_related(
        'grade_subject__grade', 'grade_subject__subject',
        'grade_subject__room', 'teacher__user',
    ).order_by('teacher_subject_id'))
    rooms = list(Room.objects.all())

    scheduled_count = 0
    total_needed = 0
    unscheduled_lessons = []

    for lesson_idx, ts in enumerate(teacher_subjects):
        slots_needed = ts.hours
        slots_assigned = 0
        total_needed += slots_needed

        grade = ts.grade_subject.grade
        grade_label = f"{grade.grade}{grade.sub_grade or ''}"
        teacher = ts.teacher
        grade_subject = ts.grade_subject

        # Get or create Lesson for this timetable
        lesson, created = Lesson.objects.get_or_create(
            timetable=timetable,
            grade_subject=grade_subject,
            teacher=teacher,
            defaults={'hours_per_week': slots_needed}
        )
        if not created and lesson.hours_per_week != slots_needed:
            lesson.hours_per_week = slots_needed
            lesson.save()

        # Round-robin: rotate starting day per lesson so hours spread evenly
        day_idx = lesson_idx % len(active_days)
        period_idx = {d: 0 for d in active_days}

        preferred_room = grade_subject.room

        def period_ok(day, period):
            # 1. Teacher conflict (same teacher, same period)
            if TimetableSlot.objects.filter(
                timetable=timetable,
                period=period,
                lesson__teacher=teacher,
            ).exists():
                return False
            # 2. Grade conflict (same grade, same period)
            if TimetableSlot.objects.filter(
                timetable=timetable,
                period=period,
                lesson__grade_subject__grade=grade,
            ).exists():
                return False
            # 3. Subject conflict (same grade_subject already at this period)
            if TimetableSlot.objects.filter(
                timetable=timetable,
                period=period,
                lesson__grade_subject=grade_subject,
            ).exists():
                return False
            # 4. Teacher availability (blacklist: skip only if is_available=False)
            if TeacherAvailability.objects.filter(
                timetable=timetable,
                teacher=teacher,
                day=day,
                is_available=False,
            ).filter(
                Q(period=period) | Q(period__isnull=True),
            ).exists():
                return False
            # 5. Grade availability (blacklist)
            if GradeAvailability.objects.filter(
                timetable=timetable,
                grade=grade,
                day=day,
                is_available=False,
            ).filter(
                Q(period=period) | Q(period__isnull=True),
            ).exists():
                return False
            return True

        def room_free(day, period, room):
            if TimetableSlot.objects.filter(
                timetable=timetable,
                period=period,
                room=room,
            ).exists():
                return False
            if RoomAvailability.objects.filter(
                timetable=timetable,
                room=room,
                day=day,
                is_available=False,
            ).filter(
                Q(period=period) | Q(period__isnull=True),
            ).exists():
                return False
            return True

        def pick_room(day, chunk):
            if preferred_room:
                if all(room_free(day, p, preferred_room) for p in chunk):
                    return preferred_room
                for room in rooms:
                    if all(room_free(day, p, room) for p in chunk):
                        return room
            return None

        def create_slots(chunk, room):
            nonlocal slots_assigned, scheduled_count
            for p in chunk:
                TimetableSlot.objects.create(
                    timetable=timetable,
                    lesson=lesson,
                    period=p,
                    room=room,
                    is_manual=False,
                )
                slots_assigned += 1
                scheduled_count += 1

        def contiguous(day, extra_orders):
            # No idle gaps: for this grade AND this teacher, occupied periods
            # on the day must be consecutive (istirahat between them is fine;
            # leading/trailing free periods are fine)
            extra = set(extra_orders)
            lookups = (
                Q(lesson__grade_subject__grade=grade),
                Q(lesson__teacher=teacher),
            )
            for lookup in lookups:
                orders = set(
                    TimetableSlot.objects.filter(
                        timetable=timetable,
                        period__day=day,
                    ).filter(lookup).values_list('period__order', flat=True)
                ) | extra
                if not orders:
                    continue
                idxs = [
                    i for i, p in enumerate(periods_by_day[day])
                    if p.order in orders
                ]
                if idxs and idxs[-1] - idxs[0] + 1 != len(idxs):
                    return False
            return True

        # Every subject: prefer 2-hour sessions (max 2 hours/day per subject);
        # sessions must not be split by istirahat (hard rule for lab rooms)
        hours_on_day = {d: 0 for d in active_days}
        is_lab = bool(
            preferred_room
            and 'lab' in (preferred_room.room_name or '').lower()
        )

        def no_break_between(day, a, b):
            return not any(
                a.order < o < b.order for o in break_orders_by_day[day]
            )

        def adjacent_session(day):
            i = day_pos[day]
            return (
                (i > 0 and hours_on_day[active_days[i - 1]] > 0)
                or (
                    i + 1 < len(active_days)
                    and hours_on_day[active_days[i + 1]] > 0
                )
            )

        def try_pair(no_break_only, allow_adjacent=False):
            nonlocal day_idx
            for _ in range(len(active_days)):
                day = active_days[day_idx % len(active_days)]
                day_idx += 1
                if hours_on_day[day] > 0:
                    continue
                if adjacent_session(day) and not allow_adjacent:
                    continue
                day_periods = periods_by_day[day]
                for i in range(len(day_periods) - 1):
                    a, b = day_periods[i], day_periods[i + 1]
                    if no_break_only and not no_break_between(day, a, b):
                        continue
                    if (
                        period_ok(day, a)
                        and period_ok(day, b)
                        and contiguous(day, (a.order, b.order))
                    ):
                        create_slots([a, b], pick_room(day, [a, b]))
                        hours_on_day[day] = 2
                        period_idx[day] = len(day_periods)
                        return True
            return False

        def try_single(allow_adjacent):
            nonlocal day_idx
            for _ in range(len(active_days)):
                day = active_days[day_idx % len(active_days)]
                day_idx += 1
                day_periods = periods_by_day[day]
                if hours_on_day[day] > 0:
                    period_idx[day] = len(day_periods)
                    continue
                if adjacent_session(day) and not allow_adjacent:
                    period_idx[day] = len(day_periods)
                    continue
                idx = period_idx[day]
                if idx >= len(day_periods):
                    continue
                period = day_periods[idx]
                period_idx[day] = idx + 1
                if not period_ok(day, period):
                    continue
                if not contiguous(day, (period.order,)):
                    continue
                create_slots([period], pick_room(day, [period]))
                hours_on_day[day] = 1
                period_idx[day] = len(day_periods)
                return True
            return False

        def singles_phase(allow_adjacent, reset):
            if reset:
                for d in active_days:
                    if hours_on_day[d] == 0:
                        period_idx[d] = 0
            while slots_assigned < slots_needed:
                if all(period_idx[d] >= len(periods_by_day[d]) for d in active_days):
                    break
                try_single(allow_adjacent)

        # Fill order — "setiap pelajaran tidak terjeda istirahat":
        #   A. sesi 2 jam TANPA istirahat (tier: hari non-adjacent, lalu adjacent)
        #   B. jam tunggal (fase ketat, lalu relaksasi hari-berurutan)
        #   C. sesi 2 jam MELEWATI istirahat — non-lab, last resort mutlak
        pairs_planned = slots_needed // 2
        pairs_done = 0

        # Phase A: no-break pairs only
        for _ in range(pairs_planned):
            if try_pair(no_break_only=True):
                pairs_done += 1
                continue
            if try_pair(no_break_only=True, allow_adjacent=True):
                pairs_done += 1
                continue
            break

        # Phase B: singles — strict, then relaxed adjacency
        singles_phase(allow_adjacent=False, reset=False)
        if slots_assigned < slots_needed:
            singles_phase(allow_adjacent=True, reset=True)

        # Phase C: crossing-istirahat pairs (non-lab only), then top up singles
        if slots_assigned < slots_needed and not is_lab:
            while (
                pairs_done < pairs_planned
                and slots_needed - slots_assigned >= 2
            ):
                if try_pair(no_break_only=False):
                    pairs_done += 1
                    continue
                if try_pair(no_break_only=False, allow_adjacent=True):
                    pairs_done += 1
                    continue
                break
            singles_phase(allow_adjacent=False, reset=False)
            if slots_assigned < slots_needed:
                singles_phase(allow_adjacent=True, reset=True)

        if slots_assigned < slots_needed:
            unscheduled_lessons.append({
                'lesson_id': lesson.lesson_id,
                'subject': grade_subject.subject.subject_name,
                'grade': grade_label,
                'teacher': teacher.user.username if teacher.user else str(teacher),
                'needed': slots_needed,
                'assigned': slots_assigned,
            })

    return JsonResponse({
        'success': True,
        'generated': scheduled_count,
        'failed': total_needed - scheduled_count,
        # Backward-compatible fields
        'scheduled_count': scheduled_count,
        'total_lessons': len(teacher_subjects),
        'unscheduled': unscheduled_lessons,
    })


# --- Manual Slot Move (AJAX) ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_move_slot(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        slot_id = data.get('slot_id')
        target_period_id = data.get('target_period_id')

        slot = TimetableSlot.objects.get(slot_id=slot_id)
        target_period = Period.objects.get(period_id=target_period_id)

        target_grade_id = data.get('target_grade_id')
        if target_grade_id and target_grade_id != slot.lesson.grade_subject.grade_id:
            return JsonResponse({'error': 'Kelas target tidak sesuai dengan kelas pelajaran ini'}, status=400)

        if target_period.is_break:
            return JsonResponse({'error': 'Tidak bisa dijadwalkan pada jam istirahat'}, status=400)

        # Check conflicts
        teacher_conflict = TimetableSlot.objects.filter(
            timetable=slot.timetable,
            period=target_period,
            lesson__teacher=slot.lesson.teacher
        ).exclude(slot_id=slot_id).exists()

        grade_conflict = TimetableSlot.objects.filter(
            timetable=slot.timetable,
            period=target_period,
            lesson__grade_subject__grade=slot.lesson.grade_subject.grade
        ).exclude(slot_id=slot_id).exists()

        if teacher_conflict:
            return JsonResponse({'error': 'Konflik guru pada periode ini'}, status=400)
        if grade_conflict:
            return JsonResponse({'error': 'Konflik kelas pada periode ini'}, status=400)

        # Check subject conflict (same grade_subject already scheduled at this period)
        subject_conflict = TimetableSlot.objects.filter(
            timetable=slot.timetable,
            period=target_period,
            lesson__grade_subject=slot.lesson.grade_subject
        ).exclude(slot_id=slot_id).exists()
        if subject_conflict:
            return JsonResponse({'error': 'Mapel ini sudah dijadwalkan pada periode ini'}, status=400)

        # Check room conflict (same room already used at this period)
        if slot.room:
            room_conflict = TimetableSlot.objects.filter(
                timetable=slot.timetable,
                period=target_period,
                room=slot.room
            ).exclude(slot_id=slot_id).exists()
            if room_conflict:
                return JsonResponse({'error': 'Ruangan sudah digunakan pada periode ini'}, status=400)

        # Check teacher availability
        teacher_unavailable = TeacherAvailability.objects.filter(
            timetable=slot.timetable,
            teacher=slot.lesson.teacher,
            day=target_period.day,
        ).filter(
            Q(period=target_period) | Q(period__isnull=True),
            is_available=False
        ).exists()
        if teacher_unavailable:
            return JsonResponse({'error': f'Guru tidak tersedia pada hari {target_period.get_day_display()}'}, status=400)

        # Check room availability if room is assigned
        if slot.room:
            room_unavailable = RoomAvailability.objects.filter(
                timetable=slot.timetable,
                room=slot.room,
                day=target_period.day,
            ).filter(
                Q(period=target_period) | Q(period__isnull=True),
                is_available=False
            ).exists()
            if room_unavailable:
                return JsonResponse({'error': f'Ruangan tidak tersedia pada hari {target_period.get_day_display()}'}, status=400)

        # Check grade availability
        grade_unavailable = GradeAvailability.objects.filter(
            timetable=slot.timetable,
            grade=slot.lesson.grade_subject.grade,
            day=target_period.day,
        ).filter(
            Q(period=target_period) | Q(period__isnull=True),
            is_available=False,
        ).exists()
        if grade_unavailable:
            return JsonResponse({'error': f'Kelas tidak tersedia pada hari {target_period.get_day_display()}'}, status=400)

        slot.period = target_period
        slot.is_manual = True
        slot.save()

        return JsonResponse({'success': True})
    except (TimetableSlot.DoesNotExist, Period.DoesNotExist, json.JSONDecodeError) as e:
        return JsonResponse({'error': str(e)}, status=400)


# --- Schedule Lesson from Unscheduled (AJAX) ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_schedule_lesson(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        teacher_subject_id = data.get('teacher_subject_id')
        target_period_id = data.get('target_period_id')

        ts = TeacherSubject.objects.select_related(
            'grade_subject__grade', 'teacher'
        ).get(teacher_subject_id=teacher_subject_id)
        target_period = Period.objects.get(period_id=target_period_id)
        timetable = Timetable.objects.get(timetable_id=data.get('timetable_id', None))

        if target_period.is_break:
            return JsonResponse({'error': 'Tidak bisa dijadwalkan pada jam istirahat'}, status=400)

        target_grade_id = data.get('target_grade_id')
        if target_grade_id and target_grade_id != ts.grade_subject.grade_id:
            return JsonResponse({'error': 'Kelas target tidak sesuai dengan kelas pelajaran ini'}, status=400)

        # Validasi: TeacherSubject harus sesuai school_year + semester timetable
        if ts.grade_subject.grade.school_year != timetable.school_year or \
           ts.grade_subject.grade.semester != timetable.semester:
            return JsonResponse({'error': 'Mapel/guru ini tidak sesuai dengan tahun ajaran dan semester jadwal'}, status=400)

        lesson, _ = Lesson.objects.get_or_create(
            timetable=timetable,
            grade_subject=ts.grade_subject,
            teacher=ts.teacher,
            defaults={'hours_per_week': ts.hours}
        )

        if TimetableSlot.objects.filter(
            timetable=timetable,
            period=target_period,
            lesson__teacher=ts.teacher
        ).exists():
            return JsonResponse({'error': 'Konflik guru pada periode ini'}, status=400)

        if TimetableSlot.objects.filter(
            timetable=timetable,
            period=target_period,
            lesson__grade_subject__grade=ts.grade_subject.grade
        ).exists():
            return JsonResponse({'error': 'Konflik kelas pada periode ini'}, status=400)

        subject_conflict = TimetableSlot.objects.filter(
            timetable=timetable,
            period=target_period,
            lesson__grade_subject=ts.grade_subject
        ).exists()
        if subject_conflict:
            return JsonResponse({'error': 'Mapel ini sudah dijadwalkan pada periode ini'}, status=400)

        teacher_unavailable = TeacherAvailability.objects.filter(
            timetable=timetable,
            teacher=ts.teacher,
            day=target_period.day,
        ).filter(
            Q(period=target_period) | Q(period__isnull=True),
            is_available=False
        ).exists()
        if teacher_unavailable:
            return JsonResponse({'error': f'Guru tidak tersedia pada hari {target_period.get_day_display()}'}, status=400)

        # Check room conflict and availability
        target_room = ts.grade_subject.room
        if target_room:
            room_conflict = TimetableSlot.objects.filter(
                timetable=timetable,
                period=target_period,
                room=target_room
            ).exists()
            if room_conflict:
                return JsonResponse({'error': 'Ruangan sudah digunakan pada periode ini'}, status=400)

            room_unavailable = RoomAvailability.objects.filter(
                timetable=timetable,
                room=target_room,
                day=target_period.day,
            ).filter(
                Q(period=target_period) | Q(period__isnull=True),
                is_available=False
            ).exists()
            if room_unavailable:
                return JsonResponse({'error': f'Ruangan tidak tersedia pada hari {target_period.get_day_display()}'}, status=400)

        # Check grade availability
        grade_unavailable = GradeAvailability.objects.filter(
            timetable=timetable,
            grade=ts.grade_subject.grade,
            day=target_period.day,
        ).filter(
            Q(period=target_period) | Q(period__isnull=True),
            is_available=False,
        ).exists()
        if grade_unavailable:
            return JsonResponse({'error': f'Kelas tidak tersedia pada hari {target_period.get_day_display()}'}, status=400)

        new_slot = TimetableSlot.objects.create(
            timetable=timetable,
            lesson=lesson,
            period=target_period,
            room=ts.grade_subject.room,
            is_manual=True,
        )

        scheduled_count = TimetableSlot.objects.filter(
            timetable=timetable,
            lesson__grade_subject=ts.grade_subject,
            lesson__teacher=ts.teacher,
        ).count()
        remaining = max(0, ts.hours - scheduled_count)

        return JsonResponse({
            'success': True,
            'slot_id': new_slot.slot_id,
            'subject_name': ts.grade_subject.subject.subject_name,
            'subject_id': ts.grade_subject.subject.subject_id,
            'teacher_name': ts.teacher.user.username,
            'grade_name': f"{ts.grade_subject.grade.grade}{ts.grade_subject.grade.sub_grade or ''}",
            'grade_id': ts.grade_subject.grade_id,
            'room_name': ts.grade_subject.room.room_name if ts.grade_subject.room else '',
            'teacher_subject_id': ts.teacher_subject_id,
            'remaining_hours': remaining,
        })
    except (TeacherSubject.DoesNotExist, Period.DoesNotExist, Timetable.DoesNotExist, json.JSONDecodeError) as e:
        return JsonResponse({'error': str(e)}, status=400)


# --- Delete Slot (AJAX) ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_delete_slot(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        slot_id = data.get('slot_id')
        slot = TimetableSlot.objects.select_related(
            'lesson__teacher__user', 'lesson__grade_subject__grade', 'lesson__grade_subject__subject', 'room'
        ).get(slot_id=slot_id)

        ts = TeacherSubject.objects.filter(
            grade_subject=slot.lesson.grade_subject,
            teacher=slot.lesson.teacher,
        ).first()

        scheduled_count = TimetableSlot.objects.filter(
            timetable=slot.timetable,
            lesson__grade_subject=slot.lesson.grade_subject,
            lesson__teacher=slot.lesson.teacher,
        ).exclude(slot_id=slot_id).count()

        remaining = (ts.hours - scheduled_count) if ts else 0

        slot_data = {
            'slot_id': slot.slot_id,
            'subject_name': slot.lesson.grade_subject.subject.subject_name,
            'subject_id': slot.lesson.grade_subject.subject.subject_id,
            'teacher_name': slot.lesson.teacher.user.username,
            'grade_name': f"{slot.lesson.grade_subject.grade.grade}{slot.lesson.grade_subject.grade.sub_grade or ''}",
            'grade_id': slot.lesson.grade_subject.grade_id,
            'room_name': slot.room.room_name if slot.room else '',
            'teacher_subject_id': ts.teacher_subject_id if ts else None,
            'remaining_hours': remaining,
        }

        slot.delete()
        return JsonResponse({'success': True, **slot_data})
    except (TimetableSlot.DoesNotExist, json.JSONDecodeError) as e:
        return JsonResponse({'error': str(e)}, status=400)


# --- Save Periods (AJAX) ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_save_periods(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        timetable_id = data.get('timetable_id')
        days = data.get('days', [])
        periods_data = data.get('periods', [])

        timetable = Timetable.objects.get(timetable_id=timetable_id)

        # Day mapping
        day_map = {0: 'SUN', 1: 'MON', 2: 'TUE', 3: 'WED', 4: 'THU', 5: 'FRI', 6: 'SAT'}

        # Delete existing periods for this timetable
        Period.objects.filter(timetable=timetable).delete()

        # Create new periods for each selected day
        for day_num in days:
            day_code = day_map.get(day_num, 'MON')
            for period_data in periods_data:
                is_break = period_data.get('type') == 'break'
                Period.objects.create(
                    timetable=timetable,
                    day=day_code,
                    order=period_data.get('order'),
                    start_time=period_data.get('start_time'),
                    end_time=period_data.get('end_time'),
                    is_break=is_break,
                    break_name=period_data.get('name') if is_break else ''
                )

        return JsonResponse({'success': True})
    except (Timetable.DoesNotExist, json.JSONDecodeError, Exception) as e:
        return JsonResponse({'error': str(e)}, status=400)


# --- Publish / Unpublish Timetable ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_publish(request, _id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('timetable-view', args=[_id]))

    timetable = Timetable.objects.get(timetable_id=_id)
    timetable.status = 'published'
    timetable.save()
    return HttpResponseRedirect(reverse('timetable-view', args=[_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_unpublish(request, _id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('timetable-view', args=[_id]))

    timetable = Timetable.objects.get(timetable_id=_id)
    timetable.status = 'draft'
    timetable.save()
    return HttpResponseRedirect(reverse('timetable-view', args=[_id]))


# --- Teacher Absence Management ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def teacher_absence_index(request, timetable_id):
    timetable = Timetable.objects.get(timetable_id=timetable_id)
    availabilities = timetable.teacher_availabilities.select_related(
        'teacher__user'
    ).all().order_by('teacher__user__username', 'day')

    context = {
        'data': availabilities,
        'timetable': timetable,
        'segment': 'guru-absen',
        'group_segment': 'kurikulum',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='JADWAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_absence_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def teacher_absence_add(request, timetable_id):
    timetable = Timetable.objects.get(timetable_id=timetable_id)
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher')
        day = request.POST.get('day')
        reason = request.POST.get('reason', '')
        period_id = request.POST.get('period')

        teacher = Teacher.objects.get(teacher_id=teacher_id)
        period = Period.objects.get(period_id=period_id) if period_id else None

        TeacherAvailability.objects.create(
            teacher=teacher,
            timetable=timetable,
            day=day,
            period=period,
            is_available=False,
            reason=reason,
        )
        return HttpResponseRedirect(reverse('teacher-absence-index', args=[timetable_id]))

    teachers = Teacher.objects.select_related('user').order_by('user__username')
    
    # Custom day order mapping
    day_order = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}
    periods = list(timetable.periods.all())
    periods.sort(key=lambda p: (day_order.get(p.day, 99), p.order))

    context = {
        'teachers': teachers,
        'periods': periods,
        'timetable': timetable,
        'segment': 'guru-absen',
        'group_segment': 'kurikulum',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='JADWAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/teacher_absence_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def teacher_absence_delete(request, timetable_id, _id):
    try:
        availability = TeacherAvailability.objects.get(availability_id=_id)
        availability.delete()
    except ProtectedError:
        pass
    return HttpResponseRedirect(reverse('teacher-absence-index', args=[timetable_id]))


# --- Substitute Matching (AJAX) ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def substitute_recommend(request, timetable_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        slot_id = data.get('slot_id')
        timetable = Timetable.objects.get(timetable_id=timetable_id)
        slot = TimetableSlot.objects.select_related(
            'lesson__teacher__user', 'period'
        ).get(slot_id=slot_id)

        original_teacher = slot.lesson.teacher
        period = slot.period

        # Find teachers who are NOT already teaching at this period
        busy_teachers = TimetableSlot.objects.filter(
            timetable=timetable,
            period=period
        ).values_list('lesson__teacher_id', flat=True)

        candidates = Teacher.objects.exclude(
            teacher_id__in=busy_teachers
        ).select_related('user').order_by('user__username')

        # Score candidates
        recommendations = []
        for candidate in candidates:
            score = 0

            # Same subject qualification
            has_qualification = TeacherSubject.objects.filter(
                teacher=candidate,
                grade_subject=slot.lesson.grade_subject
            ).exists()
            if has_qualification:
                score += 50

            # Not marked absent for this period
            is_absent = TeacherAvailability.objects.filter(
                teacher=candidate,
                timetable=timetable,
                day=period.day,
                is_available=False
            ).exists()
            if is_absent:
                continue

            # Not too many hours
            current_hours = TimetableSlot.objects.filter(
                timetable=timetable,
                lesson__teacher=candidate
            ).count()
            if current_hours < 24:
                score += 25

            recommendations.append({
                'teacher_id': candidate.teacher_id,
                'username': candidate.user.username,
                'score': score,
                'has_qualification': has_qualification,
            })

        recommendations.sort(key=lambda x: x['score'], reverse=True)

        return JsonResponse({'success': True, 'recommendations': recommendations[:10]})
    except (TimetableSlot.DoesNotExist, json.JSONDecodeError) as e:
        return JsonResponse({'error': str(e)}, status=400)


# --- Assign Substitute (AJAX) ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def substitute_assign(request, timetable_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        slot_id = data.get('slot_id')
        substitute_teacher_id = data.get('substitute_teacher_id')
        reason = data.get('reason', '')

        timetable = Timetable.objects.get(timetable_id=timetable_id)
        slot = TimetableSlot.objects.get(slot_id=slot_id)
        substitute_teacher = Teacher.objects.get(teacher_id=substitute_teacher_id)

        # Check if this teacher is available
        is_absent = TeacherAvailability.objects.filter(
            teacher=substitute_teacher,
            timetable=timetable,
            day=slot.period.day,
            is_available=False
        ).exists()
        if is_absent:
            return JsonResponse({'error': 'Guru tidak tersedia'}, status=400)

        assignment = SubstituteAssignment.objects.create(
            timetable=timetable,
            original_slot=slot,
            substitute_teacher=substitute_teacher,
            status='confirmed',
            match_score=0,
            reason=reason,
        )

        return JsonResponse({'success': True, 'assignment_id': assignment.assignment_id})
    except (TimetableSlot.DoesNotExist, Teacher.DoesNotExist, json.JSONDecodeError) as e:
        return JsonResponse({'error': str(e)}, status=400)


# --- Grade Subject by Grade (AJAX) ---

@login_required(login_url='/login/')
def ajax_grade_subjects_by_grade_for_schedule(request):
    grade_id = request.GET.get('grade_id')
    timetable_id = request.GET.get('timetable_id')
    if not grade_id:
        return JsonResponse([], safe=False)

    gs_list = GradeSubject.objects.filter(
        grade_id=grade_id
    ).select_related('subject').order_by('subject__subject_name')

    result = [
        {'id': gs.grade_subject_id, 'name': gs.subject.subject_name}
        for gs in gs_list
    ]
    return JsonResponse(result, safe=False)


# --- Timetable PDF Export ---

@login_required(login_url='/login/')
@role_required(allowed_roles='JADWAL')
def timetable_export_pdf(request, _id):
    timetable = Timetable.objects.get(timetable_id=_id)

    day_order = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}
    periods = list(timetable.periods.all())
    periods.sort(key=lambda p: (day_order.get(p.day, 99), p.order))

    slots = timetable.slots.select_related(
        'lesson__grade_subject__grade', 'lesson__grade_subject__subject',
        'lesson__teacher__user', 'period', 'room'
    ).all()

    days_display = dict(Period.DAY_CHOICES)

    header_days = []
    current_day = None
    count = 0
    for p in periods:
        if p.day != current_day:
            if current_day is not None:
                header_days.append({'code': current_day, 'name': days_display.get(current_day, current_day), 'colspan': count})
            current_day = p.day
            count = 1
        else:
            count += 1
    if current_day is not None:
        header_days.append({'code': current_day, 'name': days_display.get(current_day, current_day), 'colspan': count})

    mode = request.GET.get('mode', 'kelas')
    view_type = request.GET.get('view', 'standar')
    grade_filter = request.GET.get('grade', '')
    teacher_filter = request.GET.get('teacher', '')
    room_filter = request.GET.get('room', '')

    grades = Grade.objects.filter(
        school_year=timetable.school_year,
        semester=timetable.semester,
        gradesubject__teacher_subjects__isnull=False,
    ).distinct().order_by('grade', 'sub_grade')

    teachers = Teacher.objects.filter(
        lesson__slots__timetable=timetable
    ).distinct().order_by('user__username')

    rooms = Room.objects.filter(
        timetableslot__timetable=timetable
    ).distinct().order_by('room_name')

    if grade_filter:
        grades = grades.filter(grade_id=grade_filter) | grades.filter(grade=grade_filter[:2], sub_grade=grade_filter[2:] if len(grade_filter) > 2 else '')

    if teacher_filter:
        teachers = teachers.filter(teacher_id=teacher_filter)

    if room_filter:
        rooms = rooms.filter(room_id=room_filter)

    periods_unique = []
    seen_orders = set()
    for p in periods:
        if p.order not in seen_orders:
            seen_orders.add(p.order)
            periods_unique.append(p)

    active_days = sorted(set(p.day for p in periods), key=lambda d: day_order.get(d, 99))

    mode_label = {'kelas': 'Per Kelas', 'guru': 'Per Guru', 'ruangan': 'Per Ruangan'}.get(mode, 'Per Kelas')
    view_label = 'Standar' if view_type == 'standar' else 'Kompak'

    context = {
        'data': timetable,
        'periods': periods,
        'periods_unique': periods_unique,
        'active_days': active_days,
        'header_days': header_days,
        'slots': slots,
        'grades': grades,
        'teachers': teachers,
        'rooms': rooms,
        'days_display': days_display,
        'mode': mode,
        'view_type': view_type,
        'mode_label': mode_label,
        'view_label': view_label,
    }

    html_string = render(request, 'home/timetable_pdf.html', context).content.decode('utf-8')

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode('utf-8')), result, encoding='utf-8')

    if pdf.err:
        return HttpResponse('Error generating PDF', status=500)

    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    filename = f"Jadwal_{timetable.name}_{mode_label}_{view_label}.pdf".replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
