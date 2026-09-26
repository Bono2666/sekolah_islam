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


class TeacherStatus(models.Model):
    status_id = models.CharField(
        max_length=10, primary_key=True, help_text='Max 10 digits Status shortname.')
    status_name = models.CharField(max_length=50)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True)
    update_by = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.status_id = self.status_id.upper()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(TeacherStatus, self).save(*args, **kwargs)

    def __str__(self):
        return self.status_name


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
    SEMESTER_CHOICES = [('1', 'Semester 1'), ('2', 'Semester 2')]

    grade_id = models.CharField(max_length=7, primary_key=True, default='')
    grade = models.CharField(max_length=2, default='')
    sub_grade = models.CharField(max_length=50, null=True, blank=True)
    grade_name = models.CharField(max_length=50)
    level = models.ForeignKey(
        'Level', on_delete=models.PROTECT, null=True, blank=True)
    school_year = models.ForeignKey(
        'SchoolYear', on_delete=models.PROTECT, null=True, blank=True)
    semester = models.CharField(
        max_length=1, choices=SEMESTER_CHOICES, null=True, blank=True)
    homeroom_teacher_1 = models.ForeignKey(
        'Teacher', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='homeroom_teacher_1_of', verbose_name='Wali Kelas 1')
    homeroom_teacher_2 = models.ForeignKey(
        'Teacher', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='homeroom_teacher_2_of', verbose_name='Wali Kelas 2')
    class_leader = models.ForeignKey(
        'Student', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='class_leader_of')
    vice_class_leader = models.ForeignKey(
        'Student', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='vice_class_leader_of')
    secretary = models.ForeignKey(
        'Student', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='secretary_of')
    treasurer = models.ForeignKey(
        'Student', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='treasurer_of')
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


class SchoolYear(models.Model):
    school_year_id = models.BigAutoField(primary_key=True)
    school_year_name = models.CharField(max_length=9, unique=True)
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
        super(SchoolYear, self).save(*args, **kwargs)

    def __str__(self):
        return self.school_year_name


class ResidenceType(models.Model):
    residence_type_id = models.BigAutoField(primary_key=True)
    residence_type_name = models.CharField(max_length=50, unique=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.residence_type_name = self.residence_type_name.strip()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(ResidenceType, self).save(*args, **kwargs)

    def __str__(self):
        return self.residence_type_name


class Religion(models.Model):
    religion_id = models.BigAutoField(primary_key=True)
    religion_name = models.CharField(max_length=50, unique=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.religion_name = self.religion_name.strip()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Religion, self).save(*args, **kwargs)

    def __str__(self):
        return self.religion_name


class District(models.Model):
    district_id = models.BigAutoField(primary_key=True)
    district_name = models.CharField(max_length=100, unique=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.district_name = self.district_name.strip()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(District, self).save(*args, **kwargs)

    def __str__(self):
        return self.district_name


class SubDistrict(models.Model):
    sub_district_id = models.BigAutoField(primary_key=True)
    sub_district_name = models.CharField(max_length=100, unique=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.sub_district_name = self.sub_district_name.strip()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(SubDistrict, self).save(*args, **kwargs)

    def __str__(self):
        return self.sub_district_name


class Village(models.Model):
    village_id = models.BigAutoField(primary_key=True)
    village_name = models.CharField(max_length=100, unique=True)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.village_name = self.village_name.strip()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Village, self).save(*args, **kwargs)

    def __str__(self):
        return self.village_name


class Hostel(models.Model):
    hostel_id = models.BigAutoField(primary_key=True)
    hostel_name = models.CharField(max_length=50, unique=True)
    musrif = models.ForeignKey(
        'User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='musrif_of', verbose_name='Musrif',
        limit_choices_to={'position__position_name__icontains': 'musrif'})
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.hostel_name = self.hostel_name.strip()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Hostel, self).save(*args, **kwargs)

    def __str__(self):
        return self.hostel_name


class Student(models.Model):
    student_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, null=True, blank=True)
    hostel = models.ForeignKey(
        Hostel, on_delete=models.PROTECT, null=True, blank=True)
    sex = models.CharField(max_length=1)
    birth_place = models.CharField(max_length=50)
    birth_date = models.DateField()
    address = models.CharField(max_length=200)
    village = models.ForeignKey(Village, on_delete=models.PROTECT)
    sub_district = models.ForeignKey(SubDistrict, on_delete=models.PROTECT)
    district = models.ForeignKey(District, on_delete=models.PROTECT)
    rt = models.CharField(max_length=3)
    rw = models.CharField(max_length=3)
    postal_code = models.CharField(max_length=10)
    residence_type = models.ForeignKey(ResidenceType, on_delete=models.PROTECT)
    phone = models.CharField(max_length=15)
    email = models.CharField(max_length=50, null=True, blank=True)
    shkun_no = models.CharField(max_length=50, null=True, blank=True)
    kps_recipient = models.CharField(max_length=50, null=True, blank=True)
    kps_no = models.CharField(max_length=50, null=True, blank=True)
    nipd = models.CharField(max_length=50, null=True, blank=True)
    nisn = models.CharField(max_length=50, null=True, blank=True)
    nik = models.CharField(max_length=50, null=True, blank=True)
    religion = models.ForeignKey(
        Religion, on_delete=models.PROTECT, null=True, blank=True)
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


