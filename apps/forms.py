from django import forms
from django.forms import ModelForm
from apps.models import *
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm, UserCreationForm
import datetime
from django.forms import DateInput
from tinymce.widgets import TinyMCE
from django.forms.widgets import TimeInput


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
