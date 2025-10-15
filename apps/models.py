from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from crum import get_current_user
from decimal import Decimal
from re import sub
from django.db import models
from tinymce.models import HTMLField


class User(AbstractUser):
    is_active = models.BooleanField(default=True)
    user_id = models.CharField(max_length=50, primary_key=True)
    username = models.CharField(max_length=50)
    position = models.ForeignKey(
        'Position', on_delete=models.CASCADE, null=True)
    signature = models.ImageField(upload_to='signature/', null=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(User, self).save(*args, **kwargs)

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username


class Position(models.Model):
    position_id = models.CharField(
        max_length=3, primary_key=True, help_text='Max 3 digits Position shortname.')
    position_name = models.CharField(max_length=50)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.position_id = self.position_id.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Position, self).save(*args, **kwargs)

    def __str__(self):
        return self.position_name


class Menu(models.Model):
    menu_id = models.CharField(max_length=50, primary_key=True)
    menu_name = models.CharField(max_length=50)
    menu_remark = models.CharField(max_length=200, null=True, blank=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.menu_id = self.menu_id.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Menu, self).save(*args, **kwargs)

    def __str__(self):
        return self.menu_name


class Auth(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    add = models.BooleanField(default=False)
    edit = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'menu'], name='unique_user_menu')
        ]

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Auth, self).save(*args, **kwargs)

    def __str__(self):
        return self.menu.menu_name


class UploadLog(models.Model):
    document = models.CharField(max_length=50)
    document_id = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(UploadLog, self).save(*args, **kwargs)


class Closing(models.Model):
    document = models.CharField(max_length=50, primary_key=True)
    year_closed = models.CharField(max_length=4)
    month_closed = models.CharField(max_length=2)
    year_open = models.CharField(max_length=4)
    month_open = models.CharField(max_length=2)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.document = self.document.upper().replace(' ', '_')
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Closing, self).save(*args, **kwargs)


class Division(models.Model):
    division_id = models.BigAutoField(primary_key=True)
    division_name = models.CharField(max_length=50)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Division, self).save(*args, **kwargs)

    def __str__(self):
        return self.division_name


class Level(models.Model):
    level_id = models.CharField(max_length=3, primary_key=True)
    level_name = models.CharField(max_length=50)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.level_id = self.level_id.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Level, self).save(*args, **kwargs)

    def __str__(self):
        return self.level_name


class Grade(models.Model):
    grade_id = models.CharField(max_length=1, primary_key=True)
    grade_name = models.CharField(max_length=50)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.grade_id = self.grade_id.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Grade, self).save(*args, **kwargs)

    def __str__(self):
        return self.grade_name


class Teaching_Class(models.Model):
    class_code = models.CharField(max_length=7, primary_key=True)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    sub_grade = models.CharField(max_length=50)
    class_name = models.CharField(max_length=50)
    school_year = models.CharField(max_length=9)
    homeroom_teacher_1 = models.CharField(
        max_length=100, null=True, blank=True)
    homeroom_teacher_2 = models.CharField(
        max_length=100, null=True, blank=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Grade, self).save(*args, **kwargs)

    def __str__(self):
        return self.class_name


class Student(models.Model):
    student_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    class_code = models.ForeignKey(Teaching_Class, on_delete=models.CASCADE)
    hostel = models.CharField(max_length=50)
    sex = models.CharField(max_length=1)
    birth_place = models.CharField(max_length=50)
    birth_date = models.DateField()
    address = models.CharField(max_length=200)
    village = models.CharField(max_length=50)
    sub_district = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    rt = models.CharField(max_length=3)
    rw = models.CharField(max_length=3)
    postal_code = models.CharField(max_length=10)
    residence_type = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.CharField(max_length=50, null=True, blank=True)
    shkun_no = models.CharField(max_length=50, null=True, blank=True)
    kps_recipient = models.CharField(max_length=50, null=True, blank=True)
    kps_no = models.CharField(max_length=50, null=True, blank=True)
    nipd = models.CharField(max_length=50, null=True, blank=True)
    nisn = models.CharField(max_length=50, null=True, blank=True)
    nik = models.CharField(max_length=50, null=True, blank=True)
    religion = models.CharField(max_length=50, null=True, blank=True)
    transportation = models.CharField(max_length=50, null=True, blank=True)
    handphone = models.CharField(max_length=15, null=True, blank=True)
    father_name = models.CharField(max_length=100, null=True, blank=True)
    father_birth_year = models.CharField(max_length=4, null=True, blank=True)
    father_education = models.CharField(max_length=50, null=True, blank=True)
    father_occupation = models.CharField(max_length=50, null=True, blank=True)
    father_nik = models.CharField(max_length=50, null=True, blank=True)
    father_income = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)
    mother_name = models.CharField(max_length=100, null=True, blank=True)
    mother_birth_year = models.CharField(max_length=4, null=True, blank=True)
    mother_education = models.CharField(max_length=50, null=True, blank=True)
    mother_occupation = models.CharField(max_length=50, null=True, blank=True)
    mother_nik = models.CharField(max_length=50, null=True, blank=True)
    mother_income = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)
    guardian_name = models.CharField(max_length=100, null=True, blank=True)
    guardian_birth_year = models.CharField(max_length=4, null=True, blank=True)
    guardian_education = models.CharField(max_length=50, null=True, blank=True)
    guardian_occupation = models.CharField(
        max_length=50, null=True, blank=True)
    guardian_nik = models.CharField(max_length=50, null=True, blank=True)
    guardian_income = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True)
    other_info = models.CharField(max_length=200, null=True, blank=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Student, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