class StudyGroup(models.Model):
    GROUP_CHOICES = [(str(i), f'Kelompok {i}') for i in range(1, 11)]

    study_group_id = models.BigAutoField(primary_key=True)
    school_year = models.ForeignKey(
        'SchoolYear', on_delete=models.PROTECT, null=True, blank=True)
    group_type_code = models.CharField(max_length=10, null=True, blank=True)
    group_type_name = models.CharField(max_length=100, null=True, blank=True)
    group_name = models.CharField(max_length=100)
    group_division = models.CharField(
        max_length=2, choices=GROUP_CHOICES, null=True, blank=True)
    group_teacher = models.ForeignKey(
        'Teacher', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='study_groups', verbose_name='Guru Kelompok')
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
        super(StudyGroup, self).save(*args, **kwargs)

    def __str__(self):
        return self.group_name


class StudyGroupMember(models.Model):
    member_id = models.BigAutoField(primary_key=True)
    study_group = models.ForeignKey(
        StudyGroup, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='study_group_memberships')
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)

    class Meta:
        unique_together = ('study_group', 'student')

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        super(StudyGroupMember, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.name} - {self.study_group.group_name}"


class Teacher(models.Model):
    GENDER_CHOICES = [('L', 'Laki-Laki'), ('P', 'Perempuan')]

    teacher_id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(
        'User', on_delete=models.PROTECT, null=True, blank=True,
        related_name='teacher_profile', verbose_name='Pengguna')
    nip = models.CharField(max_length=30, null=True, blank=True, verbose_name='NIP')
    sex = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='Jenis Kelamin')
    birth_place = models.CharField(max_length=50, null=True, blank=True, verbose_name='Tempat Lahir')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Tanggal Lahir')
    address = models.CharField(max_length=200, null=True, blank=True, verbose_name='Alamat')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Telepon')
    email = models.CharField(max_length=100, null=True, blank=True, verbose_name='Email')
    status = models.ForeignKey(
        'TeacherStatus', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Status')
    specialization = models.CharField(max_length=100, null=True, blank=True, verbose_name='Spesialisasi')
    last_education = models.CharField(max_length=5, choices=[
        ('SD', 'SD'), ('SMP', 'SMP'), ('SMA', 'SMA/SMK'),
        ('D1', 'D1'), ('D2', 'D2'), ('D3', 'D3'), ('D4', 'D4'),
        ('S1', 'S1'), ('S2', 'S2'), ('S3', 'S3'),
    ], null=True, blank=True, verbose_name='Pendidikan Terakhir')
    last_school = models.CharField(max_length=200, null=True, blank=True, verbose_name='Nama Sekolah')
    last_school_major = models.CharField(max_length=100, null=True, blank=True, verbose_name='Jurusan')
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
        super(Teacher, self).save(*args, **kwargs)

    @property
    def name(self):
        return self.user.username if self.user else '-'

    def __str__(self):
        return self.name


class HalaqohTahfidz(models.Model):
    halaqoh_id = models.BigAutoField(primary_key=True)
    teacher = models.ForeignKey(
        'Teacher', on_delete=models.PROTECT, null=True, blank=True,
        related_name='halaqoh_tahfidz_set', verbose_name='Halaqoh (Guru)')
    grade = models.ForeignKey(
        'Grade', on_delete=models.PROTECT, null=True, blank=True,
        related_name='halaqoh_tahfidz_set', verbose_name='Kelas')
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
        super(HalaqohTahfidz, self).save(*args, **kwargs)

    def __str__(self):
        teacher_name = self.teacher.user.username if self.teacher and self.teacher.user else '-'
        grade_name = self.grade.grade_name if self.grade else '-'
        return f"{teacher_name} - {grade_name}"


class HalaqohTahfidzMember(models.Model):
    member_id = models.BigAutoField(primary_key=True)
    halaqoh = models.ForeignKey(
        HalaqohTahfidz, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(
        'Student', on_delete=models.CASCADE, related_name='halaqoh_tahfidz_memberships')
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)

    class Meta:
        unique_together = ('halaqoh', 'student')

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        super(HalaqohTahfidzMember, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.name} - {self.halaqoh}"


class HalaqohLughoh(models.Model):
    halaqoh_id = models.BigAutoField(primary_key=True)
    teacher = models.ForeignKey(
        'Teacher', on_delete=models.PROTECT, null=True, blank=True,
        related_name='halaqoh_lughoh_set', verbose_name='Halaqoh (Guru)')
    grade = models.ForeignKey(
        'Grade', on_delete=models.PROTECT, null=True, blank=True,
        related_name='halaqoh_lughoh_set', verbose_name='Kelas')
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
        super(HalaqohLughoh, self).save(*args, **kwargs)

    def __str__(self):
        teacher_name = self.teacher.user.username if self.teacher and self.teacher.user else '-'
        grade_name = self.grade.grade_name if self.grade else '-'
        return f"{teacher_name} - {grade_name}"


class HalaqohLughohMember(models.Model):
    member_id = models.BigAutoField(primary_key=True)
    halaqoh = models.ForeignKey(
        HalaqohLughoh, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(
        'Student', on_delete=models.CASCADE, related_name='halaqoh_lughoh_memberships')
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)

    class Meta:
        unique_together = ('halaqoh', 'student')

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        super(HalaqohLughohMember, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.name} - {self.halaqoh}"


class Extracurricular(models.Model):
    extracurricular_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name='Nama Ekstrakurikuler')
    teacher = models.ForeignKey(
        'Teacher', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='extracurriculars', verbose_name='Penanggung Jawab')
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
        super(Extracurricular, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class ExtracurricularMember(models.Model):
    member_id = models.BigAutoField(primary_key=True)
    extracurricular = models.ForeignKey(
        Extracurricular, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(
        'Student', on_delete=models.CASCADE, related_name='extracurricular_memberships')
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)

    class Meta:
        unique_together = ('extracurricular', 'student')

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        super(ExtracurricularMember, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.name} - {self.extracurricular.name}"


class SubjectGroup(models.Model):
    group_id = models.BigAutoField(primary_key=True)
    group_code = models.CharField(max_length=6, unique=True)
    group_name = models.CharField(max_length=50)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.group_code = self.group_code.strip().upper()
        self.group_name = self.group_name.strip()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(SubjectGroup, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.group_code} - {self.group_name}"


class Subject(models.Model):
    subject_id = models.BigAutoField(primary_key=True)
    subject_name = models.CharField(max_length=100, unique=True)
    group = models.ForeignKey(
        'SubjectGroup', on_delete=models.PROTECT)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.subject_name = self.subject_name.strip()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Subject, self).save(*args, **kwargs)

    def __str__(self):
        return self.subject_name


