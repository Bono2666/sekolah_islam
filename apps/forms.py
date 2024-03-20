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
            {'class': 'form-control-sm'})
        self.fields['new_password1'].widget = forms.PasswordInput(
            {'class': 'form-control-sm'})
        self.fields['new_password2'].widget = forms.PasswordInput(
            {'class': 'form-control-sm'})


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


class FormDistributor(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormDistributor, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['distributor_id'].label = 'Distributor ID'
        self.fields['distributor_name'].label = 'Distributor Name'
        self.fields['sap_code'].label = 'SAP ID'
        self.fields['distributor_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['distributor_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['sap_code'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Distributor
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormDistributorView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormDistributorView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['distributor_name'].label = 'Distributor Name'
        self.fields['sap_code'].label = 'SAP ID'
        self.fields['distributor_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['sap_code'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Distributor
        fields = ['distributor_id', 'distributor_name', 'sap_code']


class FormDistributorUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormDistributorUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['distributor_name'].label = 'Distributor Name'
        self.fields['sap_code'].label = 'SAP ID'
        self.fields['distributor_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['sap_code'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Distributor
        exclude = ['distributor_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormAreaSales(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormAreaSales, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['area_id'].label = 'ID Regional'
        self.fields['area_name'].label = 'Nama Regional'
        self.fields['manager'].label = 'Manager'
        self.fields['area_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['area_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['manager'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = AreaSales
        exclude = ['bank_account', 'form', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormAreaSalesView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormAreaSalesView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['area_name'].label = 'Nama Regional'
        self.fields['manager'].label = 'Manager'
        self.fields['area_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['manager'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = AreaSales
        fields = ['area_id', 'area_name', 'manager']


class FormAreaSalesUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormAreaSalesUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['area_name'].label = 'Nama Regional'
        self.fields['manager'].label = 'Manager'
        self.fields['area_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['manager'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = AreaSales
        exclude = ['area_id', 'form', 'bank_account', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormAreaSalesDetailView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormAreaSalesDetailView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['distributor'].label = ''

    class Meta:
        model = AreaSalesDetail
        fields = ['distributor']

        widgets = {
            'distributor': forms.Select(attrs={'class': 'form-control select2 border-0 ps-1 shadow-none bg-transparent', 'disabled': 'disabled'}),
        }


class FormAreaSalesDetail(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormAreaSalesDetail, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['distributor'].label = ''

    class Meta:
        model = AreaSalesDetail
        exclude = ['area', 'entry_date',
                   'entry_by', 'update_date', 'update_by']

        widgets = {
            'distributor': forms.Select(attrs={'class': 'form-control select2 border-0 ps-1 shadow-none bg-transparent cursor-pointer', 'placeholder': 'Select Distributor'}),
        }


class FormAreaChannel(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormAreaChannel, self).__init__(*args, **kwargs)
        self.label_suffix = ''

    class Meta:
        model = AreaChannel
        exclude = ['entry_date',
                   'entry_by', 'update_date', 'update_by']


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


class FormChannel(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormChannel, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['channel_id'].label = 'Channel ID'
        self.fields['channel_name'].label = 'Channel Name'
        self.fields['channel_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['channel_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Channel
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormChannelUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormChannelUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['channel_name'].label = 'Channel Name'
        self.fields['channel_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Channel
        exclude = ['channel_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormChannelView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormChannelView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['channel_name'].label = 'Channel Name'
        self.fields['channel_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Channel
        fields = ['channel_id', 'channel_name']


class FormCuisine(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCuisine, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['cuisine_id'].label = 'ID Masakan'
        self.fields['cuisine_name'].label = 'Nama Masakan'
        self.fields['cuisine_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['cuisine_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Cuisine
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormCuisineUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCuisineUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['cuisine_name'].label = 'Nama Masakan'
        self.fields['cuisine_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Cuisine
        exclude = ['cuisine_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormCuisineView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCuisineView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['cuisine_name'].label = 'Nama Masakan'
        self.fields['cuisine_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Cuisine
        fields = ['cuisine_id', 'cuisine_name']


class FormCategory(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCategory, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['category_id'].label = 'ID Kategori'
        self.fields['category_name'].label = 'Nama Kategori'
        self.fields['category_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['category_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Category
        fields = ['category_id', 'category_name']


class FormCategoryUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCategoryUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['category_name'].label = 'Nama Kategori'
        self.fields['category_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Category
        fields = ['category_name']


class FormCategoryView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCategoryView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['category_name'].label = 'Nama Kategori'
        self.fields['category_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Category
        fields = ['category_id', 'category_name']


class FormPackage(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPackage, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['package_id'].label = 'ID Paket'
        self.fields['package_name'].label = 'Nama Paket'
        self.fields['category'].label = 'Kategori'
        self.fields['male_price'].label = 'Harga Jual Jantan'
        self.fields['female_price'].label = 'Harga Jual Betina'
        self.fields['box'].label = 'Jumlah Box'
        self.fields['quantity'].label = 'Jumlah Kambing'
        self.fields['type'].label = 'Tipe Kambing'
        self.fields['package_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['package_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['male_price'].widget = forms.NumberInput(
            {'class': 'form-control-sm no-spinners'})
        self.fields['female_price'].widget = forms.NumberInput(
            {'class': 'form-control-sm no-spinners'})
        self.fields['box'].widget = forms.NumberInput(
            {'class': 'form-control-sm no-spinners'})
        self.fields['quantity'].widget = forms.NumberInput(
            {'class': 'form-control-sm no-spinners'})

    class Meta:
        model = Package
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormPackageUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPackageUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['package_name'].label = 'Nama Paket'
        self.fields['category'].label = 'Kategori'
        self.fields['male_price'].label = 'Harga Jual Jantan'
        self.fields['female_price'].label = 'Harga Jual Betina'
        self.fields['box'].label = 'Jumlah Box'
        self.fields['quantity'].label = 'Jumlah Kambing'
        self.fields['type'].label = 'Tipe Kambing'
        self.fields['package_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['male_price'].widget = forms.NumberInput(
            {'class': 'form-control-sm no-spinners'})
        self.fields['female_price'].widget = forms.NumberInput(
            {'class': 'form-control-sm no-spinners'})
        self.fields['box'].widget = forms.NumberInput(
            {'class': 'form-control-sm no-spinners'})
        self.fields['quantity'].widget = forms.NumberInput(
            {'class': 'form-control-sm no-spinners'})

    class Meta:
        model = Package
        exclude = ['package_id', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormPackageView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPackageView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['package_name'].label = 'Nama Paket'
        self.fields['category'].label = 'Kategori'
        self.fields['male_price'].label = 'Harga Jual Jantan'
        self.fields['female_price'].label = 'Harga Jual Betina'
        self.fields['box'].label = 'Jumlah Box'
        self.fields['quantity'].label = 'Jumlah Kambing'
        self.fields['type'].label = 'Tipe Kambing'
        self.fields['package_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['male_price'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['female_price'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['box'].widget = forms.NumberInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['quantity'].widget = forms.NumberInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Package
        fields = ['package_id', 'package_name', 'category',
                  'male_price', 'female_price', 'box', 'quantity', 'type']


class FormBudget(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormBudget, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['budget_year'].label = 'Year'
        self.fields['budget_month'].label = 'Month'
        self.fields['budget_area'].label = 'Area'
        self.fields['budget_distributor'].label = 'Distributor'
        self.fields['budget_amount'].label = 'Beginning Balance'
        self.fields['budget_upping'].label = 'Upping Price'
        self.fields['budget_total'].label = 'Total Budget'
        self.fields['budget_year'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['budget_month'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['budget_amount'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})
        self.fields['budget_upping'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['budget_total'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Budget
        exclude = ['budget_id', 'budget_balance', 'budget_status', 'entry_date',
                   'entry_by', 'update_date', 'update_by']

        YEAR_CHOICES = []
        for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
            YEAR_CHOICES.append((r, r))

        MONTH_CHOICES = []
        for r in range(1, 13):
            MONTH_CHOICES.append((r, r))


class FormBudgetUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormBudgetUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['budget_upping'].label = 'Upping Price'
        self.fields['budget_upping'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})
        self.fields['budget_amount'].label = 'Beginning Balance'
        self.fields['budget_amount'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners', 'readonly': 'readonly'})

    class Meta:
        model = Budget
        fields = ['budget_upping', 'budget_amount']


class FormNewBudgetUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormNewBudgetUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['budget_amount'].label = 'Beginning Balance'
        self.fields['budget_amount'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})
        self.fields['budget_upping'].label = 'Upping Price'
        self.fields['budget_upping'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners', 'readonly': 'readonly'})

    class Meta:
        model = Budget
        fields = ['budget_amount', 'budget_upping']


class FormBudgetView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormBudgetView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['budget_year'].label = 'Year'
        self.fields['budget_month'].label = 'Month'
        self.fields['budget_area'].label = 'Area'
        self.fields['budget_distributor'].label = 'Distributor'
        self.fields['budget_amount'].label = 'Beginning Balance'
        self.fields['budget_upping'].label = 'Upping Price'
        self.fields['budget_total'].label = 'Total Budget'
        self.fields['budget_amount'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['budget_upping'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['budget_total'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Budget
        fields = ['budget_id', 'budget_year', 'budget_month', 'budget_area',
                  'budget_distributor', 'budget_amount', 'budget_upping', 'budget_total']

        widgets = {
            'budget_area': forms.Select(attrs={'class': 'form-control form-select-sm', 'disabled': 'disabled'}),
            'budget_distributor': forms.Select(attrs={'class': 'form-control form-select-sm', 'disabled': 'disabled'}),
        }


class FormBudgetDetailUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormBudgetDetailUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['budget_percent'].label = 'Percent'
        self.fields['budget_percent'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})

    class Meta:
        model = BudgetDetail
        fields = ['budget_percent']


class FormBudgetDetailView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormBudgetDetailView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['budget_percent'].widget = forms.NumberInput(
            attrs={'class': 'form-control', 'readonly': 'readonly'})

    class Meta:
        model = BudgetDetail
        fields = ['budget_percent']


class FormBudgetApproval(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormBudgetApproval, self).__init__(*args, **kwargs)
        self.label_suffix = ''

    class Meta:
        model = BudgetApproval
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormProposalMatrix(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormProposalMatrix, self).__init__(*args, **kwargs)
        self.label_suffix = ''

    class Meta:
        model = ProposalMatrix
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


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


class FormProposal(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormProposal, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['proposal_id'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['proposal_date'].label = 'Date'
        self.fields['proposal_date'].widget = forms.DateInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['proposal_date'].input_formats = ['%d/%m/%Y']
        self.fields['proposal_date'].initial = datetime.date.today().strftime(
            '%d/%m/%Y')
        self.fields['type'].label = 'Type'
        self.fields['type'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['division'].label = 'Division'
        self.fields['program_name'].label = 'Program Name'
        self.fields['program_name'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['products'].label = 'Products'
        self.fields['products'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['area'].widget = forms.TextInput(
            attrs={'class': 'd-none', })
        self.fields['period_start'].label = 'Period (Start)'
        self.fields['period_end'].label = 'Period (End)'
        self.fields['background'].label = 'Background'
        self.fields['background'].widget = forms.Textarea(
            attrs={'class': 'form-control-sm', 'rows': 3})
        self.fields['objectives'].label = 'Objectives'
        self.fields['objectives'].widget = forms.Textarea(
            attrs={'class': 'form-control-sm', 'rows': 3})
        self.fields['mechanism'].label = 'Mechanism'
        self.fields['mechanism'].widget = forms.Textarea(
            attrs={'class': 'form-control-sm', 'rows': 3})
        self.fields['remarks'].label = 'Remarks'
        self.fields['remarks'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['attachment'].label = 'Attachment'
        self.fields['attachment'].required = False

    class Meta:
        model = Proposal
        exclude = ['budget', 'channel', 'duration', 'total_cost', 'roi', 'claim', 'balance', 'status', 'seq_number', 'proposal_claim', 'proposal_status', 'entry_date',
                   'entry_by', 'update_date', 'update_by', 'entry_pos']

        widgets = {
            'division': forms.Select(attrs={'class': 'form-control form-select-sm'}),
            # Set the date picker for period_start and period_end fields
            'period_start': DateInput(attrs={'class': 'form-control form-control-sm', 'data-provide': 'datepicker', 'data-date-format': 'dd/mm/yyyy'}),
            'period_end': DateInput(attrs={'class': 'form-control form-control-sm', 'data-provide': 'datepicker', 'data-date-format': 'dd/mm/yyyy'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control form-control-sm'}),
        }


class FormIncrementalSales(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormIncrementalSales, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['product'].label = 'Product'
        self.fields['product'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['swop_carton'].label = 'Carton'
        self.fields['swop_carton'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})
        self.fields['swop_nom'].label = 'Rp'
        self.fields['swop_nom'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})
        self.fields['swp_carton'].label = 'Carton'
        self.fields['swp_carton'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})
        self.fields['swp_nom'].label = 'Rp'
        self.fields['swp_nom'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})

    class Meta:
        model = IncrementalSales
        fields = ['product', 'swop_carton',
                  'swop_nom', 'swp_carton', 'swp_nom']


class FormProjectedCost(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormProjectedCost, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['activities'].label = 'Activities'
        self.fields['activities'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['cost'].label = 'Cost'
        self.fields['cost'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})

    class Meta:
        model = ProjectedCost
        exclude = ['proposal', 'entry_date',
                   'entry_by', 'update_date', 'update_by']


class FormProposalView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormProposalView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['proposal_date'].label = 'Date'
        self.fields['channel'].label = 'Channel'
        self.fields['channel'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['type'].label = 'Type'
        self.fields['type'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['division'].label = 'Division'
        self.fields['program_name'].label = 'Program Name'
        self.fields['program_name'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['products'].label = 'Products'
        self.fields['products'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['area'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['period_start'].label = 'Start'
        self.fields['period_end'].label = 'End'
        self.fields['duration'].label = 'Duration'
        self.fields['duration'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['background'].label = 'Background'
        self.fields['background'].widget = forms.Textarea(
            attrs={'class': 'form-control-sm', 'rows': 3, 'readonly': 'readonly'})
        self.fields['objectives'].label = 'Objectives'
        self.fields['objectives'].widget = forms.Textarea(
            attrs={'class': 'form-control-sm', 'rows': 3, 'readonly': 'readonly'})
        self.fields['mechanism'].label = 'Mechanism'
        self.fields['mechanism'].widget = forms.Textarea(
            attrs={'class': 'form-control-sm', 'rows': 3, 'readonly': 'readonly'})
        self.fields['remarks'].label = 'Remarks'
        self.fields['remarks'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['attachment'].label = 'Attachment'
        self.fields['attachment'].widget = forms.FileInput(
            attrs={'class': 'form-control form-control-sm', 'disabled': 'disabled'})

    class Meta:
        model = Proposal
        fields = ['proposal_id', 'proposal_date', 'channel', 'type', 'division', 'program_name', 'products', 'area',
                  'period_start', 'period_end', 'duration', 'background', 'objectives', 'mechanism', 'remarks', 'attachment']

        widgets = {
            'proposal_date': DateInput(attrs={'class': 'form-control form-control-sm', 'disabled': 'disabled'}),
            'period_start': DateInput(attrs={'class': 'form-control form-control-sm', 'disabled': 'disabled'}),
            'period_end': DateInput(attrs={'class': 'form-control form-control-sm', 'disabled': 'disabled'}),
        }


class FormProposalUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormProposalUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['area'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['program_name'].label = 'Program Name'
        self.fields['program_name'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['proposal_date'].label = 'Date'
        self.fields['proposal_date'].widget = forms.DateInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['type'].label = 'Type'
        self.fields['type'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['products'].label = 'Products'
        self.fields['products'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['period_start'].label = 'Period (Start)'
        self.fields['period_end'].label = 'Period (End)'
        self.fields['background'].label = 'Background'
        self.fields['background'].widget = forms.Textarea(
            attrs={'class': 'form-control-sm', 'rows': 3})
        self.fields['objectives'].label = 'Objectives'
        self.fields['objectives'].widget = forms.Textarea(
            attrs={'class': 'form-control-sm', 'rows': 3})
        self.fields['mechanism'].label = 'Mechanism'
        self.fields['mechanism'].widget = forms.Textarea(
            attrs={'class': 'form-control-sm', 'rows': 3})
        self.fields['remarks'].label = 'Remarks'
        self.fields['remarks'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['attachment'].label = 'Attachment'
        self.fields['attachment'].required = False

    class Meta:
        model = Proposal
        exclude = ['proposal_id', 'budget', 'channel', 'duration', 'total_cost', 'roi', 'claim', 'balance', 'status', 'seq_number', 'entry_date', 'entry_pos', 'proposal_claim',
                   'entry_by', 'update_date', 'update_by']

        widgets = {
            'division': forms.Select(attrs={'class': 'form-control form-select-sm'}),
            'period_start': DateInput(attrs={'class': 'form-control form-control-sm'}),
            'period_end': DateInput(attrs={'class': 'form-control form-control-sm'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control form-control-sm'}),
        }


class FormProgram(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormProgram, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['area'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['deadline'].label = 'Claim Deadline'

    class Meta:
        model = Program
        fields = ['area', 'deadline', 'content', 'approval']

        widgets = {
            'deadline': DateInput(attrs={'class': 'form-control form-control-sm'}),
            'content': TinyMCE(attrs={'cols': 80, 'rows': 30}),
            'approval': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }


class FormProgramView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormProgramView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['deadline'].label = 'Claim Deadline'

    class Meta:
        model = Program
        fields = ['deadline', 'content']

        widgets = {
            'deadline': DateInput(attrs={'class': 'form-control form-control-sm', 'disabled': 'disabled'}),
            'content': TinyMCE(attrs={'cols': 80, 'rows': 30, 'readonly': 'readonly'}),
        }


class FormProgramUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormProgramUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['deadline'].label = 'Claim Deadline'

    class Meta:
        model = Program
        fields = ['deadline', 'content']

        widgets = {
            'deadline': DateInput(attrs={'class': 'form-control form-control-sm'}),
            'content': TinyMCE(attrs={'cols': 80, 'rows': 30}),
        }


class FormProgramMatrix(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormProgramMatrix, self).__init__(*args, **kwargs)
        self.label_suffix = ''

    class Meta:
        model = ProgramMatrix
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormClaim(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormClaim, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['claim_id'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['claim_date'].label = 'Date'
        self.fields['claim_date'].widget = forms.DateInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['claim_date'].input_formats = ['%d/%m/%Y']
        self.fields['claim_date'].initial = datetime.date.today().strftime(
            '%d/%m/%Y')
        self.fields['area'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['invoice'].label = 'Invoice No.'
        self.fields['invoice'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['invoice_date'].label = 'Invoice Date'
        self.fields['due_date'].label = 'Due Date'
        self.fields['amount'].label = 'Amount'
        self.fields['amount'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})
        self.fields['remarks'].label = 'Remarks'
        self.fields['remarks'].required = False
        self.fields['additional_proposal'].label = 'Additional Proposal'
        self.fields['additional_proposal'].required = False

    class Meta:
        model = Claim
        exclude = ['program', 'status', 'tax', 'total', 'total_claim', 'seq_number', 'entry_pos', 'entry_date', 'additional_amount',
                   'entry_by', 'update_date', 'update_by']

        widgets = {
            'remarks': forms.Textarea(attrs={'class': 'form-control-sm', 'rows': 3}),
            'invoice_date': DateInput(attrs={'class': 'form-control form-control-sm', 'data-provide': 'datepicker', 'data-date-format': 'dd/mm/yyyy'}),
            'due_date': DateInput(attrs={'class': 'form-control form-control-sm', 'data-provide': 'datepicker', 'data-date-format': 'dd/mm/yyyy'}),
        }


class FormClaimView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormClaimView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['area'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['claim_date'].label = 'Date'
        self.fields['invoice'].label = 'Invoice No.'
        self.fields['invoice'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['invoice_date'].label = 'Invoice Date'
        self.fields['due_date'].label = 'Due Date'
        self.fields['amount'].label = 'Amount'
        self.fields['amount'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['tax'].label = 'Tax'
        self.fields['tax'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners', 'readonly': 'readonly'})
        self.fields['total'].label = 'Total'
        self.fields['total'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners', 'readonly': 'readonly'})
        self.fields['additional_proposal'].label = 'Additional Proposal'
        self.fields['additional_amount'].label = 'Additional Amount'
        self.fields['remarks'].label = 'Remarks'

    class Meta:
        model = Claim
        exclude = ['claim_id', 'proposal', 'program', 'status', 'seq_number', 'entry_date',
                   'entry_by', 'update_date', 'update_by']

        widgets = {
            'remarks': forms.Textarea(attrs={'class': 'form-control-sm', 'rows': 3, 'readonly': 'readonly'}),
            'claim_date': DateInput(attrs={'class': 'form-control form-control-sm', 'readonly': 'readonly'}),
            'invoice_date': DateInput(attrs={'class': 'form-control form-control-sm', 'readonly': 'readonly'}),
            'due_date': DateInput(attrs={'class': 'form-control form-control-sm', 'readonly': 'readonly'}),
        }


class FormClaimUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormClaimUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['area'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['claim_date'].label = 'Date'
        self.fields['claim_date'].widget = forms.DateInput(
            attrs={'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['claim_date'].input_formats = ['%d/%m/%Y']
        self.fields['invoice'].label = 'Invoice No.'
        self.fields['invoice'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['invoice_date'].label = 'Invoice Date'
        self.fields['due_date'].label = 'Due Date'
        self.fields['amount'].label = 'Amount'
        self.fields['amount'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})
        self.fields['remarks'].label = 'Remarks'
        self.fields['remarks'].required = False
        self.fields['additional_proposal'].label = 'Additional Proposal'
        self.fields['additional_proposal'].required = False

    class Meta:
        model = Claim
        exclude = ['claim_id', 'proposal', 'program', 'status', 'tax', 'total', 'total_claim', 'seq_number', 'entry_pos', 'entry_date', 'additional_amount',
                   'entry_by', 'update_date', 'update_by']

        widgets = {
            'remarks': forms.Textarea(attrs={'class': 'form-control-sm', 'rows': 3}),
            'invoice_date': DateInput(attrs={'class': 'form-control form-control-sm'}),
            'due_date': DateInput(attrs={'class': 'form-control form-control-sm'}),
        }


class FormRegion(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormRegion, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['region_id'].label = 'Region ID'
        self.fields['region_id'].widget = forms.TextInput(
            {'class': 'form-control-sm text-uppercase'})
        self.fields['region_name'].label = 'Region Name'
        self.fields['region_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Region
        fields = ['region_id', 'region_name']


class FormRegionUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormRegionUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['region_name'].label = 'Region Name'
        self.fields['region_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Region
        fields = ['region_name']


class FormRegionView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormRegionView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['region_name'].label = 'Region Name'
        self.fields['region_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Region
        fields = ['region_id', 'region_name']


class FormCustomer(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCustomer, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['customer_name'].label = 'Nama Customer'
        self.fields['customer_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['customer_address'].label = 'Alamat'
        self.fields['customer_address'].widget = forms.Textarea(
            {'class': 'form-control-sm', 'rows': 4})
        self.fields['customer_district'].label = 'Kecamatan'
        self.fields['customer_district'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['customer_city'].label = 'Kota'
        self.fields['customer_city'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['customer_province'].label = 'Propinsi'
        self.fields['customer_province'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['customer_phone'].label = 'Telepon'
        self.fields['customer_phone'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['customer_email'].label = 'Email'
        self.fields['customer_email'].widget = forms.EmailInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Customer
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormCustomerUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCustomerUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['customer_name'].label = 'Nama Customer'
        self.fields['customer_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['customer_address'].label = 'Alamat'
        self.fields['customer_address'].widget = forms.Textarea(
            {'class': 'form-control-sm', 'rows': 4})
        self.fields['customer_district'].label = 'Kecamatan'
        self.fields['customer_district'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['customer_city'].label = 'Kota'
        self.fields['customer_city'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['customer_province'].label = 'Propinsi'
        self.fields['customer_province'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['customer_phone'].label = 'Telepon'
        self.fields['customer_phone'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['customer_email'].label = 'Email'
        self.fields['customer_email'].widget = forms.EmailInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = Customer
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']


class FormCustomerView(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCustomerView, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['customer_name'].label = 'Nama Customer'
        self.fields['customer_name'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['customer_address'].label = 'Alamat'
        self.fields['customer_address'].widget = forms.Textarea(
            {'class': 'form-control-sm', 'rows': 4, 'readonly': 'readonly'})
        self.fields['customer_district'].label = 'Kecamatan'
        self.fields['customer_district'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['customer_city'].label = 'Kota'
        self.fields['customer_city'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['customer_province'].label = 'Propinsi'
        self.fields['customer_province'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['customer_phone'].label = 'Telepon'
        self.fields['customer_phone'].widget = forms.TextInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})
        self.fields['customer_email'].label = 'Email'
        self.fields['customer_email'].widget = forms.EmailInput(
            {'class': 'form-control-sm', 'readonly': 'readonly'})

    class Meta:
        model = Customer
        fields = ['customer_id', 'customer_name', 'customer_address',
                  'customer_district', 'customer_city', 'customer_province', 'customer_phone', 'customer_email']


class FormCustomerDetail(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormCustomerDetail, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['child_name'].label = 'Nama Anak'
        self.fields['child_name'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['child_birth'].label = 'Tanggal Lahir'
        self.fields['child_sex'].label = 'Jenis Kelamin'
        self.fields['child_sex'].widget = forms.Select(
            attrs={'class': 'form-control-sm'})
        self.fields['child_father'].label = 'Nama Ayah'
        self.fields['child_father'].widget = forms.TextInput(
            {'class': 'form-control-sm'})
        self.fields['child_mother'].label = 'Nama Ibu'
        self.fields['child_mother'].widget = forms.TextInput(
            {'class': 'form-control-sm'})

    class Meta:
        model = CustomerDetail
        exclude = ['customer', 'entry_date', 'entry_by',
                   'update_date', 'update_by']

        widgets = {
            'child_birth': DateInput(attrs={'class': 'form-control form-control-sm', 'data-provide': 'datepicker', 'data-date-format': 'dd/mm/yyyy', 'default': datetime.date.today().strftime('%d/%m/%Y')}),
        }


class FormOrder(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormOrder, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['order_id'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['order_date'].widget = forms.DateInput(
            attrs={'class': 'form-control-sm d-none', 'readonly': 'readonly'})
        self.fields['order_date'].input_formats = ['%d/%m/%Y']
        self.fields['order_date'].initial = datetime.date.today().strftime(
            '%d/%m/%Y')
        self.fields['customer_name'].label = 'Nama Lengkap Pemesan'
        self.fields['customer_name'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['customer_phone'].label = 'Telepon'
        self.fields['customer_phone'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['customer_email'].label = 'Email'
        self.fields['customer_email'].widget = forms.EmailInput(
            attrs={'class': 'form-control-sm'})
        self.fields['customer_address'].label = 'Alamat Lengkap Pengiriman'
        self.fields['customer_district'].label = 'Kecamatan'
        self.fields['customer_district'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['customer_city'].label = 'Kota/Kabupaten'
        self.fields['customer_city'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['customer_province'].label = 'Propinsi'
        self.fields['customer_province'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['delivery_date'].label = 'Tanggal Pengiriman'
        self.fields['time_arrival'].label = 'Jam Tiba di Lokasi'

    class Meta:
        model = Order
        fields = ['order_id', 'order_date', 'customer_name', 'customer_phone', 'customer_email', 'customer_address',
                  'customer_district', 'customer_city', 'customer_province', 'delivery_date', 'time_arrival']

        widgets = {
            'customer_address': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 4}),
            'delivery_date': DateInput(attrs={'class': 'form-control form-control-sm', 'data-provide': 'datepicker', 'data-date-format': 'dd/mm/yyyy'}),
            'time_arrival': TimeInput(attrs={'class': 'form-control form-control-sm', 'data-provide': 'timepicker', 'data-time-format': 'HH:ii', 'type': 'time'}),
        }


class FormOrderUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormOrderUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['order_id'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['order_date'].widget = forms.DateInput(
            attrs={'class': 'form-control-sm d-none', 'readonly': 'readonly'})
        self.fields['customer_name'].label = 'Nama Lengkap Pemesan'
        self.fields['customer_name'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['customer_phone'].label = 'Telepon'
        self.fields['customer_phone'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['customer_email'].label = 'Email'
        self.fields['customer_email'].widget = forms.EmailInput(
            attrs={'class': 'form-control-sm'})
        self.fields['customer_address'].label = 'Alamat Lengkap Pengiriman'
        self.fields['customer_district'].label = 'Kecamatan'
        self.fields['customer_district'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['customer_city'].label = 'Kota/Kabupaten'
        self.fields['customer_city'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['customer_province'].label = 'Propinsi'
        self.fields['customer_province'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['delivery_date'].label = 'Tanggal Pengiriman'
        self.fields['time_arrival'].label = 'Jam Tiba di Lokasi'

    class Meta:
        model = Order
        fields = ['order_id', 'order_date', 'customer_name', 'customer_phone', 'customer_email', 'customer_address',
                  'customer_district', 'customer_city', 'customer_province', 'delivery_date', 'time_arrival']

        widgets = {
            'customer_address': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 4}),
            'delivery_date': DateInput(attrs={'class': 'form-control form-control-sm', 'data-provide': 'datepicker', 'data-date-format': 'dd/mm/yyyy'}),
            'time_arrival': TimeInput(attrs={'class': 'form-control form-control-sm', 'data-provide': 'timepicker', 'data-time-format': 'HH:ii', 'type': 'time'}),
        }


class FormOrderChild(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormOrderChild, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['order'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['child_name'].label = 'Nama Anak'
        self.fields['child_name'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['child_birth'].label = 'Tanggal Lahir'
        self.fields['child_sex'].label = 'Jenis Kelamin'
        self.fields['child_father'].label = 'Nama Ayah'
        self.fields['child_father'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['child_mother'].label = 'Nama Ibu'
        self.fields['child_mother'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})

    class Meta:
        model = OrderChild
        exclude = ['entry_date', 'entry_by', 'update_date', 'update_by']

        widgets = {
            'child_birth': DateInput(attrs={'class': 'form-control form-control-sm', 'data-provide': 'datepicker', 'data-date-format': 'dd/mm/yyyy'}),
        }


class FormOrderChildUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormOrderChildUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['child_name'].label = 'Nama Anak'
        self.fields['child_name'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['child_birth'].label = 'Tanggal Lahir'
        self.fields['child_sex'].label = 'Jenis Kelamin'
        self.fields['child_father'].label = 'Nama Ayah'
        self.fields['child_father'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})
        self.fields['child_mother'].label = 'Nama Ibu'
        self.fields['child_mother'].widget = forms.TextInput(
            attrs={'class': 'form-control-sm'})

    class Meta:
        model = OrderChild
        exclude = ['order', 'entry_date',
                   'entry_by', 'update_date', 'update_by']

        widgets = {
            'child_birth': DateInput(attrs={'class': 'form-control form-control-sm', 'data-provide': 'datepicker', 'data-date-format': 'dd/mm/yyyy'}),
        }


class FormOrderPackage(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormOrderPackage, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['order'].widget = forms.TextInput(
            attrs={'class': 'd-none'})
        self.fields['quantity'].label = 'Jumlah Paket'
        self.fields['box_type'].label = 'Jenis Box'
        self.fields['total_price'].label = 'Total Harga'
        self.fields['quantity'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners'})
        self.fields['total_price'].widget = forms.NumberInput(
            attrs={'class': 'form-control-sm no-spinners', 'readonly': 'readonly'})

    class Meta:
        model = OrderPackage
        exclude = ['category', 'package', 'entry_date', 'main_cuisine', 'sub_cuisine', 'side_cuisine1', 'side_cuisine2', 'side_cuisine3', 'side_cuisine4', 'side_cuisine5', 'unit_price',
                   'entry_by', 'update_date', 'update_by']


class FormOrderConfirmUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormOrderConfirmUpdate, self).__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['order_note'].label = 'Catatan Pemesanan (Jika Ada)'
        self.fields['order_note'].required = False

    class Meta:
        model = Order
        fields = ['order_note']

        widgets = {
            'order_note': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3}),
        }
