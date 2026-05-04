from django import forms
from django.forms import ModelForm
from django.db.models import Q
from apps.models import *
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm, UserCreationForm
import datetime
from django.forms import DateInput
from tinymce.widgets import TinyMCE
from django.forms.widgets import TimeInput


class ComboBoxWidget(forms.Select):
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs)
        self._choices = choices

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs['list'] = f'{name}_list'
        input_html = f'<input type="text" name="{name}" value="{value or ""}" list="{name}_list" class="form-control form-control-sm">'
        datalist_html = f'<datalist id="{name}_list">'
        for option_value, option_label in self._choices:
            datalist_html += f'<option value="{option_label}">'
        datalist_html += '</datalist>'
        return input_html + datalist_html


class FormUser(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(FormUser, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['user_id'].label = 'User ID'
        self.fields['username'].label = 'Nama User'
        self.fields['email'].label = 'Email'
        self.fields['position'].label = 'Posisi'
        self.fields['signature'].label = 'Tanda Tangan'
        self.fields['signature'].required = False
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Konfirmasi Password'
        self.fields['user_id'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['username'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['email'].widget = forms.EmailInput(
            {'class': 'form-control-sm'})
        self.fields['password1'].widget = forms.PasswordInput(
            {'class': 'form-control-sm'})
        self.fields['password2'].widget = forms.PasswordInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = User
        exclude = ['date_joined', 'password', 'is_active', 'is_staff',
                   'is_superuser', 'entry_date', 'entry_by', 'update_date', 'update_by']
        widgets = {
            'signature': forms.FileInput(attrs={'class': 'form-control form-control-sm'}),
        }


class FormUserView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormUserView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['username'].label = 'Nama User'
        self.fields['email'].label = 'Email'
        self.fields['position'].label = 'Posisi'
        self.fields['username'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['email'].widget = forms.EmailInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'position', 'signature']

        widgets = {
            'position': forms.Select(attrs={'class': 'form-control form-select-sm', 'disabled': 'disabled'}),
            'signature': forms.FileInput(attrs={'class': 'form-control form-control-sm', 'disabled': 'disabled'}),
        }


class FormUserUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormUserUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['username'].label = 'Nama User'
        self.fields['email'].label = 'Email'
        self.fields['position'].label = 'Posisi'
        self.fields['username'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['email'].widget = forms.EmailInput(
            {'class': 'form-control-sm'})
        self.fields['signature'].required = False

    class Meta:
        model = User
        exclude = ['user_id', 'password', 'date_joined',
                   'is_active', 'is_staff', 'is_superuser', 'entry_date', 'entry_by', 'update_date', 'update_by']

        widgets = {
            'position': forms.Select(attrs={'class': 'form-control form-select-sm'}),
            'signature': forms.FileInput(attrs={'class': 'form-control form-control-sm'}),
        }


class FormChangePassword(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(FormChangePassword, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['old_password'].label = 'Password Lama'
        self.fields['new_password1'].label = 'Password Baru'
        self.fields['new_password2'].label = 'Konfirmasi Password Baru'
        self.fields['old_password'].widget = forms.PasswordInput(
            {'class': 'form-control-sm z-index-2'})
        self.fields['new_password1'].widget = forms.PasswordInput(
            {'class': 'form-control-sm z-index-2'})
        self.fields['new_password2'].widget = forms.PasswordInput(
            {'class': 'form-control-sm z-index-2'})


class FormSetPassword(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(FormSetPassword, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['new_password1'].label = 'Password Baru'
        self.fields['new_password2'].label = 'Konfirmasi Password Baru'
        self.fields['new_password1'].widget = forms.PasswordInput(
            {'class': 'form-control-sm'})
        self.fields['new_password2'].widget = forms.PasswordInput(
            {'class': 'form-control-sm'})


class FormPosition(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPosition, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['position_id'].label = 'ID Posisi'
        self.fields['position_name'].label = 'Nama Posisi'
        self.fields['position_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase', 'placeholder': 'XXX'})
        self.fields['position_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Position
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormPositionUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPositionUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['position_name'].label = 'Nama Posisi'
        self.fields['position_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Position
        exclude = ['position_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormPositionView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPositionView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['position_name'].label = 'Nama Posisi'
        self.fields['position_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Position
        fields = ['position_id', 'position_name']


class FormMenu(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormMenu, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['menu_id'].label = 'ID Menu'
        self.fields['menu_name'].label = 'Nama Menu'
        self.fields['menu_remark'].label = 'Deskripsi'
        self.fields['menu_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['menu_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['menu_remark'].widget = forms.Textarea(
            {'class': 'form-control-sm', 'rows': 3})

    class Meta:
        model = Menu
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormMenuUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormMenuUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['menu_name'].label = 'Nama Menu'
        self.fields['menu_remark'].label = 'Deskripsi'
        self.fields['menu_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['menu_remark'].widget = forms.Textarea(
            {'class': 'form-control-sm', 'rows': 3})

    class Meta:
        model = Menu
        exclude = ['menu_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormMenuView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormMenuView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['menu_name'].label = 'Nama Menu'
        self.fields['menu_remark'].label = 'Deskripsi'
        self.fields['menu_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['menu_remark'].widget = forms.Textarea(
            {'class': 'form-control-sm', 'rows': 3, 'readonly': 'readonly'})

    class Meta:
        model = Menu
        fields = ['menu_id', 'menu_name', 'menu_remark']


class FormAuthUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormAuthUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['add'].widget = forms.CheckboxInput(
            {'class': 'border mt-1'})
        self.fields['edit'].widget = forms.CheckboxInput(
            {'class': 'border mt-1'})
        self.fields['delete'].widget = forms.CheckboxInput(
            {'class': 'border mt-1'})

    class Meta:
        model = Auth
        exclude = ['user', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormClosing(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormClosing, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['document'].label = 'Document'
        self.fields['year_closed'].label = 'Year Closed'
        self.fields['month_closed'].label = 'Month Closed'
        self.fields['year_open'].label = 'Year Open'
        self.fields['month_open'].label = 'Month Open'
        self.fields['document'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm text-uppercase'})

    class Meta:
        model = Closing
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']

        YEAR_CHOICES = []
        for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
            YEAR_CHOICES.append((r, r))

        MONTH_CHOICES = []
        for r in range(1, 13):
            MONTH_CHOICES.append((r, r))

        widgets = {
            'year_closed': forms.Select(choices=YEAR_CHOICES, attrs={'class': 'form-control form-select-sm'}),
            'month_closed': forms.Select(choices=MONTH_CHOICES, attrs={'class': 'form-control form-select-sm'}),
            'year_open': forms.Select(choices=YEAR_CHOICES, attrs={'class': 'form-control form-select-sm'}),
            'month_open': forms.Select(choices=MONTH_CHOICES, attrs={'class': 'form-control form-select-sm'}),
        }


class FormClosingUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormClosingUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['year_closed'].label = 'Year Closed'
        self.fields['month_closed'].label = 'Month Closed'
        self.fields['year_open'].label = 'Year Open'
        self.fields['month_open'].label = 'Month Open'
        self.fields['year_closed'].widget = forms.Select(
            attrs={'class': 'form-control form-select-sm'})
        self.fields['month_closed'].widget = forms.Select(
            attrs={'class': 'form-control form-select-sm'})
        self.fields['year_open'].widget = forms.Select(
            attrs={'class': 'form-control form-select-sm'})
        self.fields['month_open'].widget = forms.Select(
            attrs={'class': 'form-control form-select-sm'})

    class Meta:
        model = Closing
        exclude = ['document', 'entry_date',
                   'entry_by', 'update_date', 'update_by']

    YEAR_CHOICES = []
    for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append((r, r))

    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append((r, r))

    widgets = {
        'year_closed': forms.Select(choices=YEAR_CHOICES, attrs={'class': 'form-control form-select-sm'}),
        'month_closed': forms.Select(choices=MONTH_CHOICES, attrs={'class': 'form-control form-select-sm'}),
        'year_open': forms.Select(choices=YEAR_CHOICES, attrs={'class': 'form-control form-select-sm'}),
        'month_open': forms.Select(choices=MONTH_CHOICES, attrs={'class': 'form-control form-select-sm'}),
    }


class FormClosingView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormClosingView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['document'].label = 'Document'
        self.fields['year_closed'].label = 'Year Closed'
        self.fields['month_closed'].label = 'Month Closed'
        self.fields['year_open'].label = 'Year Open'
        self.fields['month_open'].label = 'Month Open'
        self.fields['document'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm text-uppercase', 'readonly': 'readonly'})
        self.fields['year_closed'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['month_closed'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['year_open'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['month_open'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Closing
        fields = ['document', 'year_closed', 'month_closed',
                  'year_open', 'month_open']


class FormDivision(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormDivision, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['division_name'].label = 'Division Name'
        self.fields['division_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Division
        exclude = ['division_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormDivisionUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormDivisionUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['division_name'].label = 'Division Name'
        self.fields['division_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Division
        exclude = ['division_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormDivisionView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormDivisionView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['division_name'].label = 'Division Name'
        self.fields['division_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Division
        fields = ['division_id', 'division_name']


class DateInput(forms.DateInput):
    input_type = 'date'


class FormLevel(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormLevel, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['level_id'].label = 'Tingkatan'
        self.fields['level_name'].label = 'Nama Tingkatan'
        self.fields['level_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase', 'placeholder': 'XXX'})
        self.fields['level_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Level
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormLevelUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormLevelUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['level_name'].label = 'Nama Tingkatan'
        self.fields['level_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Level
        exclude = ['level_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormLevelView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormLevelView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['level_name'].label = 'Nama Tingkatan'
        self.fields['level_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Level
        fields = ['level_id', 'level_name']


class FormGrade(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormGrade, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['grade_id'].label = 'ID Kelas'
        self.fields['level'].label = 'Tingkatan'
        self.fields['grade'].label = 'Kelas'
        self.fields['sub_grade'].label = 'Sub Kelas'
        self.fields['grade_name'].label = 'Nama Kelas'
        self.fields['school_year'].label = 'Tahun Ajaran'
        self.fields['semester'].label = 'Semester'
        self.fields['homeroom_teacher_1'].label = 'Wali Kelas 1'
        self.fields['homeroom_teacher_2'].label = 'Wali Kelas 2'
        self.fields['class_leader'].label = 'Ketua Kelas'
        self.fields['vice_class_leader'].label = 'Wakil Ketua Kelas'
        self.fields['secretary'].label = 'Sekretaris'
        self.fields['treasurer'].label = 'Bendahara'
        self.fields['grade_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase', 'placeholder': 'VII-A'})
        self.fields['level'].queryset = Level.objects.all().order_by('level_id')
        self.fields['level'].empty_label = 'Pilih Tingkatan'
        self.fields['level'].label_from_instance = lambda obj: f"{obj.level_id} - {obj.level_name}"
        self.fields['level'].widget.attrs.update(
            {'class': 'form-control form-select-sm'})
        self.fields['grade'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'placeholder': '7'})
        self.fields['sub_grade'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'placeholder': 'A'})
        self.fields['grade_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'placeholder': 'Kelas 7A'})
        self.fields['school_year'].queryset = SchoolYear.objects.all().order_by(
            '-school_year_name')
        self.fields['school_year'].empty_label = 'Pilih Tahun Ajaran'
        self.fields['school_year'].label_from_instance = lambda obj: obj.school_year_name
        self.fields['school_year'].widget.attrs.update(
            {'class': 'form-control form-select-sm'})
        self.fields['semester'].widget = forms.Select(
            choices=[('', 'Pilih Semester'), ('1', 'Semester 1'), ('2', 'Semester 2')],
            attrs={'class': 'form-control form-select-sm'})
        teacher_qs = Teacher.objects.select_related('user').order_by('user__username')
        for f in ['homeroom_teacher_1', 'homeroom_teacher_2']:
            self.fields[f].queryset = teacher_qs
            self.fields[f].empty_label = '-'
            self.fields[f].required = False
            self.fields[f].label_from_instance = lambda obj: obj.user.username if obj.user else str(obj.user_id)
            self.fields[f].widget.attrs.update({'class': 'form-control form-select-sm'})
        # Officer fields — queryset kosong dulu, diisi saat edit via grade_id
        for f in ['class_leader', 'vice_class_leader', 'secretary', 'treasurer']:
            self.fields[f].queryset = Student.objects.none()
            self.fields[f].empty_label = '-'
            self.fields[f].required = False
            self.fields[f].label_from_instance = lambda obj: f"{obj.nipd or ''} - {obj.name}" if obj.nipd else obj.name
            self.fields[f].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = Grade
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']

    def clean(self):
        cleaned_data = super().clean()
        t1 = cleaned_data.get('homeroom_teacher_1')
        t2 = cleaned_data.get('homeroom_teacher_2')
        if t1 and t2 and t1 == t2:
            self.add_error('homeroom_teacher_2',
                           'Wali Kelas 2 tidak boleh sama dengan Wali Kelas 1.')
        return cleaned_data


class FormGradeUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormGradeUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['level'].label = 'Tingkatan'
        self.fields['grade'].label = 'Kelas'
        self.fields['sub_grade'].label = 'Sub Kelas'
        self.fields['grade_name'].label = 'Nama Kelas'
        self.fields['school_year'].label = 'Tahun Ajaran'
        self.fields['semester'].label = 'Semester'
        self.fields['homeroom_teacher_1'].label = 'Wali Kelas 1'
        self.fields['homeroom_teacher_2'].label = 'Wali Kelas 2'
        self.fields['class_leader'].label = 'Ketua Kelas'
        self.fields['vice_class_leader'].label = 'Wakil Ketua Kelas'
        self.fields['secretary'].label = 'Sekretaris'
        self.fields['treasurer'].label = 'Bendahara'
        self.fields['level'].queryset = Level.objects.all().order_by('level_id')
        self.fields['level'].empty_label = 'Pilih Tingkatan'
        self.fields['level'].label_from_instance = lambda obj: f"{obj.level_id} - {obj.level_name}"
        self.fields['level'].widget.attrs.update(
            {'class': 'form-control form-select-sm'})
        self.fields['grade'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['sub_grade'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['grade_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['school_year'].queryset = SchoolYear.objects.all().order_by(
            '-school_year_name')
        self.fields['school_year'].empty_label = 'Pilih Tahun Ajaran'
        self.fields['school_year'].label_from_instance = lambda obj: obj.school_year_name
        self.fields['school_year'].widget.attrs.update(
            {'class': 'form-control form-select-sm'})
        self.fields['semester'].widget = forms.Select(
            choices=[('', 'Pilih Semester'), ('1', 'Semester 1'), ('2', 'Semester 2')],
            attrs={'class': 'form-control form-select-sm'})
        teacher_qs = Teacher.objects.select_related('user').order_by('user__username')
        for f in ['homeroom_teacher_1', 'homeroom_teacher_2']:
            self.fields[f].queryset = teacher_qs
            self.fields[f].empty_label = '-'
            self.fields[f].required = False
            self.fields[f].label_from_instance = lambda obj: obj.user.username if obj.user else str(obj.teacher_id)
            self.fields[f].widget.attrs.update({'class': 'form-control form-select-sm'})
        # Officer fields — queryset santri dalam kelas ini
        students_qs = Student.objects.filter(
            grade=self.instance
        ).order_by('name') if self.instance and self.instance.pk else Student.objects.none()
        for f in ['class_leader', 'vice_class_leader', 'secretary', 'treasurer']:
            self.fields[f].queryset = students_qs
            self.fields[f].empty_label = '-'
            self.fields[f].required = False
            self.fields[f].label_from_instance = lambda obj: f"{obj.nipd or ''} - {obj.name}" if obj.nipd else obj.name
            self.fields[f].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = Grade
        exclude = ['grade_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']

    def clean(self):
        cleaned_data = super().clean()
        t1 = cleaned_data.get('homeroom_teacher_1')
        t2 = cleaned_data.get('homeroom_teacher_2')
        if t1 and t2 and t1 == t2:
            self.add_error('homeroom_teacher_2',
                           'Wali Kelas 2 tidak boleh sama dengan Wali Kelas 1.')
        return cleaned_data


class FormGradeView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormGradeView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['level'] = forms.CharField(
            label='Tingkatan',
            required=False,
            initial=(
                f"{self.instance.level.level_id} - {self.instance.level.level_name}"
                if self.instance and self.instance.level else ''),
            widget=forms.TextInput(
                {'class': 'form-control-sm', 'readonly': 'readonly'})
        )
        self.fields['grade'].label = 'Kelas'
        self.fields['sub_grade'].label = 'Sub Kelas'
        self.fields['grade_name'].label = 'Nama Kelas'
        self.fields['school_year'] = forms.CharField(
            label='Tahun Ajaran',
            required=False,
            initial=(
                self.instance.school_year.school_year_name if self.instance and self.instance.school_year else ''),
            widget=forms.TextInput(
                {'class': 'form-control-sm', 'readonly': 'readonly'})
        )
        self.fields['semester'] = forms.CharField(
            label='Semester',
            required=False,
            initial=(
                self.instance.get_semester_display() if self.instance and self.instance.semester else ''),
            widget=forms.TextInput(
                {'class': 'form-control-sm', 'readonly': 'readonly'})
        )
        self.fields['homeroom_teacher_1'] = forms.CharField(
            label='Wali Kelas 1', required=False,
            widget=forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'}))
        self.fields['homeroom_teacher_2'] = forms.CharField(
            label='Wali Kelas 2', required=False,
            widget=forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'}))
        self.fields['class_leader'] = forms.CharField(
            label='Ketua Kelas', required=False,
            initial=(self.instance.class_leader.name if self.instance and self.instance.class_leader else ''),
            widget=forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'}))
        self.fields['vice_class_leader'] = forms.CharField(
            label='Wakil Ketua Kelas', required=False,
            initial=(self.instance.vice_class_leader.name if self.instance and self.instance.vice_class_leader else ''),
            widget=forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'}))
        self.fields['secretary'] = forms.CharField(
            label='Sekretaris', required=False,
            initial=(self.instance.secretary.name if self.instance and self.instance.secretary else ''),
            widget=forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'}))
        self.fields['treasurer'] = forms.CharField(
            label='Bendahara', required=False,
            initial=(self.instance.treasurer.name if self.instance and self.instance.treasurer else ''),
            widget=forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'}))
        self.fields['grade'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['sub_grade'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['grade_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

        # Set nilai tampilan untuk field yang di-override
        if self.instance and self.instance.pk:
            self.initial['level'] = f"{self.instance.level.level_id} - {self.instance.level.level_name}" if self.instance.level else ''
            self.initial['school_year'] = self.instance.school_year.school_year_name if self.instance.school_year else ''
            self.initial['semester'] = self.instance.get_semester_display() if self.instance.semester else ''
            self.initial['homeroom_teacher_1'] = self.instance.homeroom_teacher_1.user.username if self.instance.homeroom_teacher_1 and self.instance.homeroom_teacher_1.user else ''
            self.initial['homeroom_teacher_2'] = self.instance.homeroom_teacher_2.user.username if self.instance.homeroom_teacher_2 and self.instance.homeroom_teacher_2.user else ''
            self.initial['class_leader'] = self.instance.class_leader.name if self.instance.class_leader else ''
            self.initial['vice_class_leader'] = self.instance.vice_class_leader.name if self.instance.vice_class_leader else ''
            self.initial['secretary'] = self.instance.secretary.name if self.instance.secretary else ''
            self.initial['treasurer'] = self.instance.treasurer.name if self.instance.treasurer else ''

    class Meta:
        model = Grade
        fields = ['grade_id', 'level', 'grade', 'sub_grade', 'grade_name',
                  'school_year', 'semester', 'homeroom_teacher_1', 'homeroom_teacher_2',
                  'class_leader', 'vice_class_leader', 'secretary', 'treasurer']


class FormStudyGroup(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormStudyGroup, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['school_year'].label = 'Tahun Ajaran'
        self.fields['group_type_code'].label = 'Kode Jenis'
        self.fields['group_type_name'].label = 'Nama Jenis'
        self.fields['group_name'].label = 'Nama Kelompok'
        self.fields['group_division'].label = 'Pembagian Kelompok'
        self.fields['group_teacher'].label = 'Guru Kelompok'
        self.fields['school_year'].queryset = SchoolYear.objects.all().order_by('-school_year_name')
        self.fields['school_year'].empty_label = 'Pilih Tahun Ajaran'
        self.fields['school_year'].label_from_instance = lambda obj: obj.school_year_name
        self.fields['school_year'].widget.attrs.update({'class': 'form-control form-select-sm'})
        self.fields['group_type_code'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['group_type_name'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['group_name'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['group_division'].widget = forms.Select(
            choices=[('', 'Pilih Kelompok')] + [(str(i), f'Kelompok {i}') for i in range(1, 11)],
            attrs={'class': 'form-control form-select-sm'})
        self.fields['group_teacher'].label = 'Guru Kelompok'
        _teacher_user_ids = User.objects.filter(
            position__position_name__iregex=r'pengajar|wali kelas'
        ).values_list('user_id', flat=True)
        self.fields['group_teacher'].queryset = Teacher.objects.select_related('user').filter(
            user__user_id__in=_teacher_user_ids
        ).order_by('user__username')
        self.fields['group_teacher'].empty_label = 'Pilih Guru'
        self.fields['group_teacher'].required = False
        self.fields['group_teacher'].label_from_instance = lambda obj: obj.user.username if obj.user else str(obj.user_id)
        self.fields['group_teacher'].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = StudyGroup
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormStudyGroupUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormStudyGroupUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['school_year'].label = 'Tahun Ajaran'
        self.fields['group_type_code'].label = 'Kode Jenis'
        self.fields['group_type_name'].label = 'Nama Jenis'
        self.fields['group_name'].label = 'Nama Kelompok'
        self.fields['group_division'].label = 'Pembagian Kelompok'
        self.fields['school_year'].queryset = SchoolYear.objects.all().order_by('-school_year_name')
        self.fields['school_year'].empty_label = 'Pilih Tahun Ajaran'
        self.fields['school_year'].label_from_instance = lambda obj: obj.school_year_name
        self.fields['school_year'].widget.attrs.update({'class': 'form-control form-select-sm'})
        self.fields['group_type_code'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['group_type_name'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['group_name'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['group_division'].widget = forms.Select(
            choices=[('', 'Pilih Kelompok')] + [(str(i), f'Kelompok {i}') for i in range(1, 11)],
            attrs={'class': 'form-control form-select-sm'})
        self.fields['group_teacher'].label = 'Guru Kelompok'
        _teacher_user_ids = User.objects.filter(
            position__position_name__iregex=r'pengajar|wali kelas'
        ).values_list('user_id', flat=True)
        self.fields['group_teacher'].queryset = Teacher.objects.select_related('user').filter(
            user__user_id__in=_teacher_user_ids
        ).order_by('user__username')
        self.fields['group_teacher'].empty_label = 'Pilih Guru'
        self.fields['group_teacher'].required = False
        self.fields['group_teacher'].label_from_instance = lambda obj: obj.user.username if obj.user else str(obj.teacher_id)
        self.fields['group_teacher'].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = StudyGroup
        exclude = ['study_group_id', 'entry_date', 'entry_by', 'update_date', 'update_by']


class FormStudyGroupView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormStudyGroupView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['school_year'] = forms.CharField(
            label='Tahun Ajaran', required=False,
            initial=(self.instance.school_year.school_year_name if self.instance and self.instance.school_year else ''),
            widget=forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'}))
        self.fields['group_type_code'].label = 'Kode Jenis'
        self.fields['group_type_name'].label = 'Nama Jenis'
        self.fields['group_name'].label = 'Nama Kelompok'
        self.fields['group_division'] = forms.CharField(
            label='Pembagian Kelompok', required=False,
            initial=(self.instance.get_group_division_display() if self.instance and self.instance.group_division else ''),
            widget=forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'}))
        self.fields['group_teacher'] = forms.CharField(
            label='Guru Kelompok', required=False,
            widget=forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'}))
        self.fields['group_type_code'].widget = forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['group_type_name'].widget = forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['group_name'].widget = forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'})

        if self.instance and self.instance.pk:
            self.initial['school_year'] = self.instance.school_year.school_year_name if self.instance.school_year else ''
            self.initial['group_division'] = self.instance.get_group_division_display() if self.instance.group_division else ''
            self.initial['group_teacher'] = self.instance.group_teacher.user.username if self.instance.group_teacher and self.instance.group_teacher.user else ''

    class Meta:
        model = StudyGroup
        fields = ['school_year', 'group_type_code', 'group_type_name',
                  'group_name', 'group_division', 'group_teacher']


EDUCATION_CHOICES = [
    ('', 'Pilih Pendidikan'),
    ('SD', 'SD'), ('SMP', 'SMP'), ('SMA', 'SMA/SMK'),
    ('D1', 'D1'), ('D2', 'D2'), ('D3', 'D3'), ('D4', 'D4'),
    ('S1', 'S1'), ('S2', 'S2'), ('S3', 'S3'),
]


class FormTeacher(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormTeacher, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['user'].label = 'Nama Guru'
        self.fields['user'].queryset = User.objects.filter(
            position__position_name__iregex=r'kepala sekolah|wali kelas|pengajar'
        ).order_by('username')
        self.fields['user'].empty_label = 'Pilih Guru'
        self.fields['user'].label_from_instance = lambda obj: obj.username
        self.fields['user'].widget.attrs.update({'class': 'form-control form-select-sm'})
        self.fields['nip'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['sex'].widget = forms.Select(
            choices=[('', 'Pilih JK'), ('L', 'Laki-Laki'), ('P', 'Perempuan')],
            attrs={'class': 'form-control form-select-sm'})
        self.fields['birth_place'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['birth_date'].widget = forms.DateInput(
            attrs={'class': 'form-control form-control-sm', 'type': 'date'})
        self.fields['address'].widget = forms.Textarea({'class': 'form-control-sm', 'rows': 2})
        self.fields['phone'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['email'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['status'].widget = forms.Select(
            choices=[('', 'Pilih Status'), ('GTY', 'Guru Tetap Yayasan'), ('GTT', 'Guru Tidak Tetap'), ('PNS', 'PNS')],
            attrs={'class': 'form-control form-select-sm'})
        self.fields['specialization'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['last_education'].widget = forms.Select(
            choices=EDUCATION_CHOICES,
            attrs={'class': 'form-control form-select-sm'})
        self.fields['last_school'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['last_school_major'].widget = forms.TextInput({'class': 'form-control-sm'})

    class Meta:
        model = Teacher
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormTeacherUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormTeacherUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['user'].label = 'Nama Guru'
        self.fields['user'].queryset = User.objects.filter(
            position__position_name__iregex=r'kepala sekolah|wali kelas|pengajar'
        ).order_by('username')
        self.fields['user'].empty_label = 'Pilih Guru'
        self.fields['user'].label_from_instance = lambda obj: obj.username
        self.fields['user'].widget.attrs.update({'class': 'form-control form-select-sm'})
        self.fields['nip'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['sex'].widget = forms.Select(
            choices=[('', 'Pilih JK'), ('L', 'Laki-Laki'), ('P', 'Perempuan')],
            attrs={'class': 'form-control form-select-sm'})
        self.fields['birth_place'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['birth_date'].widget = forms.DateInput(
            attrs={'class': 'form-control form-control-sm', 'type': 'date'})
        self.fields['address'].widget = forms.Textarea({'class': 'form-control-sm', 'rows': 2})
        self.fields['phone'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['email'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['status'].widget = forms.Select(
            choices=[('', 'Pilih Status'), ('GTY', 'Guru Tetap Yayasan'), ('GTT', 'Guru Tidak Tetap'), ('PNS', 'PNS')],
            attrs={'class': 'form-control form-select-sm'})
        self.fields['specialization'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['last_education'].widget = forms.Select(
            choices=EDUCATION_CHOICES,
            attrs={'class': 'form-control form-select-sm'})
        self.fields['last_school'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['last_school_major'].widget = forms.TextInput({'class': 'form-control-sm'})

    class Meta:
        model = Teacher
        exclude = ['teacher_id', 'entry_date', 'entry_by', 'update_date', 'update_by']


class FormTeacherView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormTeacherView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        ro = {'readonly': 'readonly'}
        self.fields['user'] = forms.CharField(
            label='Nama Guru', required=False,
            widget=forms.TextInput({'class': 'form-control-sm', **ro}))
        self.fields['sex'] = forms.CharField(
            label='Jenis Kelamin', required=False,
            widget=forms.TextInput({'class': 'form-control-sm', **ro}))
        self.fields['status'] = forms.CharField(
            label='Status', required=False,
            widget=forms.TextInput({'class': 'form-control-sm', **ro}))
        self.fields['last_education'] = forms.CharField(
            label='Pendidikan Terakhir', required=False,
            widget=forms.TextInput({'class': 'form-control-sm', **ro}))
        self.fields['nip'].widget = forms.TextInput({'class': 'form-control-sm', **ro})
        self.fields['birth_place'].widget = forms.TextInput({'class': 'form-control-sm', **ro})
        self.fields['birth_date'].widget = forms.DateInput(
            attrs={'class': 'form-control form-control-sm', 'type': 'date', **ro})
        self.fields['address'].widget = forms.Textarea({'class': 'form-control-sm', 'rows': 2, **ro})
        self.fields['phone'].widget = forms.TextInput({'class': 'form-control-sm', **ro})
        self.fields['email'].widget = forms.TextInput({'class': 'form-control-sm', **ro})
        self.fields['specialization'].widget = forms.TextInput({'class': 'form-control-sm', **ro})
        self.fields['last_school'].widget = forms.TextInput({'class': 'form-control-sm', **ro})
        self.fields['last_school_major'].widget = forms.TextInput({'class': 'form-control-sm', **ro})

        # Set nilai tampilan untuk field yang di-override
        if self.instance and self.instance.pk:
            self.initial['user'] = self.instance.user.username if self.instance.user else ''
            self.initial['sex'] = self.instance.get_sex_display() if self.instance.sex else ''
            self.initial['status'] = self.instance.get_status_display() if self.instance.status else ''
            self.initial['last_education'] = self.instance.get_last_education_display() if self.instance.last_education else ''
        self.fields['last_school_major'].widget = forms.TextInput({'class': 'form-control-sm', **ro})

    class Meta:
        model = Teacher
        fields = ['user', 'nip', 'sex', 'birth_place', 'birth_date',
                  'address', 'phone', 'email', 'status', 'specialization', 'last_education', 'last_school', 'last_school_major']


class FormSchoolYear(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSchoolYear, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['school_year_name'].label = 'Tahun Ajaran'
        self.fields['school_year_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'placeholder': '2025/2026'})

    class Meta:
        model = SchoolYear
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormSchoolYearUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSchoolYearUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['school_year_name'].label = 'Tahun Ajaran'
        self.fields['school_year_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = SchoolYear
        exclude = ['school_year_id', 'entry_date', 'entry_by',
                   'update_date', 'update_by']


class FormSchoolYearView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSchoolYearView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['school_year_name'].label = 'Tahun Ajaran'
        self.fields['school_year_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = SchoolYear
        fields = ['school_year_id', 'school_year_name']


class FormStudent(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormStudent, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['sex'] = forms.ChoiceField(
            choices=[
                ('', 'Pilih JK'),
                ('L', 'Laki-Laki'),
                ('P', 'Perempuan'),
            ],
            label='Jenis Kelamin',
            widget=forms.Select(attrs={'class': 'form-control form-select-sm'})
        )

        custom_labels = {
            'nipd': 'NIPD',
            'nisn': 'NISN',
            'nik': 'NIK',
            'religion': 'Agama',
            'name': 'Nama Santri',
            'grade': 'Kelas',
            'hostel': 'Asrama',
            'sex': 'Jenis Kelamin',
            'birth_place': 'Tempat Lahir',
            'birth_date': 'Tanggal Lahir',
            'address': 'Alamat',
            'village': 'Desa/Kelurahan',
            'sub_district': 'Kecamatan',
            'district': 'Kabupaten/Kota',
            'rt': 'RT',
            'rw': 'RW',
            'postal_code': 'Kode Pos',
            'residence_type': 'Jenis Tinggal',
            'phone': 'Telepon',
            'handphone': 'Handphone',
            'transportation': 'Alat Transportasi',
            'shkun_no': 'No. SHKUN',
            'kps_recipient': 'Penerima KPS',
            'kps_no': 'No. KPS',
            'father_name': 'Nama Ayah',
            'father_birth_year': 'Tahun Lahir Ayah',
            'father_education': 'Pendidikan Ayah',
            'father_occupation': 'Pekerjaan Ayah',
            'father_nik': 'NIK Ayah',
            'father_income': 'Penghasilan Ayah',
            'mother_name': 'Nama Ibu',
            'mother_birth_year': 'Tahun Lahir Ibu',
            'mother_education': 'Pendidikan Ibu',
            'mother_occupation': 'Pekerjaan Ibu',
            'mother_nik': 'NIK Ibu',
            'mother_income': 'Penghasilan Ibu',
            'guardian_name': 'Nama Wali',
            'guardian_birth_year': 'Tahun Lahir Wali',
            'guardian_education': 'Pendidikan Wali',
            'guardian_occupation': 'Pekerjaan Wali',
            'guardian_nik': 'NIK Wali',
            'guardian_income': 'Penghasilan Wali',
            'other_info': 'Keterangan Lain',
        }

        for field_name, field in self.fields.items():
            field.label = custom_labels.get(
                field_name, field_name.replace('_', ' ').title())

            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update(
                    {'class': 'form-control form-select-sm'})
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update(
                    {'class': 'form-control form-control-sm'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update(
                    {'class': 'form-control-sm', 'rows': 3})
            else:
                field.widget.attrs.update({'class': 'form-control-sm'})

        self.fields['grade'].queryset = Grade.objects.all().order_by(
            'grade', 'sub_grade', 'grade_name', 'school_year__school_year_name')
        self.fields['grade'].empty_label = 'Pilih Kelas'
        self.fields['grade'].label_from_instance = lambda obj: (
            f"{obj.grade}{' - ' + obj.sub_grade if obj.sub_grade else ''} | {obj.grade_name} | {obj.school_year.school_year_name}"
        )
        self.fields['hostel'].queryset = Hostel.objects.all().order_by(
            'hostel_name')
        self.fields['hostel'].empty_label = 'Pilih Asrama'
        self.fields['hostel'].label_from_instance = lambda obj: obj.hostel_name
        # Untuk field district/sub_district/village, batasi queryset agar tidak
        # load semua data (ribuan record). Saat POST, tambahkan nilai yang dikirim
        # ke queryset agar validasi ModelChoiceField tidak gagal.
        district_pk = None
        sub_district_pk = None
        village_pk = None

        if args and args[0]:  # POST data
            district_pk = args[0].get('district') or None
            sub_district_pk = args[0].get('sub_district') or None
            village_pk = args[0].get('village') or None
        elif self.instance and self.instance.pk:
            district_pk = self.instance.district_id
            sub_district_pk = self.instance.sub_district_id
            village_pk = self.instance.village_id

        district_qs = District.objects.filter(pk=district_pk) if district_pk else District.objects.none()
        sub_district_qs = SubDistrict.objects.filter(pk=sub_district_pk) if sub_district_pk else SubDistrict.objects.none()
        village_qs = Village.objects.filter(pk=village_pk) if village_pk else Village.objects.none()

        self.fields['district'].queryset = district_qs
        self.fields['district'].empty_label = 'Pilih Kabupaten/Kota'
        self.fields['district'].label_from_instance = lambda obj: obj.district_name
        self.fields['sub_district'].queryset = sub_district_qs
        self.fields['sub_district'].empty_label = 'Pilih Kecamatan'
        self.fields['sub_district'].label_from_instance = lambda obj: obj.sub_district_name
        self.fields['village'].queryset = village_qs
        self.fields['village'].empty_label = 'Pilih Desa/Kelurahan'
        self.fields['village'].label_from_instance = lambda obj: obj.village_name
        self.fields['residence_type'].queryset = ResidenceType.objects.all().order_by(
            'residence_type_name')
        self.fields['residence_type'].empty_label = 'Pilih Jenis Tinggal'
        self.fields['residence_type'].label_from_instance = lambda obj: obj.residence_type_name
        self.fields['religion'].queryset = Religion.objects.all().order_by(
            'religion_name')
        self.fields['religion'].empty_label = 'Pilih Agama'
        self.fields['religion'].label_from_instance = lambda obj: obj.religion_name

        # Set initial for autocomplete fields
        if self.instance and self.instance.pk:
            self.fields['district'].initial = self.instance.district.district_id if self.instance.district else ''
            self.fields['sub_district'].initial = self.instance.sub_district.sub_district_id if self.instance.sub_district else ''
            self.fields['village'].initial = self.instance.village.village_id if self.instance.village else ''

    def clean_district(self):
        district_value = self.cleaned_data.get('district')
        if isinstance(district_value, District):
            return district_value
        if district_value:
            try:
                return District.objects.get(pk=district_value)
            except (ValueError, District.DoesNotExist):
                try:
                    return District.objects.get(district_name=district_value)
                except District.DoesNotExist:
                    raise forms.ValidationError(
                        "Kabupaten/Kota tidak ditemukan.")
        return None

    def clean_sub_district(self):
        sub_district_value = self.cleaned_data.get('sub_district')
        if isinstance(sub_district_value, SubDistrict):
            return sub_district_value
        if sub_district_value:
            try:
                return SubDistrict.objects.get(pk=sub_district_value)
            except (ValueError, SubDistrict.DoesNotExist):
                try:
                    return SubDistrict.objects.get(sub_district_name=sub_district_value)
                except SubDistrict.DoesNotExist:
                    raise forms.ValidationError("Kecamatan tidak ditemukan.")
        return None

    def clean_village(self):
        village_value = self.cleaned_data.get('village')
        if isinstance(village_value, Village):
            return village_value
        if village_value:
            try:
                return Village.objects.get(pk=village_value)
            except (ValueError, Village.DoesNotExist):
                try:
                    return Village.objects.get(village_name=village_value)
                except Village.DoesNotExist:
                    raise forms.ValidationError(
                        "Desa/Kelurahan tidak ditemukan.")
        return None

    class Meta:
        model = Student
        exclude = ['student_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']
        widgets = {
            'birth_date': DateInput(attrs={'class': 'form-control form-control-sm'}),
            'grade': forms.Select(attrs={'class': 'form-control form-select-sm'}),
            'hostel': forms.Select(attrs={'class': 'form-control form-select-sm'}),
            'district': forms.Select(attrs={'class': 'form-control form-control-sm select2-district', 'style': 'display:none;'}),
            'sub_district': forms.Select(attrs={'class': 'form-control form-control-sm select2-subdistrict', 'style': 'display:none;'}),
            'village': forms.Select(attrs={'class': 'form-control form-control-sm select2-village', 'style': 'display:none;'}),
            'residence_type': forms.Select(attrs={'class': 'form-control form-select-sm'}),
            'religion': forms.Select(attrs={'class': 'form-control form-select-sm'}),
        }


class FormDistrict(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormDistrict, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['district_name'].label = 'Nama Kabupaten/Kota'
        self.fields['district_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'placeholder': 'Contoh: Kota Bekasi'})

    class Meta:
        model = District
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormDistrictUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormDistrictUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['district_name'].label = 'Nama Kabupaten/Kota'
        self.fields['district_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = District
        exclude = ['district_id', 'entry_date', 'entry_by',
                   'update_date', 'update_by']


class FormDistrictView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormDistrictView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['district_name'].label = 'Nama Kabupaten/Kota'
        self.fields['district_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = District
        fields = ['district_id', 'district_name']


class FormSubDistrict(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSubDistrict, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['sub_district_name'].label = 'Nama Kecamatan'
        self.fields['sub_district_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'placeholder': 'Contoh: Pondok Gede'})

    class Meta:
        model = SubDistrict
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormSubDistrictUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSubDistrictUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['sub_district_name'].label = 'Nama Kecamatan'
        self.fields['sub_district_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = SubDistrict
        exclude = ['sub_district_id', 'entry_date', 'entry_by',
                   'update_date', 'update_by']


class FormSubDistrictView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSubDistrictView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['sub_district_name'].label = 'Nama Kecamatan'
        self.fields['sub_district_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = SubDistrict
        fields = ['sub_district_id', 'sub_district_name']


class FormVillage(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormVillage, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['village_name'].label = 'Nama Desa/Kelurahan'
        self.fields['village_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'placeholder': 'Contoh: Jatiwaringin'})

    class Meta:
        model = Village
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormVillageUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormVillageUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['village_name'].label = 'Nama Desa/Kelurahan'
        self.fields['village_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Village
        exclude = ['village_id', 'entry_date', 'entry_by',
                   'update_date', 'update_by']


class FormVillageView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormVillageView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['village_name'].label = 'Nama Desa/Kelurahan'
        self.fields['village_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Village
        fields = ['village_id', 'village_name']


class FormResidenceType(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormResidenceType, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['residence_type_name'].label = 'Nama Jenis Tinggal'
        self.fields['residence_type_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'placeholder': 'Contoh: Tinggal dengan Orang Tua'})

    class Meta:
        model = ResidenceType
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormResidenceTypeUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormResidenceTypeUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['residence_type_name'].label = 'Nama Jenis Tinggal'
        self.fields['residence_type_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = ResidenceType
        exclude = ['residence_type_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormResidenceTypeView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormResidenceTypeView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['residence_type_name'].label = 'Nama Jenis Tinggal'
        self.fields['residence_type_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = ResidenceType
        fields = ['residence_type_id', 'residence_type_name']


class FormReligion(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormReligion, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['religion_name'].label = 'Nama Agama'
        self.fields['religion_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'placeholder': 'Contoh: Islam'})

    class Meta:
        model = Religion
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormReligionUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormReligionUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['religion_name'].label = 'Nama Agama'
        self.fields['religion_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Religion
        exclude = ['religion_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormReligionView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormReligionView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['religion_name'].label = 'Nama Agama'
        self.fields['religion_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Religion
        fields = ['religion_id', 'religion_name']


class FormHostel(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormHostel, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['hostel_name'].label = 'Nama Asrama'
        self.fields['hostel_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'placeholder': 'Contoh: Asrama Umar Bin Khattab'})
        self.fields['musrif'].label = 'Musrif'
        self.fields['musrif'].queryset = User.objects.filter(
            position__position_name__icontains='musrif'
        ).order_by('username')
        self.fields['musrif'].empty_label = 'Pilih Musrif'
        self.fields['musrif'].required = False
        self.fields['musrif'].label_from_instance = lambda obj: obj.username
        self.fields['musrif'].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = Hostel
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormHostelUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormHostelUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['hostel_name'].label = 'Nama Asrama'
        self.fields['hostel_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['musrif'].label = 'Musrif'
        self.fields['musrif'].queryset = User.objects.filter(
            position__position_name__icontains='musrif'
        ).order_by('username')
        self.fields['musrif'].empty_label = 'Pilih Musrif'
        self.fields['musrif'].required = False
        self.fields['musrif'].label_from_instance = lambda obj: obj.username
        self.fields['musrif'].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = Hostel
        exclude = ['hostel_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormHostelView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormHostelView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['hostel_name'].label = 'Nama Asrama'
        self.fields['hostel_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['musrif'] = forms.CharField(
            label='Musrif', required=False,
            widget=forms.TextInput({'class': 'form-control-sm', 'readonly': 'readonly'}))

        if self.instance and self.instance.pk:
            self.initial['musrif'] = self.instance.musrif.username if self.instance.musrif else ''

    class Meta:
        model = Hostel
        fields = ['hostel_id', 'hostel_name', 'musrif']


def _teacher_qs():
    return Teacher.objects.select_related('user').order_by('user__username')


def _grade_qs():
    return Grade.objects.select_related('school_year').order_by(
        '-school_year__school_year_name', 'grade', 'sub_grade')


def _grade_label(obj):
    label = obj.grade
    if obj.sub_grade:
        label += f" - {obj.sub_grade}"
    label += f" | {obj.grade_name}"
    return label


class FormHalaqohTahfidz(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['teacher'].label = 'Halaqoh (Guru)'
        self.fields['teacher'].queryset = _teacher_qs()
        self.fields['teacher'].empty_label = 'Pilih Guru'
        self.fields['teacher'].required = False
        self.fields['teacher'].label_from_instance = lambda obj: obj.user.username if obj.user else str(obj.teacher_id)
        self.fields['teacher'].widget.attrs.update({'class': 'form-control form-select-sm'})
        self.fields['grade'].label = 'Kelas'
        self.fields['grade'].queryset = _grade_qs()
        self.fields['grade'].empty_label = 'Pilih Kelas'
        self.fields['grade'].required = False
        self.fields['grade'].label_from_instance = _grade_label
        self.fields['grade'].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = HalaqohTahfidz
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormHalaqohTahfidzUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['teacher'].label = 'Halaqoh (Guru)'
        self.fields['teacher'].queryset = _teacher_qs()
        self.fields['teacher'].empty_label = 'Pilih Guru'
        self.fields['teacher'].required = False
        self.fields['teacher'].label_from_instance = lambda obj: obj.user.username if obj.user else str(obj.teacher_id)
        self.fields['teacher'].widget.attrs.update({'class': 'form-control form-select-sm'})
        self.fields['grade'].label = 'Kelas'
        self.fields['grade'].queryset = _grade_qs()
        self.fields['grade'].empty_label = 'Pilih Kelas'
        self.fields['grade'].required = False
        self.fields['grade'].label_from_instance = _grade_label
        self.fields['grade'].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = HalaqohTahfidz
        exclude = ['halaqoh_id', 'entry_date', 'entry_by', 'update_date', 'update_by']


class FormHalaqohLughoh(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['teacher'].label = 'Halaqoh (Guru)'
        self.fields['teacher'].queryset = _teacher_qs()
        self.fields['teacher'].empty_label = 'Pilih Guru'
        self.fields['teacher'].required = False
        self.fields['teacher'].label_from_instance = lambda obj: obj.user.username if obj.user else str(obj.teacher_id)
        self.fields['teacher'].widget.attrs.update({'class': 'form-control form-select-sm'})
        self.fields['grade'].label = 'Kelas'
        self.fields['grade'].queryset = _grade_qs()
        self.fields['grade'].empty_label = 'Pilih Kelas'
        self.fields['grade'].required = False
        self.fields['grade'].label_from_instance = _grade_label
        self.fields['grade'].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = HalaqohLughoh
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormHalaqohLughohUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['teacher'].label = 'Halaqoh (Guru)'
        self.fields['teacher'].queryset = _teacher_qs()
        self.fields['teacher'].empty_label = 'Pilih Guru'
        self.fields['teacher'].required = False
        self.fields['teacher'].label_from_instance = lambda obj: obj.user.username if obj.user else str(obj.teacher_id)
        self.fields['teacher'].widget.attrs.update({'class': 'form-control form-select-sm'})
        self.fields['grade'].label = 'Kelas'
        self.fields['grade'].queryset = _grade_qs()
        self.fields['grade'].empty_label = 'Pilih Kelas'
        self.fields['grade'].required = False
        self.fields['grade'].label_from_instance = _grade_label
        self.fields['grade'].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = HalaqohLughoh
        exclude = ['halaqoh_id', 'entry_date', 'entry_by', 'update_date', 'update_by']


class FormExtracurricular(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['name'].label = 'Nama Ekstrakurikuler'
        self.fields['name'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['teacher'].label = 'Penanggung Jawab'
        self.fields['teacher'].queryset = _teacher_qs()
        self.fields['teacher'].empty_label = 'Pilih Guru'
        self.fields['teacher'].required = False
        self.fields['teacher'].label_from_instance = lambda obj: obj.user.username if obj.user else str(obj.teacher_id)
        self.fields['teacher'].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = Extracurricular
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormExtracurricularUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['name'].label = 'Nama Ekstrakurikuler'
        self.fields['name'].widget = forms.TextInput({'class': 'form-control-sm'})
        self.fields['teacher'].label = 'Penanggung Jawab'
        self.fields['teacher'].queryset = _teacher_qs()
        self.fields['teacher'].empty_label = 'Pilih Guru'
        self.fields['teacher'].required = False
        self.fields['teacher'].label_from_instance = lambda obj: obj.user.username if obj.user else str(obj.teacher_id)
        self.fields['teacher'].widget.attrs.update({'class': 'form-control form-select-sm'})

    class Meta:
        model = Extracurricular
        exclude = ['extracurricular_id', 'entry_date', 'entry_by', 'update_date', 'update_by']


class FormExtracurricularView(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        ro = {'readonly': 'readonly'}
        self.fields['name'].label = 'Nama Ekstrakurikuler'
        self.fields['name'].widget = forms.TextInput({'class': 'form-control-sm', **ro})
        self.fields['teacher'] = forms.CharField(
            label='Penanggung Jawab', required=False,
            widget=forms.TextInput({'class': 'form-control-sm', **ro}))
        if self.instance and self.instance.pk:
            self.initial['teacher'] = self.instance.teacher.user.username if self.instance.teacher and self.instance.teacher.user else ''

    class Meta:
        model = Extracurricular
        fields = ['extracurricular_id', 'name', 'teacher']