class TeacherSubject(models.Model):
    teacher_subject_id = models.BigAutoField(primary_key=True)
    grade_subject = models.ForeignKey(
        'GradeSubject', on_delete=models.CASCADE, related_name='teacher_subjects')
    teacher = models.ForeignKey(
        'Teacher', on_delete=models.PROTECT)
    hours = models.PositiveIntegerField(verbose_name='Jam')
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ('grade_subject', 'teacher')

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(TeacherSubject, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.teacher} - {self.grade_subject.subject} ({self.grade_subject.grade})"


class GradeSubject(models.Model):
    grade_subject_id = models.BigAutoField(primary_key=True)
    grade = models.ForeignKey(
        'Grade', on_delete=models.PROTECT)
    subject = models.ForeignKey(
        'Subject', on_delete=models.PROTECT)
    room = models.ForeignKey(
        'Room', on_delete=models.SET_NULL, null=True, blank=True)
    keterangan = models.CharField(max_length=100, blank=True, default='')
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ('grade', 'subject')

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(GradeSubject, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject} ({self.grade})"


class Room(models.Model):
    room_id = models.BigAutoField(primary_key=True)
    room_name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=200, blank=True, default='')
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.room_name = self.room_name.strip()
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Room, self).save(*args, **kwargs)

    def __str__(self):
        return self.room_name


