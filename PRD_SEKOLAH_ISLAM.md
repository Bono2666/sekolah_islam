# Product Requirements Document (PRD)

## Sistem Manajemen Sekolah Islam (Sekolah Islam)

---

| Field | Value |
|-------|-------|
| **Nama Produk** | Sekolah Islam — Sistem Informasi Manajemen Pesantren |
| **Versi** | 1.0 |
| **URL Produksi** | `https://sekolah.ksisolusi.com/` |
| **Pengembang** | KSISolusi |
| **Tanggal Dibuat** | 27 Agustus 2026 |
| **Status** | Aktif (In Development) |

---

## Daftar Isi

1. [Executive Summary](#1-executive-summary)
2. [Goals & Objectives](#2-goals--objectives)
3. [User Roles & Personas](#3-user-roles--personas)
4. [Tech Stack](#4-tech-stack)
5. [Feature Specification](#5-feature-specification)
   - 5.1 [Autentikasi & Autorisasi](#51-autentikasi--autorisasi)
   - 5.2 [Dashboard](#52-dashboard)
   - 5.3 [Master Data](#53-master-data)
   - 5.4 [Manajemen Santri](#54-manajemen-santri)
   - 5.5 [Manajemen Guru](#55-manajemen-guru)
   - 5.6 [Kurikulum](#56-kurikulum)
   - 5.7 [Keasramaan](#57-keasramaan)
   - 5.8 [Import Data](#58-import-data)
   - 5.9 [Export & Cetak](#59-export--cetak)
   - 5.10 [Penilaian](#510-penilaian)
   - 5.11 [Keuangan](#511-keuangan)
   - 5.12 [Jadwal Pelajaran](#512-jadwal-pelajaran)
6. [Database Schema](#6-database-schema)
7. [URL Structure](#7-url-structure)
8. [Navigation Map](#8-navigation-map)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Backlog & Fitur Belum Diimplementasi](#10-backlog--fitur-belum-diimplementasi)
11. [Risks & Technical Debt](#11-risks--technical-debt)
12. [Glossary](#12-glossary)

---

## 1. Executive Summary

**Sekolah Islam** adalah sistem informasi manajemen terpusat yang dirancang khusus untuk pesantren/pondok pesantren. Sistem ini mengelola data santri (siswa), guru, kelas, asrama, kurikulum tahfidz & lughoh, ekstrakurikuler, serta data master pendukung lainnya.

Sistem ini dibangun menggunakan Django 5.0.6 dengan database MySQL, menggunakan arsitektur server-rendered (traditional MVC) dengan jQuery AJAX untuk interaksi dinamis. UI menggunakan template Soft UI Dashboard (Argon Dashboard) berbasis Bootstrap 5.

Saat ini sistem sudah berjalan di produksi dan digunakan untuk mengelola data pesantren secara digital.

---

## 2. Goals & Objectives

| Goal | Objective | Success Metric |
|------|-----------|----------------|
| **Sentralisasi Data** | Satu platform untuk mengelola seluruh data santri, guru, kelas, asrama | Semua data tersentralisasi di satu database |
| **Efisiensi Administrasi** | Mengurangi penggunaan spreadsheet/kertas | Waktu input data berkurang 50% |
| **Pelacakan Akademik** | Memantau progress halaqoh tahfidz, lughoh, dan ekskul per santri | Setiap santri memiliki jejak digital kegiatan |
| **Keamanan Data** | RBAC per menu dengan audit trail | Setiap perubahan data tercatat (entry_by, update_by) |
| **Kemudahan Input** | Import data geografis bulk dari file Excel/CSV | Data geografis bisa diimport dalam hitungan menit |
| **Akuntabilitas** | Setiap perubatan data tercatat siapa yang mengubah dan kapan | Audit trail lengkap di setiap model |

---

## 3. User Roles & Personas

### 3.1 Role Definitions

| Role | Keterangan | Akses |
|------|------------|-------|
| **Superuser** | Admin sistem dengan akses penuh | Semua menu & CRUD tanpa batasan |
| **Admin** | Pengguna dengan akses ditentukan per menu | Hak akses tambah/ubah/hapus ditentukan via tabel `Auth` |
| **User Biasa** | Pengguna dengan akses terbatas | Hanya melihat data, tidak bisa mengubah |

### 3.2 Personas

| Persona | Deskripsi | Kebutuhan Utama |
|---------|-----------|-----------------|
| **Kepala Pesantren** | Pengambil keputusan, butuh laporan | Melihat ringkasan data, cetak laporan |
| **Sekretaris/Operator** | Input dan mengelola data harian | CRUD santri, guru, import data geografis |
| **Guru/Pengajar** | Mengelola data kelas dan halaqoh | Melihat daftar santri, mengelola halaqoh |
| **Musrif (Pengawas Asrama)** | Mengelola data asrama | Melihat santri per asrama, mengelola kegiatan |
| **Bendahara** | Mengelola keuangan | (Fitur belum diimplementasi) |

### 3.3 Permission System

Sistem menggunakan **Menu-Level RBAC** dengan tabel `Auth`:

```
Auth = User + Menu + (add + edit + delete)
```

- Setiap user memiliki hak akses per menu
- Superuser bypass semua pengecekan permission
- Decorator `@role_required` digunakan di setiap view
- Sidebar menyesuaikan menu yang bisa diakses user

---

## 4. Tech Stack

### 4.1 Backend

| Komponen | Teknologi | Versi |
|----------|-----------|-------|
| Framework | Django | 5.0.6 |
| Bahasa | Python | 3.11 |
| Database | MySQL | - |
| DB Adapter | pymysql | - |
| ORM | Django ORM | - |

### 4.2 Frontend

| Komponen | Teknologi | Keterangan |
|----------|-----------|------------|
| UI Framework | Soft UI Dashboard (Argon) | Bootstrap 5-based admin template |
| CSS | Custom Soft UI + Font Awesome 5 | Icon library |
| JavaScript | jQuery 3.x (slim) | DOM manipulation |
| jQuery UI | 1.12.1 | Autocomplete widgets |
| DataTables | 1.13.5 (Bootstrap 5) | Server-side paginated tables |
| Rich Text Editor | TinyMCE | HTML content editor |
| Form Controls | Select2 | Enhanced select boxes |
| Typography | Google Fonts (Open Sans) | - |

### 4.3 Django Packages

| Package | Purpose |
|---------|---------|
| `pymysql` | MySQL database adapter |
| `dj-database-url` | Database URL parsing for production |
| `django-crum` | Get current request user for audit trails |
| `django-phonenumber-field` + `phonenumbers` | Phone number validation |
| `django-import-export` | Data import/export (Tablib) |
| `django-auto-logout` | Auto-logout after 15 minutes of inactivity |
| `django-mathfilters` | Template math filters |
| `django-tinymce` | Rich text editor integration |
| `django-user-agents` | Device/browser detection (mobile sidebar) |
| `pillow` | Image handling (user signatures) |
| `reportlab` + `pypdf2` + `xhtml2pdf` | PDF generation |
| `xlwt` + `xlsxwriter` | Excel export |
| `requests` | HTTP client |

### 4.4 Konfigurasi

| Aspek | Value |
|-------|-------|
| Bahasa UI | Bahasa Indonesia (`id`) |
| Timezone | Asia/Jakarta (WIB) |
| USE_TZ | `False` (naive datetimes) |
| Auto-Logout | 15 menit idle |
| Email Backend | SMTP via `mail.ksisolusi.com:465` (SSL) |
| CSRF Protection | Enabled |

---

## 5. Feature Specification

### 5.1 Autentikasi & Autorisasi

#### 5.1.1 Login

| Aspek | Detail |
|-------|--------|
| URL | `/login/` |
| Template | `accounts/login.html` |
| Layout | `layouts/base-fullscreen.html` |
| Fields | User ID (primary key), Password |
| User Model | `User(AbstractUser)` dengan `user_id` sebagai `USERNAME_FIELD` |

**Alur Login:**
1. User mengakses halaman login
2. User memasukkan User ID dan Password
3. Sistem memvalidasi kredensial
4. Jika valid, redirect ke dashboard (`/`)
5. Jika tidak valid, tampilkan pesan error

#### 5.1.2 Logout

| Aspek | Detail |
|-------|--------|
| URL | `/logout/` |
| View | `LogoutView` (Django built-in) |
| Behavior | Hapus session, redirect ke login |

#### 5.1.3 Auto-Logout

| Aspek | Detail |
|-------|--------|
| Package | `django-auto-logout` |
| Timeout | 15 menit |
| Behavior | Redirect ke login setelah idle |

#### 5.1.4 Password Management

| Fitur | URL | Keterangan |
|-------|-----|------------|
| Change Password | `/master/user/change-password/` | User mengubah password sendiri |
| Set Password | `/master/user/set-password/<id>/` | Admin mengatur password untuk user lain |

#### 5.1.5 RBAC (Role-Based Access Control)

**Tabel `Auth`:**
```
user (FK → User) + menu (FK → Menu) + add (bool) + edit (bool) + delete (bool)
Unique constraint: (user, menu)
```

**Decorator:** `@role_required(allowed_roles='MENU_ID')`

**Superuser:** Bypass semua pengecekan permission

---

### 5.2 Dashboard

| Aspek | Detail |
|-------|--------|
| URL | `/` |
| Template | `home/index.html` |
| Segment | `index` |

Dashboard menampilkan ringkasan data utama pesantren (konten spesifik dapat dikustomisasi).

---

### 5.3 Master Data

Semua master data mengikuti pola CRUD standar:

```
/master/<entity>/              → Index (daftar)
/master/<entity>/add/          → Tambah
/master/<entity>/<id>/         → Detail (View)
/master/<entity>/<id>/update/  → Edit
/master/<entity>/<id>/delete/  → Hapus
```

Beberapa modul memiliki endpoint tambahan:
```
/master/<entity>/data/         → DataTables JSON (server-side pagination)
/master/<entity>/import/       → Import wizard
```

#### 5.3.1 Pengguna (User)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/user/` |
| Menu ID | `USER` |
| Model | `User(AbstractUser)` |
| PK | `user_id` (CharField, max 50) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `user_id` | CharField(50), PK | ID pengguna (primary key) |
| `username` | CharField(50) | Nama pengguna |
| `email` | EmailField | Email |
| `position` | FK → Position | Posisi/jabatan |
| `signature` | ImageField | Tanda tangan digital |
| `is_active` | BooleanField | Status aktif |
| `password` | - | Password (hashed) |

**Fitur Tambahan:**
- Hapus tanda tangan (`remove-signature`)
- Autentikasi per menu (assignment menu ke user)

#### 5.3.2 Posisi (Position)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/position/` |
| Menu ID | `POSITION` |
| Model | `Position` |
| PK | `position_id` (CharField, max 3) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `position_id` | CharField(3), PK | Kode posisi (uppercase) |
| `position_name` | CharField(50) | Nama posisi |

#### 5.3.3 Menu

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/menu/` |
| Menu ID | `MENU` |
| Model | `Menu` |
| PK | `menu_id` (CharField, max 50) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `menu_id` | CharField(50), PK | ID menu (uppercase) |
| `menu_name` | CharField(50) | Nama menu |
| `menu_remark` | CharField(200) | Keterangan menu |

#### 5.3.4 Periode Closing (Closing Period)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/closing-period/` |
| Menu ID | `CLOSING-PERIOD` |
| Model | `Closing` |
| PK | `document` (CharField, max 50) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `document` | CharField(50), PK | Nama dokumen (uppercase, underscore) |
| `year_closed` | CharField(4) | Tahun ditutup |
| `month_closed` | CharField(2) | Bulan ditutup |
| `year_open` | CharField(4) | Tahun dibuka |
| `month_open` | CharField(2) | Bulan dibuka |

#### 5.3.5 Bagian (Division)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/division/` |
| Menu ID | `DIVISION` |
| Model | `Division` |
| PK | `division_id` (BigAutoField) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `division_id` | BigAutoField, PK | ID otomatis |
| `division_name` | CharField(50) | Nama bagian |

#### 5.3.6 Tingkatan (Level)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/level/` |
| Menu ID | `LEVEL` |
| Model | `Level` |
| PK | `level_id` (CharField, max 3) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `level_id` | CharField(3), PK | Kode tingkatan (uppercase) |
| `level_name` | CharField(50) | Nama tingkatan |

#### 5.3.7 Kelas (Grade)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/grade/` |
| Menu ID | `GRADE` |
| Model | `Grade` |
| PK | `grade_id` (CharField, max 7) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `grade_id` | CharField(7), PK | ID kelas (uppercase) |
| `grade` | CharField(2) | Kode kelas |
| `sub_grade` | CharField(50) | Sub-kelas |
| `grade_name` | CharField(50) | Nama kelas |
| `level` | FK → Level | Tingkatan |
| `school_year` | FK → SchoolYear | Tahun ajaran |
| `semester` | CharField(1) | Semester (1 atau 2) |
| `homeroom_teacher_1` | FK → Teacher | Wali Kelas 1 |
| `homeroom_teacher_2` | FK → Teacher | Wali Kelas 2 |
| `class_leader` | FK → Student | Ketua Kelas |
| `vice_class_leader` | FK → Student | Wakil Ketua Kelas |
| `secretary` | FK → Student | Sekretaris |
| `treasurer` | FK → Student | Bendahara |

#### 5.3.8 Tahun Ajaran (School Year)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/school-year/` |
| Menu ID | `TAHUN-AJARAN` |
| Model | `SchoolYear` |
| PK | `school_year_id` (BigAutoField) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `school_year_id` | BigAutoField, PK | ID otomatis |
| `school_year_name` | CharField(9), Unique | Nama tahun ajaran (e.g., "2025/2026") |

#### 5.3.9 Agama (Religion)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/religion/` |
| Menu ID | `AGAMA` |
| Model | `Religion` |
| PK | `religion_id` (BigAutoField) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `religion_id` | BigAutoField, PK | ID otomatis |
| `religion_name` | CharField(50), Unique | Nama agama |

#### 5.3.10 Kabupaten/Kota (District)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/district/` |
| Menu ID | `KABUPATEN-KOTA` |
| Model | `District` |
| PK | `district_id` (BigAutoField) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `district_id` | BigAutoField, PK | ID otomatis |
| `district_name` | CharField(100), Unique | Nama kabupaten/kota |

**Endpoints Tambahan:**
| URL | Fungsi |
|-----|--------|
| `/master/district/data/` | Server-side DataTables |
| `/master/district/import/` | Import dari Excel/CSV |

#### 5.3.11 Kecamatan (Sub-District)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/sub-district/` |
| Menu ID | `KECAMATAN` |
| Model | `SubDistrict` |
| PK | `sub_district_id` (BigAutoField) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `sub_district_id` | BigAutoField, PK | ID otomatis |
| `sub_district_name` | CharField(100), Unique | Nama kecamatan |

**Endpoints Tambahan:**
| URL | Fungsi |
|-----|--------|
| `/master/sub-district/data/` | Server-side DataTables |
| `/master/sub-district/import/` | Import dari Excel/CSV |

#### 5.3.12 Desa/Kelurahan (Village)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/village/` |
| Menu ID | `DESA-KELURAHAN` |
| Model | `Village` |
| PK | `village_id` (BigAutoField) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `village_id` | BigAutoField, PK | ID otomatis |
| `village_name` | CharField(100), Unique | Nama desa/kelurahan |

**Endpoints Tambahan:**
| URL | Fungsi |
|-----|--------|
| `/master/village/data/` | Server-side DataTables |
| `/master/village/import/` | Import dari Excel/CSV |

#### 5.3.13 Jenis Tinggal (Residence Type)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/residence-type/` |
| Menu ID | `JENIS-TINGGAL` |
| Model | `ResidenceType` |
| PK | `residence_type_id` (BigAutoField) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `residence_type_id` | BigAutoField, PK | ID otomatis |
| `residence_type_name` | CharField(50), Unique | Nama jenis tinggal |

#### 5.3.14 Asrama (Hostel)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/master/hostel/` |
| Menu ID | `ASRAMA` |
| Model | `Hostel` |
| PK | `hostel_id` (BigAutoField) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `hostel_id` | BigAutoField, PK | ID otomatis |
| `hostel_name` | CharField(50), Unique | Nama asrama |
| `musrif` | FK → User | Musrif (pengawas asrama) |

**Constraint:** `musrif` hanya bisa dipilih dari user dengan posisi yang mengandung "musrif".

---

### 5.4 Manajemen Santri

#### 5.4.1 Data Santri (Student)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/santri/` |
| Menu ID | `DATA-SANTRI` |
| Model | `Student` |
| PK | `student_id` (BigAutoField) |

**Fields Data Diri:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `student_id` | BigAutoField, PK | ID otomatis |
| `name` | CharField(100) | Nama lengkap |
| `grade` | FK → Grade | Kelas |
| `hostel` | FK → Hostel | Asrama |
| `sex` | CharField(1) | Jenis kelamin (L/P) |
| `birth_place` | CharField(50) | Tempat lahir |
| `birth_date` | DateField | Tanggal lahir |
| `address` | CharField(200) | Alamat |
| `village` | FK → Village | Desa/Kelurahan |
| `sub_district` | FK → SubDistrict | Kecamatan |
| `district` | FK → District | Kabupaten/Kota |
| `rt` | CharField(3) | RT |
| `rw` | CharField(3) | RW |
| `postal_code` | CharField(10) | Kode pos |
| `residence_type` | FK → ResidenceType | Jenis tempat tinggal |
| `phone` | CharField(15) | Telepon |
| `email` | CharField(50) | Email |
| `religion` | FK → Religion | Agama |
| `transportation` | CharField(50) | Alat transportasi |
| `handphone` | CharField(15) | Handphone |

**Fields Identitas:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `shkun_no` | CharField(50) | Nomor SHKUN |
| `kps_recipient` | CharField(50) | Penerima KPS |
| `kps_no` | CharField(50) | Nomor KPS |
| `nipd` | CharField(50) | NIPD |
| `nisn` | CharField(50) | NISN |
| `nik` | CharField(50) | NIK |

**Fields Orang Tua:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `father_name` | CharField(100) | Nama Ayah |
| `father_birth_year` | CharField(4) | Tahun Lahir Ayah |
| `father_education` | CharField(50) | Pendidikan Ayah |
| `father_occupation` | CharField(50) | Pekerjaan Ayah |
| `father_nik` | CharField(50) | NIK Ayah |
| `father_income` | DecimalField(15,2) | Penghasilan Ayah |
| `mother_name` | CharField(100) | Nama Ibu |
| `mother_birth_year` | CharField(4) | Tahun Lahir Ibu |
| `mother_education` | CharField(50) | Pendidikan Ibu |
| `mother_occupation` | CharField(50) | Pekerjaan Ibu |
| `mother_nik` | CharField(50) | NIK Ibu |
| `mother_income` | DecimalField(15,2) | Penghasilan Ibu |

**Fields Wali:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `guardian_name` | CharField(100) | Nama Wali |
| `guardian_birth_year` | CharField(4) | Tahun Lahir Wali |
| `guardian_education` | CharField(50) | Pendidikan Wali |
| `guardian_occupation` | CharField(50) | Pekerjaan Wali |
| `guardian_nik` | CharField(50) | NIK Wali |
| `guardian_income` | DecimalField(15,2) | Penghasilan Wali |

**Field Lainnya:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `other_info` | CharField(200) | Informasi lain |

#### 5.4.2 Santri per Kelas

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/santri/per-kelas/` |
| Menu ID | `KELAS-SANTRI` |

**Endpoints:**
| URL | Fungsi |
|-----|--------|
| `/santri/per-kelas/` | Daftar semua kelas |
| `/santri/per-kelas/<grade_id>/` | Detail kelas (daftar santri) |
| `/santri/per-kelas/<grade_id>/update/` | Update detail kelas |
| `/santri/per-kelas/<grade_id>/add-student/` | Tambah santri ke kelas |
| `/santri/per-kelas/<grade_id>/remove/<student_id>/` | Hapus santri dari kelas |

#### 5.4.3 Santri per Asrama

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/santri/per-asrama/` |
| Menu ID | `ASRAMA-SANTRI` |

**Endpoints:**
| URL | Fungsi |
|-----|--------|
| `/santri/per-asrama/` | Daftar semua asrama |
| `/santri/per-asrama/<hostel_id>/` | Detail asrama (daftar santri) |
| `/santri/per-asrama/<hostel_id>/add-student/` | Tambah santri ke asrama |
| `/santri/per-asrama/<hostel_id>/remove/<student_id>/` | Hapus santri dari asrama |

#### 5.4.4 Santri per Halaqoh Tahfidz

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/santri/per-halaqoh-tahfidz/` |
| Menu ID | `HALAQOH-TAHFIDZ` |

**Endpoints:**
| URL | Fungsi |
|-----|--------|
| `/santri/per-halaqoh-tahfidz/` | Daftar halaqoh tahfidz |
| `/santri/per-halaqoh-tahfidz/<id>/` | Detail (daftar santri) |
| `/santri/per-halaqoh-tahfidz/<id>/add-student/` | Tambah santri |
| `/santri/per-halaqoh-tahfidz/<id>/remove/<student_id>/` | Hapus santri |

#### 5.4.5 Santri per Halaqoh Lughoh

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/santri/per-halaqoh-lughoh/` |
| Menu ID | `HALAQOH-LUGHOH` |

**Endpoints:**
| URL | Fungsi |
|-----|--------|
| `/santri/per-halaqoh-lughoh/` | Daftar halaqoh lughoh |
| `/santri/per-halaqoh-lughoh/<id>/` | Detail (daftar santri) |
| `/santri/per-halaqoh-lughoh/<id>/add-student/` | Tambah santri |
| `/santri/per-halaqoh-lughoh/<id>/remove/<student_id>/` | Hapus santri |

#### 5.4.6 Santri per Ekskul

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/santri/per-ekskul/` |
| Menu ID | `EKSKUL-SANTRI` |

**Endpoints:**
| URL | Fungsi |
|-----|--------|
| `/santri/per-ekskul/` | Daftar ekskul |
| `/santri/per-ekskul/<id>/` | Detail (daftar santri) |
| `/santri/per-ekskul/<id>/add-student/` | Tambah santri |
| `/santri/per-ekskul/<id>/remove/<student_id>/` | Hapus santri |

#### 5.4.7 Kelompok Belajar

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/santri/kelompok-belajar/` |
| Menu ID | `KELOMPOK-BELAJAR` |
| Model | `StudyGroup` |

**Model Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `study_group_id` | BigAutoField, PK | ID otomatis |
| `school_year` | FK → SchoolYear | Tahun ajaran |
| `group_type_code` | CharField(10) | Kode tipe kelompok |
| `group_type_name` | CharField(100) | Nama tipe kelompok |
| `group_name` | CharField(100) | Nama kelompok |
| `group_division` | CharField(2) | Divisi kelompok (1-10) |
| `group_teacher` | FK → Teacher | Guru kelompok |

**Endpoints:**
| URL | Fungsi |
|-----|--------|
| `/santri/kelompok-belajar/` | Daftar kelompok belajar |
| `/santri/kelompok-belajar/add/` | Tambah kelompok |
| `/santri/kelompok-belajar/<id>/` | Detail kelompok |
| `/santri/kelompok-belajar/<id>/update/` | Update kelompok |
| `/santri/kelompok-belajar/<id>/delete/` | Hapus kelompok |
| `/santri/kelompok-belajar/<id>/add-student/` | Tambah santri ke kelompok |
| `/santri/kelompok-belajar/<id>/remove/<student_id>/` | Hapus santri dari kelompok |

---

### 5.5 Manajemen Guru

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/kurikulum/guru/` |
| Menu ID | `GURU` |
| Model | `Teacher` |
| PK | `teacher_id` (BigAutoField) |

**Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `teacher_id` | BigAutoField, PK | ID otomatis |
| `user` | OneToOneField → User | Akun pengguna |
| `nip` | CharField(30) | NIP |
| `sex` | CharField(1) | Jenis kelamin (L/P) |
| `birth_place` | CharField(50) | Tempat lahir |
| `birth_date` | DateField | Tanggal lahir |
| `address` | CharField(200) | Alamat |
| `phone` | CharField(20) | Telepon |
| `email` | CharField(100) | Email |
| `status` | CharField(3) | Status (GTY/GTT/PNS) |
| `specialization` | CharField(100) | Keahlian |
| `last_education` | CharField(5) | Pendidikan terakhir |
| `last_school` | CharField(200) | Nama sekolah terakhir |
| `last_school_major` | CharField(100) | Jurusan |

**Status Choices:**
| Code | Label |
|------|-------|
| GTY | Guru Tetap Yayasan |
| GTT | Guru Tidak Tetap |
| PNS | PNS |

**Last Education Choices:**
| Code | Label |
|------|-------|
| SD | SD |
| SMP | SMP |
| SMA | SMA/SMK |
| D1-D4 | Diploma |
| S1 | Sarjana |
| S2 | Magister |
| S3 | Doktor |

---

### 5.6 Kurikulum

#### 5.6.1 Halaqoh Tahfidz (Quran Memorization Circle)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/kurikulum/halaqoh-tahfidz/` |
| Menu ID | `HALAQOH-TAHFIDZ` |
| Model | `HalaqohTahfidz` |
| PK | `halaqoh_id` (BigAutoField) |

**Model Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `halaqoh_id` | BigAutoField, PK | ID otomatis |
| `teacher` | FK → Teacher | Guru halaqoh |
| `grade` | FK → Grade | Kelas |

**Member Model:** `HalaqohTahfidzMember`
| Field | Tipe | Keterangan |
|-------|------|------------|
| `member_id` | BigAutoField, PK | ID otomatis |
| `halaqoh` | FK → HalaqohTahfidz | Halaqoh |
| `student` | FK → Student | Santri |

**Unique Constraint:** `(halaqoh, student)`

**Endpoints:**
| URL | Fungsi |
|-----|--------|
| `/kurikulum/halaqoh-tahfidz/` | Daftar halaqoh |
| `/kurikulum/halaqoh-tahfidz/add/` | Tambah halaqoh |
| `/kurikulum/halaqoh-tahfidz/<id>/` | Detail halaqoh |
| `/kurikulum/halaqoh-tahfidz/<id>/update/` | Update halaqoh |
| `/kurikulum/halaqoh-tahfidz/<id>/delete/` | Hapus halaqoh |
| `/kurikulum/halaqoh-tahfidz/<id>/add-student/` | Tambah santri |
| `/kurikulum/halaqoh-tahfidz/<id>/remove/<student_id>/` | Hapus santri |

#### 5.6.2 Halaqoh Lughoh (Arabic Language Circle)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/kurikulum/halaqoh-lughoh/` |
| Menu ID | `HALAQOH-LUGHOH` |
| Model | `HalaqohLughoh` |
| PK | `halaqoh_id` (BigAutoField) |

**Model Fields:** Sama dengan HalaqohTahfidz (teacher + grade)

**Member Model:** `HalaqohLughohMember`
| Field | Tipe | Keterangan |
|-------|------|------------|
| `member_id` | BigAutoField, PK | ID otomatis |
| `halaqoh` | FK → HalaqohLughoh | Halaqoh |
| `student` | FK → Student | Santri |

**Unique Constraint:** `(halaqoh, student)`

#### 5.6.3 Ekstrakurikuler

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/kurikulum/ekskul/` |
| Menu ID | `EKSKUL` |
| Model | `Extracurricular` |
| PK | `extracurricular_id` (BigAutoField) |

**Model Fields:**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `extracurricular_id` | BigAutoField, PK | ID otomatis |
| `name` | CharField(100) | Nama ekskul |
| `teacher` | FK → Teacher | Penanggung jawab |

**Member Model:** `ExtracurricularMember`
| Field | Tipe | Keterangan |
|-------|------|------------|
| `member_id` | BigAutoField, PK | ID otomatis |
| `extracurricular` | FK → Extracurricular | Ekskul |
| `student` | FK → Student | Santri |

**Unique Constraint:** `(extracurricular, student)`

---

### 5.7 Keasramaan

Keasramaan mencakup:

| Sub-Modul | Menu ID | Status |
|-----------|---------|--------|
| Asrama | `ASRAMA` | ✅ Aktif |
| Halaqoh Tahfidz | `HALAQOH-TAHFIDZ` | ✅ Aktif |
| Halaqoh Lughoh | `HALAQOH-LUGHOH` | ✅ Aktif |
| Kegiatan Asrama | `KEGIATAN-ASRAMA` | ❌ Belum diimplementasi |
| Ekstrakurikuler | `EKSKUL` | ✅ Aktif |

---

### 5.8 Import Data

#### 5.8.1 Fitur Import

Sistem mendukung import data geografis dari file **Excel (.xlsx)** atau **CSV (.csv)**:

| Data yang bisa diimport | Menu ID | Model |
|------------------------|---------|-------|
| Kabupaten/Kota | `KABUPATEN-KOTA` | `District` |
| Kecamatan | `KECAMATAN` | `SubDistrict` |
| Desa/Kelurahan | `DESA-KELURAHAN` | `Village` |

#### 5.8.2 Alur Import (2-Step Wizard)

**Step 1: Upload**
1. User memilih file (.xlsx atau .csv)
2. Sistem menyimpan file ke `MEDIA_ROOT/import_temp/`
3. Sistem mem-parse file dan menampilkan header + 5 baris pertama sebagai preview
4. Sistem melakukan auto-suggestion mapping kolom berdasarkan alias

**Step 2: Mapping**
1. User memetakan kolom file ke field目标
2. Sistem menampilkan preview data
3. User mengklik "Import" untuk memproses

**Step 3: Hasil**
1. Sistem memproses setiap baris dalam transaction atomic
2. Menghitung: data baru (created), sudah ada (existing), dilewati (skipped), error
3. Menampilkan ringkasan hasil import

#### 5.8.3 Auto-Suggestion Mapping

Sistem memiliki daftar alias untuk setiap field:

**District:**
```
district_name, district, kabupaten, kabupaten kota, kabupaten/kota,
kab kota, kab/kota, kota, nama kabupaten, nama kota, ...
```

**SubDistrict:**
```
sub_district_name, sub district, subdistrict, kecamatan, nama kecamatan
```

**Village:**
```
village_name, village, desa, kelurahan, desa kelurahan,
desa/kelurahan, nama desa, nama kelurahan, ...
```

#### 5.8.4 Teknis Import

- File disimpan sementara di `MEDIA_ROOT/import_temp/` dengan nama unik (`import_<uuid>.xlsx`)
- File dihapus setelah import selesai atau sesi habis
- Data disimpan di session selama proses mapping
- Import dilakukan dalam `transaction.atomic()` (rollback jika ada error)
- Duplikat terdeteksi via `get_or_create` (sudah ada = existing, baru = created)

---

### 5.9 Export & Cetak

#### 5.9.1 Export Excel

| Package | Format |
|---------|--------|
| `xlwt` | `.xls` (legacy) |
| `xlsxwriter` | `.xlsx` (modern) |

#### 5.9.2 Cetak PDF

| Package | Keterangan |
|---------|------------|
| `reportlab` | PDF generation |
| `pypdf2` | PDF manipulation (merge) |
| `xhtml2pdf` | HTML to PDF conversion |

#### 5.9.3 Tanda Tangan Digital

- User dapat mengupload tanda tangan digital (image)
- Tanda tangan tersimpan di `media/signature/`
- Digunakan pada dokumen cetak

---

### 5.10 Penilaian

**Status: Sebagian Diimplementasi** — Nilai Per Kelas sudah aktif; Nilai Per Asrama & Nilai Per Ekskul masih backlog (§10.2).

| Sub-Modul | Menu ID | Status |
|-----------|---------|--------|
| Nilai Per Kelas | `NILAI-KELAS` | ✅ Aktif |
| Nilai Per Asrama | `NILAI-ASRAMA` | ❌ Belum diimplementasi |
| Nilai Per Ekskul | `NILAI-EKSKUL` | ❌ Belum diimplementasi |

#### 5.10.1 Nilai Per Kelas (NILAI-KELAS) — ✅ Aktif

Penilaian per **Guru × Mapel × Kelas × Semester × Tahun Ajaran** — satu baris `StudentScore` per santri untuk kombinasi tersebut.

| Aspek | Detail |
|-------|--------|
| Model utama | `StudentScore` — `score1`/`score2`/`score3` (Decimal 5,2, boleh NULL), `unique_together` (`teacher_subject`, `student`, `semester`, `school_year`), audit `entry_by`/`update_by` via django-crum |
| Model pendukung | `TeacherSubject`, `GradeSubject`, `Grade`, `Student`, `SchoolYear` |
| Template | `home/nilai_kelas_index.html`, `home/nilai_kelas_entry.html` |
| Sidebar | Group **Penilaian** → "Nilai Per Kelas" (`segment='nilai-kelas'`, `group_segment='penilaian'`) |
| RBAC | `@role_required('NILAI-KELAS')` di semua rute; `@edit_required(allowed_menu='NILAI-KELAS')` untuk simpan & hapus; tombol mengikuti `btn.add/edit/delete` (superuser selalu boleh) |

**Alur proses (As-Built):**

1. **List** (`/nilai/kelas/`) — tabel Kelas, Sub Kelas, Guru, Mapel, Semester, Tahun; hanya kombinasi yang sudah punya nilai (di-dedup per `teacher_subject + semester + school_year`), DataTables client-side berbahasa Indonesia, klik baris → mode lihat. Tombol **Tambah Nilai** (gating `btn.add`).
2. **Filter entry** (`/nilai/kelas/add/`) — form GET `FormNilaiFilter`: Kelas → Sub Kelas → Guru → Mata Pelajaran → Semester → Tahun Ajaran, lalu **Search**. Pilihan Guru/Mapel dibangun dari `TeacherSubject` sub kelas terpilih; di sisi klien cascading di-refresh lewat `GET /nilai/kelas/ajax/options/?grade_id=`.
3. **Grid nilai** — baris = seluruh santri kelas (`Student.grade`, urut NIPD), kolom NIPD, Nama, Nilai 1–3 (`<input type="number" min="0" max="100" step="0.01">`).
4. **Mode lihat vs edit** — dibuka dari list (`/nilai/kelas/view/<teacher_subject>/<semester>/<year>/`) → **mode lihat** (input `disabled`; tombol Kembali · Ubah · Hapus); setelah Search di halaman Tambah → **mode edit** (tombol Batal · Simpan). **Ubah** menyalakan input (hint "Ubah nilai lalu klik Simpan"), **Batal** mengembalikan nilai ke `data-original`, **Hapus** dinonaktifkan selama mode edit.
5. **Simpan (AJAX)** — `POST /nilai/kelas/ajax/save/` body JSON `{teacher_subject, semester, school_year, scores: [{student_id, score1, score2, score3}]}` + header `X-CSRFToken`. Server memvalidasi semester ∈ {1,2}, nilai 0–100 (koma → titik), membuang student yang bukan anggota kelas, lalu **replace-all** dalam `transaction.atomic()` (hapus seluruh baris kombinasi → tulis ulang). Respons `{success: true, count: n}`; sukses → `alert` + reload halaman.
6. **Hapus** — modal konfirmasi → `/nilai/kelas/delete/<teacher_subject>/<semester>/<year>/` menghapus **seluruh** `StudentScore` kombinasi tsb → redirect ke list.
7. **Pesan filter** — "Lengkapi semua filter lalu klik Search." (filter belum lengkap); "Guru tidak terdaftar untuk mapel dan kelas tersebut. Pilih kombinasi lain." (tidak ada `TeacherSubject` yang cocok); "Filter nilai tidak valid, silakan ulangi pencarian" (400 saat simpan).

---

### 5.11 Keuangan

**Status: Belum Diimplementasi**

Menu yang direncanakan:

| Sub-Modul | Menu ID | Status |
|-----------|---------|--------|
| Tagihan | `TAGIHAN` | ❌ Belum diimplementasi |
| Closing Tagihan | `CLOSING-TAGIHAN` | ❌ Belum diimplementasi |
| Pembayaran | `PEMBAYARAN` | ❌ Belum diimplementasi |
| Master Jemputan | `MASTER-JEMPUTAN` | ❌ Belum diimplementasi |

---

### 5.12 Jadwal Pelajaran (Timetable)

**Status: Aktif** (sudah berjalan di produksi)

| Aspek | Detail |
|-------|--------|
| URL Prefix | `/kurikulum/jadwal/` |
| Menu ID | `JADWAL` |
| Models | `Room`, `Period`, `Timetable`, `Lesson`, `TimetableSlot`, `TeacherAvailability`, `RoomAvailability`, `GradeAvailability`, `TeacherSubject`, `GradeSubject`, `Subject`, `SubjectGroup`, `SubstituteAssignment` |
| Referensi detail | `PRODUCT_SPEC_SEKOLAH_ISLAM.md` §25 (US-058 s/d US-076) |

Modul ini memungkinkan admin menyusun jadwal mengajar mingguan (guru, mapel, kelas, ruangan, periode) melalui kombinasi **auto-generate** dan **drag-and-drop manual**, lalu mempublikasikannya.

**Tujuan:**
- Mengisi slot jadwal (hari × periode) untuk setiap kombinasi Kelas–Mapel–Guru secara otomatis, sejumlah jam yang ditetapkan di **Guru Per Mapel (`TeacherSubject.hours`)**.
- Menghindari konflik guru, ruangan, dan kelas pada slot yang sama.
- Menyediakan hasil berstatus **draft** yang bisa disempurnakan manual (drag-and-drop) sebelum dipublikasikan (**published**).

**Ruang Lingkup — termasuk:**
- Auto-generate jadwal reguler mingguan, di-scope per **Timetable** (kombinasi Tahun Ajaran + Semester).
- Validasi konflik guru/ruangan/kelas dan ketersediaan waktu masing-masing saat generate.
- Penjadwalan manual pelengkap via drag-and-drop dari panel "Belum Dijadwalkan" (*unscheduled pool*).

**Ruang Lingkup — tidak termasuk (modul/fitur terpisah):**
- **Guru Pengganti (`SubstituteAssignment`)** — penggantian guru pada slot tertentu untuk tanggal spesifik; fitur pasca-jadwal-final, terpisah dari proses generate.
- Penilaian, Keuangan, Kegiatan Asrama — di luar cakupan modul ini.
- Jadwal ekstrakurikuler dan jadwal ujian — belum terintegrasi ke model `Timetable`/`Period` yang sama.

#### 5.12.1 Data Master Jadwal

**Peta istilah UI (Indonesia) ↔ model Django** — penamaan Inggris di kode, label Indonesia di UI:

| Istilah UI (Indonesia) | Model Django | Keterangan |
|---|---|---|
| Guru | `Teacher` | — |
| Kelas | `Grade` | — |
| Ruangan | `Room` | `room_id`, `room_name`, `capacity` |
| Mata Pelajaran | `Subject` | `subject_name`, `group` (FK → SubjectGroup) |
| Kelompok Mapel | `SubjectGroup` | `group_id`, `group_code`, `group_name` |
| Guru Per Mapel | `TeacherSubject` | `teacher`, `grade_subject`, `hours` (jam/minggu) |
| Mapel Per Kelas | `GradeSubject` | `grade`, `subject`, `room` (ruangan default), `keterangan` |
| Jadwal (induk) | `Timetable` | `name`, `school_year`, `semester`, `status`, `notes` |
| Periode | `Period` | `timetable`, `period_name`, `start_time`, `end_time`, `order`, `day`, `is_break` |
| Slot Jadwal | `TimetableSlot` | `timetable`, `lesson`, `period`, `room`, `is_manual` |
| Pelajaran (internal) | `Lesson` | `timetable`, `grade_subject`, `teacher`, `hours_per_week` — **tanpa CRUD UI** |
| Ketersediaan Guru | `TeacherAvailability` | `timetable`, `teacher`, `period`, `day`, `is_available` |
| Ketersediaan Ruangan | `RoomAvailability` | `timetable`, `room`, `period`, `day`, `is_available` |
| Ketersediaan Kelas | `GradeAvailability` | `timetable`, `grade`, `period`, `day`, `is_available` |
| Guru Pengganti | `SubstituteAssignment` | `slot` (FK → TimetableSlot), `substitute_teacher`, `reason`, `date` |

**Catatan penting:**
- Ketersediaan (Guru/Ruangan/Kelas) **di-scope per Timetable**, bukan global — satu guru bisa punya ketersediaan berbeda di jadwal Semester Ganjil vs Genap.
- `Lesson` unik per `(timetable, grade_subject, teacher)` — **team teaching (2 guru untuk 1 mapel di 1 kelas) didukung struktural**: cukup buat 2 baris `TeacherSubject` untuk `grade_subject` yang sama.
- Hari (`day`) disimpan sebagai kode 3-huruf: `MON/TUE/WED/THU/FRI/SAT/SUN`.

**Mata Pelajaran (Subject):**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `subject_id` | BigAutoField, PK | ID otomatis |
| `subject_name` | CharField(100), Unique | Nama mata pelajaran |
| `group` | FK → SubjectGroup | Kelompok mapel (on_delete=PROTECT) |

**Kelompok Mapel (SubjectGroup):**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `group_id` | BigAutoField, PK | ID otomatis |
| `group_code` | CharField(6), Unique | Kode kelompok (uppercase) |
| `group_name` | CharField(50) | Nama kelompok |

**Ruangan (Room):**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `room_id` | BigAutoField, PK | ID otomatis |
| `room_name` | CharField(100) | Nama ruangan |
| `capacity` | PositiveIntegerField, default 0 | Kapasitas ruangan (0 = tidak divalidasi saat generate — lihat [10.6](#106-auto-generate-jadwal)) |

> **Catatan:** Field `capacity` sudah ada di `models.py` (sejak migrasi `0030_add_schedule_models`) tetapi belum terdokumentasi di `PRODUCT_SPEC_SEKOLAH_ISLAM.md` US-061 — spec perlu dilengkapi dengan field ini.

**Periode (Period):**
| Field | Tipe | Keterangan |
|-------|------|------------|
| `period_id` | BigAutoField, PK | ID otomatis |
| `timetable` | FK → Timetable | Jadwal induk |
| `period_name` | CharField(50) | Nama periode (misal: "Jam 1", "Jam 2") |
| `start_time` | TimeField | Waktu mulai |
| `end_time` | TimeField | Waktu selesai |
| `order` | IntegerField | Urutan |
| `day` | CharField(3) | Hari (MON/TUE/WED/THU/FRI/SAT/SUN) |
| `is_break` | BooleanField | Apakah ini waktu istirahat |

**Day Choices:**
| Code | Label |
|------|-------|
| MON | Senin |
| TUE | Selasa |
| WED | Rabu |
| THU | Kamis |
| FRI | Jumat |
| SAT | Sabtu |
| SUN | Ahad |

#### 5.12.2 Jadwal Induk (Timetable)

| Field | Tipe | Keterangan |
|-------|------|------------|
| `timetable_id` | BigAutoField, PK | ID otomatis |
| `name` | CharField(100) | Nama jadwal |
| `school_year` | FK → SchoolYear | Tahun ajaran |
| `semester` | CharField(1) | Semester (1=Ganjil, 2=Genap) |
| `status` | CharField(10) | Status: draft/published |
| `notes` | TextField | Catatan |
| `entry_date` | DateTimeField | Waktu dibuat |
| `entry_by` | CharField(50) | User ID pembuat |
| `update_date` | DateTimeField | Waktu diupdate |
| `update_by` | CharField(50) | User ID pengupdate |

**Semester Choices:**

| Code | Label |
|------|-------|
| 1 | Ganjil |
| 2 | Genap |

> **Catatan:** Field `school_year` dan `semester` menentukan data mana yang ditampilkan di grid. Hanya GradeSubject/TeacherSubject/Grade yang sesuai tahun ajaran dan semester jadwal yang akan muncul.

#### 5.12.3 Mata Pelajaran Per Kelas (GradeSubject)

| Field | Tipe | Keterangan |
|-------|------|------------|
| `grade_subject_id` | BigAutoField, PK | ID otomatis |
| `grade` | FK → Grade | Kelas |
| `subject` | FK → Subject | Mata pelajaran |
| `room` | FK → Room | Ruangan default |
| `keterangan` | CharField(200) | Keterangan tambahan |

#### 5.12.4 Guru Per Mapel (TeacherSubject)

| Field | Tipe | Keterangan |
|-------|------|------------|
| `teacher_subject_id` | BigAutoField, PK | ID otomatis |
| `teacher` | FK → Teacher | Guru |
| `grade_subject` | FK → GradeSubject | kombinasi kelas + mapel |
| `hours` | IntegerField | Jam mengajar per minggu |

#### 5.12.5 Slot Jadwal (TimetableSlot)

| Field | Tipe | Keterangan |
|-------|------|------------|
| `slot_id` | BigAutoField, PK | ID otomatis |
| `timetable` | FK → Timetable | Jadwal induk |
| `lesson` | FK → Lesson | Pelajaran |
| `period` | FK → Period | Periode |
| `room` | FK → Room | Ruangan |
| `is_manual` | BooleanField | Apakah dijadwalkan manual (drag-drop) |

#### 5.12.6 Pelajaran (Lesson)

> **Catatan:** Model ini adalah model internal yang digunakan oleh sistem (auto-generate, drag-drop scheduling). Tidak memiliki CRUD UI terpisah.

| Field | Tipe | Keterangan |
|-------|------|------------|
| `lesson_id` | BigAutoField, PK | ID otomatis |
| `timetable` | FK → Timetable | Jadwal induk |
| `grade_subject` | FK → GradeSubject | kombinasi kelas + mapel |
| `teacher` | FK → Teacher | Guru |
| `hours_per_week` | PositiveIntegerField | Jam yang harus dijadwalkan per minggu |

**Unique Constraint:** `(timetable, grade_subject, teacher)`

**Penggunaan:**
- Auto-generate: `Lesson.objects.get_or_create()` saat generate jadwal
- Schedule lesson: `Lesson.objects.get_or_create()` saat drag-drop dari pool
- TimetableSlot: FK ke Lesson

#### 5.12.7 Ketersediaan Guru (TeacherAvailability)

| Field | Tipe | Keterangan |
|-------|------|------------|
| `availability_id` | BigAutoField, PK | ID otomatis |
| `timetable` | FK → Timetable | Jadwal induk |
| `teacher` | FK → Teacher | Guru |
| `period` | FK → Period | Periode |
| `day` | CharField(3) | Hari |
| `is_available` | BooleanField | Tersedia/tidak |

#### 5.12.8 Ketersediaan Ruangan (RoomAvailability)

| Field | Tipe | Keterangan |
|-------|------|------------|
| `room_availability_id` | BigAutoField, PK | ID otomatis |
| `timetable` | FK → Timetable | Jadwal induk |
| `room` | FK → Room | Ruangan |
| `period` | FK → Period | Periode |
| `day` | CharField(3) | Hari |
| `is_available` | BooleanField | Tersedia/tidak |

#### 5.12.8a Ketersediaan Kelas (GradeAvailability)

| Field | Tipe | Keterangan |
|-------|------|------------|
| `grade_availability_id` | BigAutoField, PK | ID otomatis |
| `timetable` | FK → Timetable | Jadwal induk |
| `grade` | FK → Grade | Kelas |
| `period` | FK → Period | Periode |
| `day` | CharField(3) | Hari |
| `is_available` | BooleanField | Tersedia/tidak |

> **Catatan:** GradeAvailability digunakan untuk menandai kapan kelas tersedia/tidak tersedia untuk dijadwalkan. Diperiksa saat auto-generate dan drag-drop scheduling.

#### 5.12.9 Guru Pengganti (SubstituteAssignment)

| Field | Tipe | Keterangan |
|-------|------|------------|
| `substitute_id` | BigAutoField, PK | ID otomatis |
| `slot` | FK → TimetableSlot | Slot jadwal |
| `substitute_teacher` | FK → Teacher | Guru pengganti |
| `reason` | CharField(200) | Alasan penggantian |
| `date` | DateField | Tanggal penggantian |

#### 5.12.10 View Modes

Sistem mendukung 6 mode tampilan jadwal:

| Mode | Deskripsi | Keterangan |
|------|-----------|------------|
| **Kelas Standar** | Tabel tunggal, kolom = periode, baris = kelas | Header periode digabung per hari (merged th) |
| **Kelas Kompak** | Satu tabel per kelas, baris = hari | Ringkas, cocok untuk banyak kelas |
| **Guru Standar** | Tabel tunggal, baris = guru | Mirip kelas standar tapi per guru |
| **Guru Kompak** | Satu tabel per guru, baris = hari | Ringkas untuk melihat jadwal per guru |
| **Ruangan Standar** | Tabel tunggal, baris = ruangan | Untuk melihat penggunaan ruangan |
| **Ruangan Kompak** | Satu tabel per ruangan, baris = hari | Ringkas untuk melihat per ruangan |

#### 5.12.11 Fitur Interaktif

**Drag-and-Drop Scheduling:**
- Guru/mapel yang belum dijadwalkan muncul di panel "Belum Dijadwalkan"
- Drag card ke cell grid untuk menjadwalkan
- Drag antar cell untuk memindahkan jadwal
- **Validasi kecocokan kelas (mode Kelas): card hanya bisa di-drop ke baris kelas yang sama. Dicek di client (cell `data-grade-id` vs card `data-grade-id`) dan di server (`target_grade_id`); jika tidak cocok ditolak dengan 400 — "Kelas target tidak sesuai dengan kelas pelajaran ini"**
- Tombol hapus pada setiap card untuk menghapus jadwal
- Update DOM secara real-time tanpa refresh halaman

**Filter & Pencarian:**
- Filter berdasarkan kelas, guru, atau ruangan
- Filter disimpan di localStorage per jadwal

**Mode & View Toggle:**
- Toggle antar 3 mode (Kelas/Guru/Ruangan) dengan icon button
- Toggle antar Standar/Kompak view
- State tersimpan di localStorage

**Freeze Column:**
- Kolom pertama (label kelas/guru/ruangan) freeze saat scroll horizontal
- Z-index hierarchy: corner cell > frozen header > period headers > body frozen

**Break/Istirahat Styling:**
- Cell istirahat memiliki background kuning pastel (#fff9c4)
- Font italic dan text "ISTIRAHAT"
- Berlaku di semua view mode dan dark mode

**Subject Colors:**
- 12 warna untuk mapel berbeda (berdasarkan hash `subject_id`)
- Warna diterapkan pada card slot
- Konsisten di semua view mode

**Panel Belum Dijadwalkan (Unscheduled Pool):**
- Menampilkan `Lesson` yang jam-nya belum (sepenuhnya) terisi, lengkap dengan sisa jam
- Pelajaran yang gagal dijadwalkan saat auto-generate otomatis muncul di panel ini
- Bisa dijadwalkan via drag-and-drop ke grid

**Analisis Beban Mengajar:**
- Card ringkasan pemanfaatan **guru** (jam terjadwal / total jam tersedia) dan **ruangan** (jam terpakai / total jam tersedia)
- Ditampilkan di atas grid pada halaman detail jadwal
- Progress bar berwarna: hijau ≥80%, kuning ≥50%, merah <50% utilisasi

**Export PDF:**
- Sesuai mode tampilan aktif saat tombol diklik (kelas/guru/ruangan × standar/kompak)
- Via `xhtml2pdf` (Pisa), ukuran **A4 landscape**

#### 5.12.12 Auto-Generation

Sistem dapat menghasilkan jadwal secara otomatis:
- Memperhitungkan ketersediaan guru, ruangan, **dan kelas**
- Menghindari konflik waktu (guru/ruangan/kelas/mapel-kelas sama di periode yang sama)
- **Mengisi jumlah jam sesuai penugasan** — total slot per `Lesson` mengikuti `hours_per_week` yang disinkronkan dari `TeacherSubject.hours`
- Menyebar jam mengajar **secara merata antar hari (round-robin, offset per-lesson)**
- **Semua mapel**: jam diusahakan sebagai **sesi 2 jam pelajaran berturut-turut per hari**; jika tidak memungkinkan, fallback **1 jam per hari** — **maksimal 2 jam per mapel per hari**
- Sesi 2 jam **tidak boleh terpotong istirahat — diusahakan untuk setiap pelajaran**: **wajib untuk Laboratorium**; untuk mapel lain pasangan melewati istirahat hanya dipakai sebagai **last resort mutlak** — yaitu **setelah** fase pasangan bebas-istirahat **dan** fase jam tunggal dicoba (relaksasi aturan hari-berurutan didahulukan); urutan pemrosesan `TeacherSubject` deterministik (`order_by('teacher_subject_id')`)
- **Tanpa jeda jam kosong**: untuk tiap **kelas dan guru per hari**, slot terisi harus berurutan — jeda hanya di awal/akhir hari atau pada **jam istirahat**
- **Tidak berulang pada hari berurutan (aturan lunak)**: sesi satu mapel (per kelas) tidak boleh jatuh pada dua hari berturut-turut (mis. Senin & Selasa); aturan ketat diutamakan dan **hanya dilonggarkan bila terpaksa** (semua kandidat hari gagal hanya karena aturan ini) agar jam tetap terjadwal penuh
- Hanya mengambil data GradeSubject/TeacherSubject yang sesuai **tahun ajaran dan semester** jadwal
- **Selalu replace**: semua slot lama dihapus sebelum generate ulang

**Algoritma (as-built) — greedy dengan rotasi round-robin antar hari** (bukan constraint-solving dengan backtracking):

```
1. Ambil GradeSubject untuk (school_year, semester) milik Timetable ini
2. Ambil TeacherSubject untuk masing-masing GradeSubject tsb
3. Hapus semua TimetableSlot lama (replace)
4. Kelompokkan Period non-break per hari (MON..SUN), urutkan per `order`

5. Untuk setiap TeacherSubject (kombinasi Guru + Mapel + Kelas) — urutan
   deterministik `order_by('teacher_subject_id')`, dengan offset hari
   yang dirotasi per-lesson (round-robin):
   a. get_or_create Lesson (timetable, grade_subject, teacher);
      sinkronkan Lesson.hours_per_week = TeacherSubject.hours
   b. FASE A — SESI 2 JAM BEBAS-ISTIRAHAT untuk SEMUA mapel (bagian
      Lab yang tidak pernah memasuki fase C): hitung pasangan direncanakan
      = hours // 2. Untuk tiap pasangan (urut round-robin antar hari,
      1 hari hanya boleh diisi 1 sesi per Lesson — cap maksimal
      2 jam/mapel/hari):
      - Pass A1 (semua mapel; satu-satunya pasangan untuk Lab): cari
        sepasang periode BERURUTAN pada hari tersebut yang TIDAK terpotong
        jam istirahat (tidak ada Period.is_break dengan order di antara
        kedua periode), hari non-berurutan, dan lolos seluruh cek.
      - Pass A2 (semua mapel): pasangan bebas-istirahat yang sama, tapi
        pada hari berurutan (relaksasi anti-hari-berurutan, jika terpaksa).
      - Cek kontiguity (tanpa jeda): union slot kelas + slot guru pada
        hari tersebut + kedua kandidat periode harus berurutan (jeda hanya
        di awal/akhir hari atau pada jam istirahat).
      - Cek hari berurutan: hari tersebut tidak boleh berdampingan
        (D-1/D+1) dengan hari yang sudah berisi sesi Lesson ini
        (berlaku Pass A1; Pass A2 = relaksasinya); cap 2 jam/hari tetap.
      - Lolos → buat kedua slot sekaligus dalam satu ruangan sama
        (prefer GradeSubject.room, fallback ruangan lain yang valid);
        hari ditandai penuh (2 jam); pasangan terpakai +1.
      - Pasangan tidak muat → lanjut pasangan berikutnya; bila satu kali
        percobaan pasangan gagal total (state tidak berubah), hentikan fase A.
   c. FASE B — JAM TUNGGAL (sisa jam termasuk jam ganjil, atau pasangan
      yang gagal) TANPA memakai pasangan melewati istirahat — maksimal
      1 jam per hari (hari yang sudah berisi untuk Lesson ini dilewati,
      sehingga cap 2 jam/mapel/hari selalu terpenuhi). Putaran round-robin
      antar hari; per hari coba periode berikutnya yang belum dicoba
      (urut `order`) selama masih ada (hari, periode) yang belum dicoba:
        * Tidak ada konflik guru / kelas / grade_subject di slot itu
        * Guru/Kelas/Ruangan tidak punya record ketersediaan
          is_available=False (prefer GradeSubject.room, fallback ruangan
          lain; jika tidak ada ruangan valid, slot tetap dibuat room kosong)
        * Kontiguity — union slot kelas + slot guru + kandidat berurutan
        * Hari berurutan — hari kandidat tidak didekati hari yang sudah
          berisi sesi Lesson ini (D-1 / D+1)
      - Lolos → buat TimetableSlot dengan is_manual=False
      - DUA FASE (aturan lunak): fase 1 berjalan ketat (cek hari
        berurutan aktif). Bila fase 1 selesai tanpa hasil dan sisa jam
        masih ada, fase 2 mengulang dengan cek hari-berurutan
        DINONAKTIFKAN (hari yang sudah berisi jam Lesson ini tetap
        ditolak demi cap 2 jam/mapel/hari) — fallback "jika terpaksa".
   d. FASE C — PASANGAN MELEWATI ISTIRAHAT (hanya non-Lab, LAST RESORT
      MUTLAK): bila setelah fase A+B masih ada sisa jam ≥2 DAN pasangan
      terpakai < pasangan direncanakan: ulangi fase pasangan dengan pasangan
      berurutan yang melewati istirahat — tier hari non-berurutan lalu hari
      berurutan — memakai seluruh cek yang sama. Untuk tiap pasangan yang
      berhasil, lanjutkan fase B (ketat lalu relaksasi) guna mengisi sisa
      jam ganjil. Lab tidak pernah memasuki fase ini.
   e. Lesson "failed" untuk sisa jamnya HANYA ketika seluruh kombinasi
      (hari, periode) sudah dicoba di KEDUA fase jam tunggal tanpa hasil
      — tetap muncul di panel "Belum Dijadwalkan"

6. Return ringkasan: {success, generated: <jumlah slot>, failed: <jumlah jam gagal>}
```

**Hard constraint (divalidasi sistem saat generate):**
1. **Konflik guru** — guru yang sama tidak ditempatkan di dua kelas pada hari & periode yang sama.
2. **Konflik kelas** — kelas yang sama tidak diisi dua mapel pada hari & periode yang sama.
3. **Konflik mapel-kelas** — `grade_subject` yang sama tidak dijadwalkan dua kali pada hari & periode yang sama.
4. **Konflik ruangan** — implisit lewat pengecekan `RoomAvailability` + slot yang sudah terisi.
5. **Ketersediaan guru** — sesuai `TeacherAvailability` untuk timetable tsb (blacklist).
6. **Ketersediaan ruangan** — sesuai `RoomAvailability` (blacklist).
7. **Ketersediaan kelas** — sesuai `GradeAvailability` (blacklist).
8. **Jam sesuai penugasan** — total slot satu `Lesson` mengikuti `hours_per_week` dari `TeacherSubject.hours`.
9. **Scoping tahun ajaran & semester** — hanya `GradeSubject`/`TeacherSubject`/`Grade` yang sesuai `school_year` + `semester` milik `Timetable`.
10. **Sesi 2 jam & maksimal 2 jam/hari** — jam dipecah jadi sesi 2 jam berturut-turut pada hari yang sama; sisa jam ganjil jadi 1 jam pada hari lain; fallback 1 jam/hari bila sesi 2 jam tidak memungkinkan.
11. **Tidak terpotong istirahat — diusahakan tiap pelajaran** — urutan isi per lesson: (A) pasangan bebas-istirahat → (B) jam tunggal → (C) pasangan melewati istirahat (non-lab, last resort mutlak); wajib untuk Laboratorium.
12. **Tanpa jeda jam kosong** — slot terisi per kelas & per guru per hari harus berurutan (kontiguity), divalidasi saat penempatan sesi 2 jam maupun jam tunggal.
13. **Tidak berulang pada hari berurutan (aturan lunak)** — sesi satu lesson tidak boleh jatuh pada hari berurutan; aturan ketat diutamakan, hanya dilonggarkan bila terpaksa.

**Belum divalidasi sistem saat ini** (backlog — lihat [10.6](#106-auto-generate-jadwal)):
- Kapasitas ruangan vs jumlah siswa kelas (`Room.capacity`).
- Batas maksimal jam mengajar guru per minggu (belum ada field di `Teacher`).

**Soft constraint:**
- **Distribusi jam merata per hari** — strategi round-robin: hari mulai diproses dirotasi (offset berbeda per lesson) sehingga jam mengajar tersebar antar hari, bukan menumpuk di hari pertama.
- **Pasangan jam bebas istirahat — diusahakan tiap mapel** — fase A (bebas-istirahat) → fase B (jam tunggal) → fase C (melewati istirahat, last resort mutlak); wajib untuk Laboratorium.
- **Belum ada soft-constraint scoring** di algoritma (selain round-robin & preferensi bebas-istirahat); item seperti skor prioritas constraint, penghindaran gap, dan batas jam berturut-turut ada di backlog [10.6](#106-auto-generate-jadwal).

> **Catatan semantik (blacklist):** Sistem hanya menolak slot jika ada record ketersediaan `is_available=False`. Jika ketersediaan tidak diatur, semua slot dianggap tersedia — konsisten dengan `move-slot` dan `schedule-lesson`.

**Implikasi praktis pendekatan greedy:**
- Karena tidak ada backtracking, urutan pemrosesan `TeacherSubject` memengaruhi hasil — kombinasi yang diproses lebih dulu "mengambil" slot yang mungkin dibutuhkan kombinasi lain yang lebih terbatas ketersediaannya. **Urutan dibuat deterministik** dengan `.order_by('teacher_subject_id')` agar hasil generate reproducible antar eksekusi.
- Round-robin memastikan jam tersebar merata antar hari, tapi hasil **tidak dijamin optimal** — cukup cepat (first-fit) dan bisa langsung disempurnakan manual lewat drag-and-drop.

#### 5.12.13 Endpoints

| URL | Method | Fungsi |
|-----|--------|--------|
| `/kurikulum/jadwal/` | GET | Index jadwal |
| `/kurikulum/jadwal/<id>/` | GET | Detail jadwal |
| `/kurikulum/jadwal/add/` | GET/POST | Tambah jadwal |
| `/kurikulum/jadwal/<id>/update/` | GET/POST | Edit jadwal |
| `/kurikulum/jadwal/<id>/delete/` | POST | Hapus jadwal |
| `/kurikulum/jadwal/<id>/grid/` | GET | Grid view (6 mode) |
| `/kurikulum/jadwal/<id>/export-pdf/` | GET | **Ekspor PDF (sesuai tampilan aktif)** |
| `/kurikulum/jadwal/ajax/save-periods/` | POST | Simpan periode |
| `/kurikulum/jadwal/ajax/save-availability/` | POST | Simpan ketersediaan guru |
| `/kurikulum/jadwal/ajax/save-room-availability/` | POST | Simpan ketersediaan ruangan |
| `/kurikulum/jadwal/ajax/save-grade-availability/` | POST | **Simpan ketersediaan kelas** |
| `/kurikulum/jadwal/view/<id>/generate/` | POST | Auto-generate jadwal |
| `/kurikulum/jadwal/ajax/move-slot/` | POST | Pindahkan slot (drag-drop) |
| `/kurikulum/jadwal/ajax/schedule-lesson/` | POST | Jadwalkan dari pool |
| `/kurikulum/jadwal/ajax/delete-slot/` | POST | Hapus slot |

#### 5.12.14 Dark Mode Support

Semua komponen jadwal mendukung dark mode:
- Grid background: `#344767`
- Header period: `#30475e`
- Frozen column: `#2d3e50`
- Card slot: border color disesuaikan
- Break cell: tetap kuning pastel
- Pool panel: background gelap

#### 5.12.15 Alur Proses (As-Built)

1. Admin membuat **Timetable** baru: nama, Tahun Ajaran, Semester → status awal `draft`.
2. Admin mengatur **Period** (jam pelajaran per hari, termasuk slot istirahat `is_break`).
3. Admin mengatur **Ketersediaan Guru**, **Ketersediaan Ruangan**, dan **Ketersediaan Kelas** (dua tab dalam satu modal: "Ketersediaan Ruangan" + "Ketersediaan Kelas") — masing-masing lewat grid checkbox per hari × periode.
4. Data **GradeSubject** (Mapel Per Kelas) dan **TeacherSubject** (Guru Per Mapel) sudah harus ada untuk tahun ajaran & semester yang sama dengan Timetable.
5. Admin membuka halaman **Grid View** (`/kurikulum/jadwal/<id>/grid/`) dan menekan tombol **"Generate"**.
6. Request AJAX ke `/kurikulum/jadwal/view/<id>/generate/` → sistem membuat/mengisi `Lesson` dan `TimetableSlot` sesuai algoritma di §5.12.12.
7. Grid ter-update setelah generate (halaman di-reload oleh JS); pelajaran yang gagal dijadwalkan otomatis tetap muncul di panel **"Belum Dijadwalkan"**.
8. Admin melengkapi sisa jadwal secara manual via **drag-and-drop**. Menjalankan ulang generate **selalu replace**: semua slot lama dihapus dulu, lalu jadwal baru dibuat dari nol.
9. Admin mengubah status Timetable dari `draft` ke `published` saat jadwal siap dipakai.

#### 5.12.16 Kriteria Keberhasilan

- 0% konflik guru/ruangan/kelas pada jadwal berstatus `published`.
- Panel "Belum Dijadwalkan" kosong (atau minim) setelah kombinasi generate + pelengkapan manual.
- Waktu proses generate untuk satu Timetable selesai dalam hitungan detik (algoritma first-fit ringan secara komputasi).

---

## 6. Database Schema

### 6.1 Entity Relationship Diagram (Text-Based)

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│    User      │────<│     Auth     │>────│     Menu     │
│ (user_id PK) │     │ (user+menu)  │     │ (menu_id PK) │
└──────┬──────┘     └──────────────┘     └──────────────┘
       │
       │ 1:1
       ▼
┌──────────────┐
│   Teacher    │
│(teacher_id PK)│
└──────┬───────┘
       │
       │ 1:N
       ├──────────────────────────────────┐
       │                                  │
       ▼                                  ▼
┌──────────────────┐           ┌──────────────────┐
│ HalaqohTahfidz   │           │ HalaqohLughoh    │
│ (halaqoh_id PK)  │           │ (halaqoh_id PK)  │
└────────┬─────────┘           └────────┬─────────┘
         │ 1:N                          │ 1:N
         ▼                              ▼
┌──────────────────────┐    ┌──────────────────────┐
│ HalaqohTahfidzMember │    │ HalaqohLughohMember  │
│ (member_id PK)       │    │ (member_id PK)        │
└──────────┬───────────┘    └──────────┬───────────┘
           │ N:1                       │ N:1
           └───────────┬───────────────┘
                       │
                       ▼
               ┌──────────────┐
               │   Student    │
               │(student_id PK)│
               └──────┬───────┘
                      │
                      ├──── N:1 ──→ Grade ── FK → Level
                      │              Grade ── FK → SchoolYear
                      │
                      ├──── N:1 ──→ Hostel ── FK → User (Musrif)
                      │
                      ├──── N:1 ──→ ResidenceType
                      │
                      ├──── N:1 ──→ Religion
                      │
                      ├──── N:1 ──→ District
                      │              District ── N:1 → SubDistrict
                      │              SubDistrict ── N:1 → Village
                      │
                      └──── N:M ──→ StudyGroup (via StudyGroupMember)
                                   StudyGroup ── FK → SchoolYear
                                   StudyGroup ── FK → Teacher

┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Timetable  │────<│   TimetableSlot  │>────│     Lesson       │
│(timetable_id)│     │  (slot_id PK)    │     │ (lesson_id PK)   │
└──────┬───────┘     └──────────────────┘     └──────────────────┘
       │                                         │
       │ 1:N                                     │ N:1
       ├─────────────────┐                       │
       ▼                 ▼                       │
┌──────────────┐  ┌──────────────────────┐       │
│   Period     │  │ TeacherAvailability  │       │
│(period_id PK)│  │ (availability_id PK) │       │
└──────────────┘  └──────────────────────┘       │
                                                 │
       ┌─────────────────────────────────────────┘
       │
       ▼
┌──────────────────┐     ┌──────────────────┐
│   TeacherSubject │     │   GradeSubject   │
│(teacher_subject) │     │(grade_subject_id)│
└──────────────────┘     └──────────────────┘
       │                          │
       │ N:1                      │ N:1
       ▼                          ▼
┌──────────────┐           ┌──────────────┐
│   Teacher    │           │    Grade     │
│(teacher_id)  │           │ (grade_id)   │
└──────────────┘           └──────────────┘

┌──────────────────────┐
│   Room               │
│ (room_id PK)         │
│ capacity (default 0) │
└──────────────────────┘
       │
       │ 1:N
       ▼
┌──────────────────────┐
│  RoomAvailability    │
│ (room_availability_id)│
│ timetable → Timetable│
└──────────────────────┘

┌──────────────────────┐
│  GradeAvailability   │
│(grade_availability_id)│
│ timetable → Timetable│
│ grade → Grade        │
│ period → Period      │
│ day, is_available    │
└──────────────────────┘

┌──────────────────────┐
│   TeacherStatus      │
│ (status_id PK)       │
│ status_name          │
└──────────────────────┘
       │
       │ 1:N
       ▼
┌──────────────────────┐
│   Teacher            │
│ (teacher_id PK)      │
│ status → TeacherStatus│
└──────────────────────┘

┌──────────────────────┐     ┌──────────────────────┐
│   SubjectGroup       │<────│      Subject         │
│ (group_id PK)        │     │ (subject_id PK)      │
│ group_code           │     │ subject_name (unique)│
│ group_name           │     │ group → SubjectGroup │
└──────────────────────┘     └──────────────────────┘

┌──────────────────────┐
│   StudentScore       │
│ (score_id PK)        │
│ teacher_subject →    │──┐
│   TeacherSubject     │  │ unique
│ student → Student    │  │ (teacher_subject,
│ semester (1/2)       │  │  student, semester,
│ school_year →        │──┘  school_year)
│   SchoolYear         │
│ score1/score2/score3 │
│ entry_by, update_by  │
└──────────────────────┘
```

### 6.2 Audit Trail

Setiap model memiliki field audit:

| Field | Tipe | Keterangan |
|-------|------|------------|
| `entry_date` | DateTimeField | Waktu data dibuat |
| `entry_by` | CharField(50) | User ID yang membuat |
| `update_date` | DateTimeField | Waktu data diupdate |
| `update_by` | CharField(50) | User ID yang mengupdate |

Menggunakan `django-crum` untuk otomatis mendapatkan current user.

---

## 7. URL Structure

### 7.1 Authentication Routes

| URL | View | Name |
|-----|------|------|
| `/login/` | `login_view` | `login` |
| `/logout/` | `LogoutView` | `logout` |
| `/forbidden/` | `forbidden_view` | `forbidden-view` |

### 7.2 Master Data Routes (14 modul × 5 endpoints = 70+)

**Pattern:**
```
/master/<entity>/              → Index
/master/<entity>/add/          → Add
/master/<entity>/<id>/         → View
/master/<entity>/<id>/update/  → Update
/master/<entity>/<id>/delete/  → Delete
/master/<entity>/data/         → DataTables JSON (beberapa modul)
/master/<entity>/import/       → Import (3 modul geografis)
```

**Modul:**
| Entity | Routes |
|--------|--------|
| user | 7 (CRUD + remove-signature + change-password + set-password) |
| position | 5 |
| menu | 5 |
| auth | 2 (update + delete per user-menu) |
| closing-period | 5 |
| division | 5 |
| level | 5 |
| grade | 5 |
| religion | 5 |
| district | 8 (CRUD + data + import) |
| school-year | 5 |
| sub-district | 8 (CRUD + data + import) |
| village | 8 (CRUD + data + import) |
| hostel | 5 |
| residence-type | 5 |

### 7.3 Student Routes

| URL Pattern | Fungsi |
|-------------|--------|
| `/santri/` | List santri |
| `/santri/add/` | Tambah santri |
| `/santri/view/<id>/` | Detail santri |
| `/santri/update/<id>/` | Edit santri |
| `/santri/delete/<id>/` | Hapus santri |
| `/santri/per-kelas/` | Santri per kelas |
| `/santri/per-kelas/<id>/` | Detail kelas |
| `/santri/per-kelas/<id>/update/` | Update kelas |
| `/santri/per-kelas/<id>/add-student/` | Tambah santri ke kelas |
| `/santri/per-kelas/<id>/remove/<student_id>/` | Hapus santri dari kelas |
| `/santri/per-asrama/` | Santri per asrama |
| `/santri/per-asrama/<id>/` | Detail asrama |
| `/santri/per-asrama/<id>/add-student/` | Tambah santri ke asrama |
| `/santri/per-asrama/<id>/remove/<student_id>/` | Hapus santri dari asrama |
| `/santri/per-halaqoh-tahfidz/` | Santri per halaqoh tahfidz |
| `/santri/per-halaqoh-tahfidz/<id>/` | Detail halaqoh tahfidz |
| `/santri/per-halaqoh-tahfidz/<id>/add-student/` | Tambah santri |
| `/santri/per-halaqoh-tahfidz/<id>/remove/<student_id>/` | Hapus santri |
| `/santri/per-halaqoh-lughoh/` | Santri per halaqoh lughoh |
| `/santri/per-halaqoh-lughoh/<id>/` | Detail halaqoh lughoh |
| `/santri/per-halaqoh-lughoh/<id>/add-student/` | Tambah santri |
| `/santri/per-halaqoh-lughoh/<id>/remove/<student_id>/` | Hapus santri |
| `/santri/per-ekskul/` | Santri per ekskul |
| `/santri/per-ekskul/<id>/` | Detail ekskul |
| `/santri/per-ekskul/<id>/add-student/` | Tambah santri |
| `/santri/per-ekskul/<id>/remove/<student_id>/` | Hapus santri |
| `/santri/kelompok-belajar/` | Kelompok belajar |
| `/santri/kelompok-belajar/add/` | Tambah kelompok |
| `/santri/kelompok-belajar/<id>/` | Detail kelompok |
| `/santri/kelompok-belajar/<id>/update/` | Update kelompok |
| `/santri/kelompok-belajar/<id>/delete/` | Hapus kelompok |
| `/santri/kelompok-belajar/<id>/add-student/` | Tambah santri ke kelompok |
| `/santri/kelompok-belajar/<id>/remove/<student_id>/` | Hapus santri dari kelompok |

### 7.4 Kurikulum Routes

| URL Pattern | Fungsi |
|-------------|--------|
| `/kurikulum/guru/` | List guru |
| `/kurikulum/guru/add/` | Tambah guru |
| `/kurikulum/guru/view/<id>/` | Detail guru |
| `/kurikulum/guru/update/<id>/` | Edit guru |
| `/kurikulum/guru/delete/<id>/` | Hapus guru |
| `/kurikulum/halaqoh-tahfidz/` | List halaqoh tahfidz |
| `/kurikulum/halaqoh-tahfidz/add/` | Tambah halaqoh tahfidz |
| `/kurikulum/halaqoh-tahfidz/<id>/` | Detail halaqoh tahfidz |
| `/kurikulum/halaqoh-tahfidz/<id>/update/` | Update halaqoh tahfidz |
| `/kurikulum/halaqoh-tahfidz/<id>/delete/` | Hapus halaqoh tahfidz |
| `/kurikulum/halaqoh-tahfidz/<id>/add-student/` | Tambah santri |
| `/kurikulum/halaqoh-tahfidz/<id>/remove/<student_id>/` | Hapus santri |
| `/kurikulum/halaqoh-lughoh/` | List halaqoh lughoh |
| `/kurikulum/halaqoh-lughoh/add/` | Tambah halaqoh lughoh |
| `/kurikulum/halaqoh-lughoh/<id>/` | Detail halaqoh lughoh |
| `/kurikulum/halaqoh-lughoh/<id>/update/` | Update halaqoh lughoh |
| `/kurikulum/halaqoh-lughoh/<id>/delete/` | Hapus halaqoh lughoh |
| `/kurikulum/halaqoh-lughoh/<id>/add-student/` | Tambah santri |
| `/kurikulum/halaqoh-lughoh/<id>/remove/<student_id>/` | Hapus santri |
| `/kurikulum/ekskul/` | List ekskul |
| `/kurikulum/ekskul/add/` | Tambah ekskul |
| `/kurikulum/ekskul/<id>/` | Detail ekskul |
| `/kurikulum/ekskul/<id>/update/` | Update ekskul |
| `/kurikulum/ekskul/<id>/delete/` | Hapus ekskul |
| `/kurikulum/mapel/` | List mata pelajaran |
| `/kurikulum/mapel/add/` | Tambah mata pelajaran |
| `/kurikulum/mapel/<id>/` | Detail mata pelajaran |
| `/kurikulum/mapel/<id>/update/` | Update mata pelajaran |
| `/kurikulum/mapel/<id>/delete/` | Hapus mata pelajaran |
| `/kurikulum/guru-mapel/` | List guru per mapel |
| `/kurikulum/guru-mapel/add/` | Tambah guru per mapel |
| `/kurikulum/guru-mapel/<id>/` | Detail guru per mapel |
| `/kurikulum/guru-mapel/<id>/update/` | Update guru per mapel |
| `/kurikulum/guru-mapel/<id>/delete/` | Hapus guru per mapel |
| `/kurikulum/mapel-kelas/` | List mapel per kelas |
| `/kurikulum/mapel-kelas/add/` | Tambah mapel per kelas |
| `/kurikulum/mapel-kelas/<id>/` | Detail mapel per kelas |
| `/kurikulum/mapel-kelas/<id>/update/` | Update mapel per kelas |
| `/kurikulum/mapel-kelas/<id>/delete/` | Hapus mapel per kelas |
| `/kurikulum/ruangan/` | List ruangan |
| `/kurikulum/ruangan/add/` | Tambah ruangan |
| `/kurikulum/ruangan/<id>/` | Detail ruangan |
| `/kurikulum/ruangan/<id>/update/` | Update ruangan |
| `/kurikulum/ruangan/<id>/delete/` | Hapus ruangan |
| `/kurikulum/jadwal/` | List jadwal pelajaran |
| `/kurikulum/jadwal/add/` | Tambah jadwal pelajaran |
| `/kurikulum/jadwal/<id>/` | Detail jadwal pelajaran |
| `/kurikulum/jadwal/<id>/update/` | Update jadwal pelajaran |
| `/kurikulum/jadwal/<id>/delete/` | Hapus jadwal pelajaran |
| `/kurikulum/jadwal/<id>/grid/` | Grid view jadwal (6 mode) |
| `/kurikulum/jadwal/<id>/export-pdf/` | **Ekspor PDF jadwal** |
| `/kurikulum/jadwal/ajax/save-periods/` | AJAX: Simpan periode |
| `/kurikulum/jadwal/ajax/save-availability/` | AJAX: Simpan ketersediaan guru |
| `/kurikulum/jadwal/ajax/save-room-availability/` | AJAX: Simpan ketersediaan ruangan |
| `/kurikulum/jadwal/ajax/save-grade-availability/` | AJAX: **Simpan ketersediaan kelas** |
| `/kurikulum/jadwal/view/<id>/generate/` | AJAX: Auto-generate jadwal |
| `/kurikulum/jadwal/ajax/move-slot/` | AJAX: Pindahkan slot |
| `/kurikulum/jadwal/ajax/schedule-lesson/` | AJAX: Jadwalkan dari pool |
| `/kurikulum/jadwal/ajax/delete-slot/` | AJAX: Hapus slot |

### 7.5 Penilaian Routes

| URL Pattern | Fungsi |
|-------------|--------|
| `/nilai/kelas/` | List nilai per kelas |
| `/nilai/kelas/add/` | Form filter & entry nilai |
| `/nilai/kelas/view/<teacher_subject>/<semester>/<year>/` | Detail nilai (mode lihat) |
| `/nilai/kelas/delete/<teacher_subject>/<semester>/<year>/` | Hapus nilai kombinasi |
| `/nilai/kelas/ajax/options/` | AJAX: opsi guru & mapel per sub kelas |
| `/nilai/kelas/ajax/save/` | AJAX: simpan nilai (replace-all) |

### 7.6 AJAX Endpoints

| URL | Method | Fungsi |
|-----|--------|--------|
| `/santri/ajax/sub-districts/` | GET | Get kecamatan berdasarkan kabupaten |
| `/santri/ajax/villages/` | GET | Get desa berdasarkan kecamatan |
| `/santri/ajax/district-autocomplete/` | GET | Autocomplete kabupaten |
| `/santri/ajax/sub-district-autocomplete/` | GET | Autocomplete kecamatan |
| `/santri/ajax/village-autocomplete/` | GET | Autocomplete desa |
| `/santri/ajax/district-list/` | GET | Daftar kabupaten (JSON) |
| `/santri/ajax/sub-district-list/` | GET | Daftar kecamatan (JSON) |
| `/santri/ajax/village-list/` | GET | Daftar desa (JSON) |
| `/master/district/data/` | GET | DataTables server-side kabupaten |
| `/master/sub-district/data/` | GET | DataTables server-side kecamatan |
| `/master/village/data/` | GET | DataTables server-side desa |
| `/kurikulum/jadwal/ajax/save-periods/` | POST | Simpan periode jadwal |
| `/kurikulum/jadwal/ajax/save-availability/` | POST | Simpan ketersediaan guru |
| `/kurikulum/jadwal/ajax/save-room-availability/` | POST | Simpan ketersediaan ruangan |
| `/kurikulum/jadwal/ajax/save-grade-availability/` | POST | **Simpan ketersediaan kelas** |
| `/kurikulum/jadwal/view/<id>/generate/` | POST | Auto-generate jadwal |
| `/kurikulum/jadwal/ajax/move-slot/` | POST | Pindahkan slot (drag-drop) |
| `/kurikulum/jadwal/ajax/schedule-lesson/` | POST | Jadwalkan dari pool |
| `/kurikulum/jadwal/ajax/delete-slot/` | POST | Hapus slot |
| `/nilai/kelas/ajax/options/` | GET | Opsi guru & mapel per sub kelas (JSON) |
| `/nilai/kelas/ajax/save/` | POST | Simpan nilai (JSON, replace-all) |

### 7.7 Total Routes

**Total: 250+ URL patterns**

---

## 8. Navigation Map

### 8.1 Sidebar Structure

```
📁 Santri
   ├── 📄 List Santri (DATA-SANTRI)
   ├── 📄 Per Kelas (KELAS-SANTRI)
   ├── 📄 Kelompok Belajar (KELOMPOK-BELAJAR)
   ├── 📄 Per Asrama (ASRAMA-SANTRI)
   ├── 📄 Per Halaqoh Tahfidz (HALAQOH-TAHFIDZ)
   ├── 📄 Per Halaqoh Lughoh (HALAQOH-LUGHOH)
   └── 📄 Per Ekskul (EKSKUL-SANTRI)

📁 Kurikulum
   ├── 📄 Guru (GURU)
   ├── 📄 Kelas (GRADE)
   ├── 📄 Mata Pelajaran (MAPEL) ✅
   ├── 📄 Guru Per Mapel (GURU-MAPEL) ✅
   ├── 📄 Mapel Per Kelas (MAPEL-KELAS) ✅
   └── 📄 Jadwal Pelajaran (JADWAL) ✅

📁 Keasramaan
   ├── 📄 Asrama (ASRAMA)
   ├── 📄 Halaqoh Tahfidz (HALAQOH-TAHFIDZ)
   ├── 📄 Halaqoh Lughoh (HALAQOH-LUGHOH)
   ├── 📄 Kegiatan Asrama (KEGIATAN-ASRAMA) ❌
   └── 📄 Ekstrakurikuler (EKSKUL)

📁 Penilaian
   ├── 📄 Nilai Per Kelas (NILAI-KELAS) ✅
   ├── 📄 Nilai Per Asrama (NILAI-ASRAMA) ❌
   └── 📄 Nilai Per Ekskul (NILAI-EKSKUL) ❌

📁 Keuangan
   ├── 📄 Tagihan (TAGIHAN) ❌
   ├── 📄 Closing Tagihan (CLOSING-TAGIHAN) ❌
   ├── 📄 Pembayaran (PEMBAYARAN) ❌
   └── 📄 Master Jemputan (MASTER-JEMPUTAN) ❌

📁 Data Master
   ├── 📄 Pengguna (USER)
   ├── 📄 Posisi (POSITION)
   ├── 📄 Menu (MENU)
   ├── 📄 Tingkatan (LEVEL)
   ├── 📄 Agama (AGAMA)
   ├── 📄 Kabupaten/Kota (KABUPATEN-KOTA)
   ├── 📄 Kecamatan (KECAMATAN)
   ├── 📄 Desa/Kelurahan (DESA-KELURAHAN)
   ├── 📄 Jenis Tinggal (JENIS-TINGGAL)
   └── 📄 Tahun Ajaran (TAHUN-AJARAN)
```

### 8.2 Sidebar Behavior

- Sidebar collapsible per group (disimpan di `sessionStorage`)
- Menu disabled jika user tidak memiliki akses (berdasarkan `Auth`)
- Superuser selalu bisa mengakses semua menu
- Mobile sidebar menggunakan `django-user-agents` untuk deteksi device

---

## 9. Non-Functional Requirements

### 9.1 Keamanan

| Aspek | Implementasi |
|-------|-------------|
| Autentikasi | Django Auth + Custom User Model |
| Autorisasi | RBAC per menu via tabel `Auth` |
| CSRF Protection | Enabled di semua form |
| Password Storage | Django default (PBKDF2) |
| Auto-Logout | 15 menit idle |
| Session Management | Django default session |
| SQL Injection | Django ORM (parameterized queries) |
| XSS Protection | Django template auto-escaping |

### 9.2 Performance

| Aspek | Implementasi |
|-------|-------------|
| Pagination | DataTables server-side untuk data geografis |
| Query Optimization | Raw SQL untuk some joins (User + Position) |
| Caching | Tidak ada (belum diimplementasi) |

### 9.3 Lokalisasi

| Aspek | Value |
|-------|-------|
| Bahasa UI | Bahasa Indonesia |
| Timezone | Asia/Jakarta (WIB) |
| Date Format | Sesuai locale Indonesia |
| Currency | Rupiah (untuk field income) |

### 9.4 Cetak

| Aspek | Implementasi |
|-------|-------------|
| PDF | ReportLab + xhtml2pdf |
| Excel | xlwt (.xls) + xlsxwriter (.xlsx) |
| Tanda Tangan | Digital signature (image upload) |

### 9.5 Browser Support

| Browser | Status |
|---------|--------|
| Chrome | ✅ Supported |
| Firefox | ✅ Supported |
| Edge | ✅ Supported |
| Safari | ✅ Supported |

### 9.6 Responsive Design

- Menggunakan Soft UI Dashboard (Bootstrap 5)
- Sidebar adaptif untuk mobile (via `django-user-agents`)
- DataTables responsive

---

## 10. Backlog & Fitur Belum Diimplementasi

### 10.1 Kurikulum

| Fitur | Menu ID | Prioritas | Status |
|-------|---------|-----------|--------|
| Mata Pelajaran | `MAPEL` | Tinggi | ✅ Aktif |
| Guru Per Mapel | `GURU-MAPEL` | Tinggi | ✅ Aktif |
| Mapel Per Kelas | `MAPEL-KELAS` | Tinggi | ✅ Aktif |
| Jadwal Pelajaran | `JADWAL` | Tinggi | ✅ Aktif |

### 10.2 Penilaian

| Fitur | Menu ID | Prioritas | Status | Keterangan |
|-------|---------|-----------|--------|------------|
| Nilai Per Kelas | `NILAI-KELAS` | Tinggi | ✅ Aktif | Input, ubah, hapus & lihat nilai per kelas (§5.10.1) |
| Nilai Per Asrama | `NILAI-ASRAMA` | Menengah | ❌ Belum | Nilai perkembangan di asrama |
| Nilai Per Ekskul | `NILAI-EKSKUL` | Menengah | ❌ Belum | Nilai keikutsertaan ekskul |

### 10.3 Keuangan

| Fitur | Menu ID | Prioritas | Keterangan |
|-------|---------|-----------|------------|
| Tagihan | `TAGIHAN` | Tinggi | Pembuatan tagihan SPP |
| Closing Tagihan | `CLOSING-TAGIHAN` | Menengah | Penguncian tagihan |
| Pembayaran | `PEMBAYARAN` | Tinggi | Pencatatan pembayaran |
| Master Jemputan | `MASTER-JEMPUTAN` | Rendah | Data jemputan santri |

### 10.4 Keasramaan

| Fitur | Menu ID | Prioritas | Keterangan |
|-------|---------|-----------|------------|
| Kegiatan Asrama | `KEGIATAN-ASRAMA` | Menengah | Jadwal kegiatan harian asrama |

### 10.5 Technical Improvements

| Fitur | Prioritas | Keterangan |
|-------|-----------|------------|
| REST API (DRF) | Menengah | Saat ini commented out di requirements.txt |
| Notification System | Menengah | Saat ini commented out di codebase |
| Unit Tests | Tinggi | Saat ini tests.py kosong |
| Refactor views.py | Tinggi | ~6,300 baris dalam satu file |
| Environment Variables | Tinggi | Password hardcoded di settings.py |
| Multi-Room Support | Menengah | Perluas auto-generate untuk multi-ruangan |

### 10.6 Auto-Generate Jadwal

Item berikut adalah backlog peningkatan algoritma auto-generate (§5.12.12) — bukan requirement yang sudah terpenuhi:

| Item | Status Saat Ini | Rekomendasi |
|------|-----------------|-------------|
| Validasi kapasitas ruangan vs jumlah siswa | Field `Room.capacity` ada (default 0) tapi **tidak divalidasi** saat generate | Cek `Room.capacity` vs jumlah siswa kelas saat generate (abaikan jika capacity=0) |
| Batas maksimal jam mengajar guru/minggu | Tidak ada field/limit di `Teacher`, tidak divalidasi | Tambah field `max_hours_per_week`, cek saat generate |
| Menghindari gap kosong di jadwal kelas/guru | Tidak ada | Tambah scoring soft-constraint setelah slot pertama valid |
| Prioritas/bobot constraint | Tidak ada | Perlu desain skema skor jika ingin soft-constraint dioptimalkan |
| Validasi kelengkapan data sebelum generate | Sebagian — hanya alert jika tahun ajaran/semester Timetable belum diisi | Tambah pre-check: apakah semua `Grade` sudah punya `GradeSubject` & `TeacherSubject` sebelum generate ditekan |
| Multi-draft/versioning jadwal | Tidak ada — satu Timetable = satu status draft/published | Bisa ditambah jika sekolah ingin membandingkan beberapa skenario |
| Pilihan sesi 2 jam selektif per mapel | Semua mapel diperlakukan sama (sesi 2 jam diusahakan) | Opsional: flag `prefer_double_period` di `GradeSubject` |
| Distribusi jam merata per hari | ✅ Sudah diimplementasi (round-robin, offset per-lesson) | — |
| Sesi 2 jam otomatis untuk semua mapel | ✅ Sudah diimplementasi (maks 2 jam/mapel/hari, bebas istirahat wajib untuk Lab) | — |

---

## 11. Risks & Technical Debt

### 11.1 Monolithic Architecture

**Issue:** `apps/views.py` memiliki ~6,300 baris kode dalam satu file.

**Impact:** Sulit untuk maintain, debug, dan extend.

**Recommendation:** Refactor ke per-modul views (e.g., `views/student.py`, `views/master.py`, `views/import.py`).

### 11.2 Single App Structure

**Issue:** Semua logic berada di dalam satu app `apps/`.

**Impact:** Tidak ada pemisahan yang jelas antar domain.

**Recommendation:** Pisahkan ke multiple apps (e.g., `students`, `teachers`, `curriculum`, `master_data`).

### 11.3 Hardcoded Credentials

**Issue:** Password email dan database password hardcoded di `settings.py`.

**Impact:** Security risk jika source code bocor.

**Recommendation:** Gunakan environment variables (python-decouple atau django-environ).

### 11.4 No Tests

**Issue:** `apps/tests.py` kosong.

**Impact:** Tidak ada jaminan kualitas saat ada perubahan kode.

**Recommendation:** Tulis unit tests untuk model, form, dan view critical.

### 11.5 Raw SQL Queries

**Issue:** Beberapa view menggunakan raw SQL (cursor.execute).

**Impact:** Vulnerable to SQL injection jika tidak hati-hati, tidak portable ke database lain.

**Recommendation:** Gunakan Django ORM atau `django.db.models.RawSQL`.

### 11.6 Commented-Out Features

**Issue:** DRF dan notification system sudah di-install tapi di-comment.

**Impact:** Fitur terhambat, dependencies terinstall tapi tidak terpakai.

**Recommendation:** Implementasi atau hapus dependencies yang tidak terpakai.

---

## 12. Glossary

| Istilah | Keterangan |
|---------|------------|
| **Santri** | Siswa/pelajar di pesantren |
| **Guru** | Pengajar/pendidik |
| **Asrama** | Gedung/tempat tinggal santri |
| **Musrif** | Pengawas/pembina asrama |
| **Halaqoh** | Lingkaran belajar kelompok kecil |
| **Tahfidz** | Program menghafal Al-Quran |
| **Lughoh** | Program belajar bahasa Arab |
| **Ekskul** | Ekstrakurikuler |
| **Kelompok Belajar** | Kelompok belajar akademik |
| **Kelas** | Kelompok belajar reguler |
| **Tahun Ajaran** | Periode akademik (e.g., 2025/2026) |
| **Semester** | Periode pembelajaran (1 atau 2) |
| **Wali Kelas** | Guru yang bertanggung jawab atas kelas |
| **Ketua Kelas** | Santri yang memimpin kelas |
| **SHKUN** | Nomor registrasi santri |
| **NISN** | Nomor Induk Siswa Nasional |
| **NIK** | Nomor Induk Kependudukan |
| **KPS** | Kartu Perlindungan Sosial |
| **NIPD** | Nomor Induk Peserta Didik |
| **GTY** | Guru Tetap Yayasan |
| **GTT** | Guru Tidak Tetap |
| **PNS** | Pegawai Negeri Sipil |
| **RBAC** | Role-Based Access Control |
| **CRUD** | Create, Read, Update, Delete |
| **DataTables** | jQuery plugin untuk tabel interaktif |
| **AJAX** | Asynchronous JavaScript and XML |
| **Jadwal Pelajaran** | Jadwal mengajar guru untuk kelas/ruangan tertentu |
| **Periode** | Blok waktu dalam jadwal (misal: Jam 1, Jam 2) |
| **Slot** | Satu jadwal mengajar (guru + mapel + kelas + ruangan + waktu) |
| **Auto-Generate** | Pembuatan jadwal otomatis berdasarkan ketersediaan |
| **Lesson** | Model internal (tanpa CRUD UI) yang merepresentasikan "kebutuhan jam" satu kombinasi Guru + Mapel + Kelas dalam satu Timetable |
| **First-fit** | Strategi algoritma auto-generate: ambil slot kosong valid pertama yang ditemukan, tanpa mengevaluasi alternatif lain |
| **Unscheduled Pool** | Panel "Belum Dijadwalkan": berisi `Lesson` yang jam-nya belum (sepenuhnya) terisi ke `TimetableSlot` |
| **is_manual** | Flag pada `TimetableSlot` untuk membedakan slot hasil generate otomatis vs input manual (drag-drop) |
| **Blacklist Ketersediaan** | Semantik cek ketersediaan: slot hanya ditolak jika ada record `is_available=False`; tanpa record = tersedia |
| **Team Teaching** | 2 guru mengajar 1 mapel di 1 kelas — didukung oleh 2 baris `TeacherSubject` pada `grade_subject` yang sama |
| **Round-Robin** | Rotasi offset hari per-lesson saat generate agar jam mengajar tersebar merata antar hari |
| **Frozen Column** | Kolom yang tetap terlihat saat scroll horizontal |

---

## Lampiran

### A. File Structure

```
sekolah_islam/
├── manage.py
├── requirements.txt
├── PRD_SEKOLAH_ISLAM.md
├── core/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── models.py          (~1,200 lines)
│   ├── views.py           (~6,300 lines)
│   ├── forms.py           (~2,100 lines)
│   ├── urls.py            (~320 lines)
│   ├── validators.py
│   ├── mail.py
│   ├── host.py
│   ├── notifications.py   (commented out)
│   ├── templates/
│   │   ├── accounts/login.html
│   │   ├── home/          (116 template files)
│   │   ├── layouts/
│   │   └── includes/
│   ├── templatetags/
│   ├── migrations/        (39 migration files)
│   ├── fixtures/
│   │   └── setup_data.json
│   ├── static/
│   └── media/
└── authentication/
    ├── views.py
    ├── forms.py
    ├── urls.py
    └── decorators.py
```

### B. Dependencies

```
django==5.0.6
pillow
pymysql
django-crum
phonenumbers
django-phonenumber-field
dj-database-url
django-import-export
django-auto-logout
pytz
xlwt
xlsxwriter
django-mathfilters
reportlab
pypdf2
requests
django-tinymce
xhtml2pdf
django-user-agents
```

---

**End of Document**
