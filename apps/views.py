from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import connection, IntegrityError
from django.db.models.deletion import ProtectedError
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
        'group_segment': 'master',
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
        'group_segment': 'master',
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
        'group_segment': 'master',
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
        'group_segment': 'master',
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
    teachers = Teacher.objects.select_related('user').order_by('user__username')
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