class Period(models.Model):
    DAY_CHOICES = [
        ('MON', 'Senin'),
        ('TUE', 'Selasa'),
        ('WED', 'Rabu'),
        ('THU', 'Kamis'),
        ('FRI', 'Jumat'),
        ('SAT', 'Sabtu'),
        ('SUN', 'Ahad'),
    ]

    period_id = models.BigAutoField(primary_key=True)
    timetable = models.ForeignKey(
        'Timetable', on_delete=models.CASCADE, related_name='periods')
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    order = models.PositiveIntegerField(default=0)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_break = models.BooleanField(default=False)
    break_name = models.CharField(max_length=50, blank=True, default='')
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ('timetable', 'day', 'order')
        ordering = ['day', 'order']

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Period, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_day_display()} - {self.order} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"


class Timetable(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Terbit'),
    ]

    timetable_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    school_year = models.ForeignKey(
        'SchoolYear', on_delete=models.PROTECT, null=True, blank=True)
    semester = models.CharField(max_length=1, choices=[('1', 'Ganjil'), ('2', 'Genap')], default='1')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, default='')
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
        super(Timetable, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_semester_display()})"


class Lesson(models.Model):
    lesson_id = models.BigAutoField(primary_key=True)
    timetable = models.ForeignKey(
        'Timetable', on_delete=models.CASCADE, related_name='lessons')
    grade_subject = models.ForeignKey(
        'GradeSubject', on_delete=models.PROTECT)
    teacher = models.ForeignKey(
        'Teacher', on_delete=models.PROTECT)
    hours_per_week = models.PositiveIntegerField(default=1)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ('timetable', 'grade_subject', 'teacher')

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(Lesson, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.grade_subject} - {self.teacher}"


class TimetableSlot(models.Model):
    slot_id = models.BigAutoField(primary_key=True)
    timetable = models.ForeignKey(
        'Timetable', on_delete=models.CASCADE, related_name='slots')
    lesson = models.ForeignKey(
        'Lesson', on_delete=models.CASCADE, related_name='slots')
    period = models.ForeignKey(
        'Period', on_delete=models.CASCADE, related_name='slots')
    room = models.ForeignKey(
        'Room', on_delete=models.PROTECT, null=True, blank=True)
    is_manual = models.BooleanField(default=False)
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ('timetable', 'period', 'lesson')

    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = get_current_user().user_id
        self.update_date = timezone.now()
        self.update_by = get_current_user().user_id
        super(TimetableSlot, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.lesson} @ {self.period}"


class TeacherAvailability(models.Model):
    availability_id = models.BigAutoField(primary_key=True)
    teacher = models.ForeignKey(
        'Teacher', on_delete=models.CASCADE, related_name='availabilities')
    timetable = models.ForeignKey(
        'Timetable', on_delete=models.CASCADE, related_name='teacher_availabilities')
    day = models.CharField(max_length=3, choices=Period.DAY_CHOICES)
    period = models.ForeignKey(
        'Period', on_delete=models.CASCADE, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    reason = models.CharField(max_length=200, blank=True, default='')
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Teacher Availabilities'

    def save(self, *args, **kwargs):
        user = get_current_user()
        user_id = user.user_id if user else None
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = user_id
        self.update_date = timezone.now()
        self.update_by = user_id
        super(TeacherAvailability, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.teacher} - {self.get_day_display()} ({'Tersedia' if self.is_available else 'Tidak Tersedia'})"


class RoomAvailability(models.Model):
    availability_id = models.BigAutoField(primary_key=True)
    room = models.ForeignKey(
        'Room', on_delete=models.CASCADE, related_name='availabilities')
    timetable = models.ForeignKey(
        'Timetable', on_delete=models.CASCADE, related_name='room_availabilities')
    day = models.CharField(max_length=3, choices=Period.DAY_CHOICES)
    period = models.ForeignKey(
        'Period', on_delete=models.CASCADE, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    reason = models.CharField(max_length=200, blank=True, default='')
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Room Availabilities'

    def save(self, *args, **kwargs):
        user = get_current_user()
        user_id = user.user_id if user else None
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = user_id
        self.update_date = timezone.now()
        self.update_by = user_id
        super(RoomAvailability, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.room} - {self.get_day_display()} ({'Tersedia' if self.is_available else 'Tidak Tersedia'})"


class GradeAvailability(models.Model):
    availability_id = models.BigAutoField(primary_key=True)
    grade = models.ForeignKey(
        'Grade', on_delete=models.CASCADE, related_name='availabilities')
    timetable = models.ForeignKey(
        'Timetable', on_delete=models.CASCADE, related_name='grade_availabilities')
    day = models.CharField(max_length=3, choices=Period.DAY_CHOICES)
    period = models.ForeignKey(
        'Period', on_delete=models.CASCADE, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    reason = models.CharField(max_length=200, blank=True, default='')
    entry_date = models.DateTimeField(null=True)
    entry_by = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Grade Availabilities'

    def save(self, *args, **kwargs):
        user = get_current_user()
        user_id = user.user_id if user else None
        if not self.entry_date:
            self.entry_date = timezone.now()
            self.entry_by = user_id
        self.update_date = timezone.now()
        self.update_by = user_id
        super(GradeAvailability, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.grade} - {self.get_day_display()} ({'Tersedia' if self.is_available else 'Tidak Tersedia'})"


class SubstituteAssignment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Menunggu'),
        ('confirmed', 'Dikonfirmasi'),
        ('cancelled', 'Dibatalkan'),
    ]

    assignment_id = models.BigAutoField(primary_key=True)
    timetable = models.ForeignKey(
        'Timetable', on_delete=models.CASCADE, related_name='substitute_assignments')
    original_slot = models.ForeignKey(
        'TimetableSlot', on_delete=models.CASCADE, related_name='substitutes')
    substitute_teacher = models.ForeignKey(
        'Teacher', on_delete=models.PROTECT, related_name='substitute_assignments')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    match_score = models.FloatField(default=0)
    reason = models.CharField(max_length=200, blank=True, default='')
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
        super(SubstituteAssignment, self).save(*args, **kwargs)

    def __str__(self):
        return f"Substitute: {self.original_slot} -> {self.substitute_teacher}"
