# PRD: Generate Jadwal Pelajaran Otomatis

**Aplikasi:** Sekolah Islam — Sistem Informasi Manajemen Pesantren
**Modul:** Kurikulum → Jadwal Pelajaran (Timetable) → Auto-Generate
**Versi Dokumen:** 2.8 (revisi — **urutan isi dirombak**: pasangan melewati istirahat menjadi **last resort mutlak SETELAH fase jam tunggal**, sehingga "setiap pelajaran tidak terjeda istirahat" diusahakan maksimal; iterasi `TeacherSubject` dibuat deterministik dengan `order_by('teacher_subject_id')`; sebelumnya: v2.7 pasangan bebas-istirahat didahulukan per tier, v2.6 aturan hari-berurutan dilonggarkan jika terpaksa, sesi 2 jam, maks 2 jam/mapel/hari, tanpa jeda kosong)
**Status:** Aktif (sudah berjalan di produksi)
**Referensi:** `PRD_SEKOLAH_ISLAM.md` §5.12, §6 · `PRODUCT_SPEC_SEKOLAH_ISLAM.md` §25 (US-058 s/d US-076)

---

## Catatan Revisi

Dokumen ini adalah revisi dari draf PRD "Generate Jadwal Otomatis" sebelumnya, yang semula ditulis sebagai rancangan generik (data Guru/Kelas/Ruangan/Mapel bebas konteks). Setelah dicocokkan dengan PRD dan Product Spec aplikasi **Sekolah Islam** yang sudah diimplementasikan, dokumen ini diperbarui agar konsisten dengan:

- Nama model & field yang benar-benar dipakai di database (Django ORM).
- Algoritma auto-generate yang **benar-benar berjalan** di produksi (bukan rancangan backtracking/CSP teoretis).
- Constraint yang **benar-benar divalidasi** sistem saat ini, dan mana yang masih berupa rekomendasi/backlog.
- Tech stack aktual (Django 5.0.6, MySQL, jQuery AJAX, Bootstrap 5/Soft UI Dashboard).

Bagian [13. Gap Analysis](#13-gap-analysis--rekomendasi-peningkatan) merangkum apa saja dari draf awal yang **belum** ada di implementasi aktual, dan bagian [14. Catatan Ketidaksesuaian Data](#14-catatan-ketidaksesuaian-data) mencatat satu-dua hal di dokumen sumber yang perlu dikonfirmasi.

---

## 1. Latar Belakang

Modul Jadwal Pelajaran pada aplikasi Sekolah Islam memungkinkan admin menyusun jadwal mengajar mingguan (guru, mapel, kelas, ruangan, periode) melalui kombinasi **auto-generate** dan **drag-and-drop manual**. Fitur ini sudah *Aktif* di produksi dengan Menu ID `JADWAL`, di bawah URL prefix `/kurikulum/jadwal/`.

## 2. Tujuan

- Mengisi slot jadwal (hari × periode) untuk setiap kombinasi Kelas–Mapel–Guru secara otomatis, sejumlah jam yang ditetapkan di **Guru Per Mapel (TeacherSubject.hours)**.
- Menghindari konflik guru, ruangan, dan kelas pada slot yang sama.
- Menyediakan hasil berstatus **draft** yang bisa disempurnakan manual (drag-and-drop) sebelum dipublikasikan (**published**).

## 3. Ruang Lingkup

### Termasuk:
- Auto-generate jadwal reguler mingguan, di-scope per **Timetable** (kombinasi Tahun Ajaran + Semester).
- Validasi konflik guru/ruangan/kelas dan ketersediaan waktu masing-masing saat generate.
- Penjadwalan manual pelengkap via drag-and-drop dari panel "Belum Dijadwalkan" (unscheduled pool).

### Tidak termasuk (modul/fitur terpisah):
- **Guru Pengganti (SubstituteAssignment)** — penggantian guru pada slot tertentu untuk tanggal spesifik; ini fitur pasca-jadwal-final, terpisah dari proses generate.
- Penilaian, Keuangan, Kegiatan Asrama — belum diimplementasi, di luar cakupan modul ini.
- Jadwal ekstrakurikuler dan jadwal ujian — belum terintegrasi ke model Timetable/Period yang sama.

## 4. Model Data yang Digunakan

Semua model berada dalam satu app Django (`apps/models.py`), dengan penamaan Inggris di kode dan label Indonesia di UI. Padanan dengan istilah yang dipakai sehari-hari di aplikasi:

| Istilah UI (Indonesia) | Model Django | Keterangan |
|---|---|---|
| Guru | `Teacher` | — |
| Kelas | `Grade` | — |
| Ruangan | `Room` | `room_id`, `room_name` (lihat catatan §14 soal field Kapasitas) |
| Mata Pelajaran | `Subject` | `subject_id` (CharField PK, max 10), `subject_name`, `description` |
| Kelompok Mapel | `SubjectGroup` | `group_id`, `group_code`, `group_name` — lihat catatan §14 |
| Guru Per Mapel | `TeacherSubject` | `teacher`, `grade_subject`, `hours` (jam/minggu) |
| Mapel Per Kelas | `GradeSubject` | `grade`, `subject`, `room` (ruangan default), `keterangan` |
| Jadwal (induk) | `Timetable` | `name`, `school_year` (FK), `semester` (1=Ganjil/2=Genap), `status` (draft/published), `notes` |
| Periode | `Period` | `timetable` (FK), `period_name`, `start_time`, `end_time`, `order`, `day`, `is_break` |
| Slot Jadwal | `TimetableSlot` | `timetable`, `lesson`, `period`, `room`, `is_manual` |
| Pelajaran (internal) | `Lesson` | `timetable`, `grade_subject`, `teacher`, `hours_per_week` — **tanpa CRUD UI**, dibuat otomatis saat generate/drag-drop |
| Ketersediaan Guru | `TeacherAvailability` | `timetable`, `teacher`, `period`, `day`, `is_available` |
| Ketersediaan Ruangan | `RoomAvailability` | `timetable`, `room`, `period`, `day`, `is_available` |
| Ketersediaan Kelas | `GradeAvailability` | `timetable`, `grade`, `period`, `day`, `is_available` |
| Guru Pengganti | `SubstituteAssignment` | `slot` (FK → TimetableSlot), `substitute_teacher`, `reason`, `date` |

**Hal penting yang berbeda dari draf awal:**
- Ketersediaan (Guru/Ruangan/Kelas) **di-scope per Timetable**, bukan global — satu guru bisa punya ketersediaan berbeda di jadwal Semester Ganjil vs Genap.
- `Lesson` adalah unique per `(timetable, grade_subject, teacher)` — artinya **team teaching (2 guru untuk 1 mapel di 1 kelas) sudah didukung secara struktural**, cukup buat 2 baris `TeacherSubject` untuk `grade_subject` yang sama.
- Hari (`day`) disimpan sebagai kode 3-huruf: `MON/TUE/WED/THU/FRI/SAT/SUN`.

## 5. Hard Constraint (Divalidasi Sistem Saat Generate)

Berdasarkan algoritma yang berjalan (§25.11 US-068), yang **benar-benar dicek**:

1. **Konflik guru** — guru yang sama tidak ditempatkan di dua kelas pada hari & periode yang sama.
2. **Konflik kelas** — kelas yang sama tidak diisi dua mapel pada hari & periode yang sama.
3. **Konflik mapel-kelas** — `grade_subject` yang sama tidak dijadwalkan dua kali pada hari & periode yang sama.
4. **Konflik ruangan** — implisit lewat pengecekan `RoomAvailability` + slot yang sudah terisi.
5. **Ketersediaan Guru** — sesuai `TeacherAvailability` untuk timetable tsb (blacklist: hanya ditolak jika ada record `is_available=False`).
6. **Ketersediaan Ruangan** — sesuai `RoomAvailability` (blacklist).
7. **Ketersediaan Kelas** — sesuai `GradeAvailability` (blacklist).
8. **Jam sesuai penugasan** — total slot yang dibuat untuk satu `Lesson` mengikuti `hours_per_week` dari `TeacherSubject.hours`.
9. **Scoping tahun ajaran & semester** — hanya `GradeSubject`/`TeacherSubject`/`Grade` yang sesuai `school_year` + `semester` milik `Timetable` yang diikutsertakan.
10. **Sesi 2 jam & maksimal 2 jam/hari** — untuk SEMUA `Lesson`: jam dipecah menjadi sesi **2 jam pelajaran berturut-turut pada hari yang sama** (1 sesi = 1 hari, maksimal 2 jam/mapel/kelas per hari); sisa jam ganjil dijadwalkan **1 jam pada hari lain**. Jika sesi 2 jam tidak memungkinkan, jam jatuh ke fallback 1 jam per hari.
11. **Tidak terpotong istirahat — diusahakan untuk setiap pelajaran** — pasangan 2 jam wajib berada pada dua periode berurutan yang **tidak dijahit jam istirahat** di tengahnya. **Hard untuk Laboratorium** (nama ruangan mengandung "lab"); **untuk semua mapel diusahakan**. **Urutan isi per lesson:** **(A)** pasangan 2 jam **bebas-istirahat** (tier: hari non-berurutan → hari berurutan, relaksasi aturan hari-berurutan "jika terpaksa") → **(B)** jam tunggal (fase ketat → fase relaksasi) → **(C)** pasangan **melewati istirahat** — non-lab, **last resort mutlak** — hanya dipakai bila fase A+B menyisakan **≥2 jam yang belum terisi** (setelah itu jam tunggal dilanjutkan untuk sisa ganjil). Dengan urutan ini pasangan melewati istirahat hanya muncul bila **mustahil** mengisi sisa jam tanpa memotong istirahat (bandingkan v2.7: fase pasangan crossing dijalankan *sebelum* jam tunggal sehingga masih bisa menghasilkan pelajaran terjeda istirahat).
12. **Tanpa jeda jam kosong** — untuk **setiap kelas dan setiap guru per hari**, slot yang terisi harus **berurutan/contiguous**: tidak boleh ada periode mengajar kosong di antara slot terisi (jeda hanya diizinkan di awal/akhir hari atau pada jam istirahat). Divalentidasi pada saat menempatkan sesi 2 jam maupun jam tunggal — invariant terjaga selama generate berjalan.
13. **Tidak berulang pada hari berurutan (aturan lunak — dilonggarkan jika terpaksa)** — sesi (2 jam atau 1 jam) milik satu `Lesson` (mapel per kelas) **tidak boleh jatuh pada dua hari yang berurutan** (mis. Senin & Selasa); hari sesi harus berjarak minimal 1 hari kosong. **Setiap keputusan penempatan selalu mencoba aturan ketat lebih dulu.** Aturan ini hanya dilonggarkan bila **terpaksa**: ketika seluruh kandidat penempatan (fase sesi 2 jam pass 1+2, maupun fase jam tunggal) gagal **hanya** karena cek hari-berurutan — sistem mengulang dengan cek tersebut dinonaktifkan agar jam tetap terjadwal penuh. Tanpa fallback ini, lesson dengan ketersediaan guru < 3 hari bebas-berurutan (mis. guru yang hanya bebas Senin–Kamis untuk 5 jam) **mustahil** penuh secara matematis dan selalu kekurangan jam (mis. IPA 5 jam → 4 jam).

**Belum divalidasi sistem saat ini** (lihat §13 untuk rekomendasi):
- Kapasitas ruangan vs jumlah siswa kelas.
- Batas maksimal jam mengajar guru per minggu.

## 6. Soft Constraint

**Distribusi jam merata per hari** sudah diimplementasi melalui strategi **round-robin**: untuk setiap `Lesson`, hari mulai diproses dirotasi (offset berbeda per lesson) sehingga jam mengajar tersebar merata antar hari, bukan menumpuk di hari pertama.

**Pasangan jam bebas istirahat — diusahakan untuk setiap mapel**: sistem selalu memilih pasangan 2 jam yang tidak terpotong istirahat lebih dulu (fase A), lalu mengisi sisa jam dengan jam tunggal (fase B); pasangan yang melewati istirahat baru dipertimbangkan sebagai **last resort mutlak** pada fase C — setelah fase A **dan** fase B gagal menyisakan ≥2 jam — lihat constraint #11 untuk aturan ketat Laboratorium.

Status sisanya: **belum ada soft-constraint scoring** di algoritma auto-generate (selain round-robin & preferensi bebas-istirahat). Item-item lain seperti menghindari gap, membatasi jam berturut-turut, atau prioritas constraint dipindahkan ke bagian [Gap Analysis](#13-gap-analysis--rekomendasi-peningkatan) sebagai usulan peningkatan, bukan requirement yang sudah terpenuhi.

## 7. Alur Proses (As-Built)

1. Admin membuat **Timetable** baru: nama, Tahun Ajaran, Semester → status awal `draft`.
2. Admin mengatur **Period** (jam pelajaran per hari, termasuk slot istirahat `is_break`).
3. Admin mengatur **Ketersediaan Guru**, **Ketersediaan Ruangan**, dan **Ketersediaan Kelas** (dua tab dalam satu modal: "Ketersediaan Ruangan" + "Ketersediaan Kelas") — masing-masing lewat grid checkbox per hari × periode.
4. Data **GradeSubject** (Mapel Per Kelas) dan **TeacherSubject** (Guru Per Mapel) sudah harus ada untuk tahun ajaran & semester yang sama dengan Timetable.
5. Admin membuka halaman **Grid View** (`/kurikulum/jadwal/<id>/grid/`) dan menekan tombol **"Generate"**.
6. Request AJAX ke `/kurikulum/jadwal/view/<id>/generate/` → sistem membuat/mengisi `Lesson` dan `TimetableSlot` sesuai algoritma di §8.
7. Grid ter-update setelah generate (halaman di-reload oleh JS); pelajaran yang gagal dijadwalkan otomatis tetap muncul di panel **"Belum Dijadwalkan"**.
8. Admin melengkapi sisa jadwal secara manual via **drag-and-drop**. Menjalankan ulang generate **selalu replace**: semua slot lama dihapus dulu, lalu jadwal baru dibuat dari nol.
9. Admin mengubah status Timetable dari `draft` ke `published` saat jadwal siap dipakai.

## 8. Algoritma Auto-Generate (As-Built)

Algoritma **greedy dengan rotasi round-robin antar hari** (bukan constraint-solving dengan backtracking):

```
1. Ambil GradeSubject untuk (school_year, semester) milik Timetable ini
2. Ambil TeacherSubject untuk masing-masing GradeSubject tsb
3. Hapus semua TimetableSlot lama (replace)
4. Kelompokkan Period non-break per hari (MON..SUN), urutkan per `order`

5. Untuk setiap TeacherSubject (kombinasi Guru + Mapel + Kelas) — **urutan
   deterministik `order_by('teacher_subject_id')`**, dengan offset hari
   yang dirotasi per-lesson (round-robin):
   a. get_or_create Lesson (timetable, grade_subject, teacher);
      sinkronkan Lesson.hours_per_week = TeacherSubject.hours
   b. **FASE A — Sesi 2 jam bebas-istirahat** untuk SEMUA mapel (bagian
      Lab yang tidak pernah memasuki fase C): hitung pasangan direncanakan
      = hours // 2. Untuk tiap pasangan (urut round-robin antar hari,
      1 hari hanya boleh diisi 1 sesi per Lesson — cap maksimal
      2 jam/mapel/hari):
      - Pass A1 (semua mapel; satu-satunya pasangan untuk Lab): cari
        sepasang periode BERURUTAN pada hari tersebut yang TIDAK terpotong
        jam istirahat (tidak ada `Period.is_break` dengan order di antara
        kedua periode), hari non-berurutan, dan lolos seluruh cek di bawah.
      - Pass A2 (semua mapel): pasangan bebas-istirahat yang sama, tapi
        pada hari berurutan (relaksasi anti-hari-berurutan, jika terpaksa).
      - Cek kontiguity (tanpa jeda): union slot kelas tsb + slot guru tsb
        pada hari tersebut + kedua kandidat periode harus berurutan
        (jeda hanya boleh di awal/akhir hari atau jam istirahat).
      - Cek hari berurutan: hari tersebut tidak boleh berdampingan (D-1/D+1)
        dengan hari yang sudah berisi sesi Lesson ini (anti-repeat) —
        **berlaku pada Pass A1; Pass A2 adalah relaksasi aturan ini
        "jika terpaksa"**; cap 2 jam/hari tetap berlaku.
      - Jika ditemukan: buat kedua slot sekaligus dalam satu ruangan sama
        (prefer GradeSubject.room, fallback ruangan lain yang valid untuk
        kedua periode); hari tersebut ditandai penuh (2 jam) dan tidak
        menerima sesi/jam tambahan lagi; pasangan terpakai bertambah 1.
      - Jika pasangan tidak muat: lanjut pasangan berikutnya; apabila satu
        kali percobaan pasangan sudah gagal total (state tidak berubah),
        hentikan fase A.
   c. **FASE B — JAM TUNGGAL** (sisa jam termasuk jam ganjil, atau pasangan
      yang gagal) dijadwalkan **tanpa memakai pasangan melewati istirahat** —
      maksimal 1 jam per hari, hari yang sudah berisi 2 jam (sesi) atau
      1 jam (tunggal) untuk Lesson ini dilewati, sehingga
      cap maksimal 2 jam/mapel/hari selalu terpenuhi. Putaran round-robin
      antar hari; per hari, coba periode berikutnya yang belum dicoba
      (urut `order`) selama masih ada (hari, periode) yang belum dicoba:
      Cari slot (hari, periode) yang lolos semua cek:
          * Tidak ada konflik guru di slot itu
          * Tidak ada konflik kelas di slot itu
          * Tidak ada konflik mapel-kelas (grade_subject) di slot itu
          * Guru tersedia — TIDAK punya TeacherAvailability is_available=False
          * Kelas tersedia — TIDAK punya GradeAvailability is_available=False
          * Ruangan tersedia — TIDAK punya RoomAvailability is_available=False
            (prefer ruangan default GradeSubject.room, fallback ruangan lain;
             jika tidak ada ruangan valid, slot tetap dibuat dengan room kosong)
          * Kontiguity — union slot kelas + slot guru pada hari itu + kandidat
            harus berurutan (tanpa jeda kecuali istirahat/awal/akhir hari)
          * Hari berurutan — hari kandidat tidak boleh didekati hari yang
            sudah berisi sesi Lesson ini (D-1 / D+1)
      - Jika ditemukan: buat TimetableSlot, tandai is_manual=False
      - Iterasi berikutnya mencoba periode berikutnya pada hari yang sama
      - **Dua fase (aturan lunak):** fase 1 berjalan ketat (cek hari
        berurutan aktif). Bila fase 1 selesai tanpa hasil dan sisa jam
        masih ada, **fase 2** mengulang dari awal dengan cek hari-berurutan
        **dinonaktifkan** (hari yang sudah berisi jam untuk Lesson ini tetap
        ditolak demi cap 2 jam/mapel/hari) — fallback "jika terpaksa".
   d. **FASE C — pasangan MELEWATI ISTIRAHAT (hanya non-Lab, LAST RESORT
      MUTLAK):** bila setelah fase A+B masih ada sisa jam ≥2 **dan**
      pasangan terpakai < pasangan direncanakan: ulangi fase pasangan
      dengan pasangan berurutan yang melewati istirahat — tier hari
      non-berurutan lalu hari berurutan (relaksasi) — memakai seluruh
      cek yang sama (kontiguity, anti-hari-berurutan, cap 2 jam/hari).
      Untuk tiap pasangan yang berhasil, lanjutkan fase B (ketat lalu
      relaksasi) guna mengisi sisa jam ganjil. Lab tidak pernah memasuki
      fase ini.
   e. Lesson dianggap "failed" untuk sisa jamnya HANYA ketika seluruh
      kombinasi (hari, periode) sudah dicoba di KEDUA fase jam tunggal
      tanpa hasil — tetap muncul di panel "Belum Dijadwalkan"

6. Return ringkasan: {success, generated: <jumlah slot dibuat>, failed: <jumlah jam gagal>}
```

**Catatan semantik ketersediaan (blacklist):** Sistem hanya menolak slot jika ada record ketersediaan dengan `is_available=False`. Jika admin tidak mengatur ketersediaan sama sekali, semua slot dianggap tersedia — konsisten dengan endpoint `move-slot` dan `schedule-lesson`.

**Implikasi praktis dari pendekatan greedy:**
- Karena tidak ada backtracking, urutan pemrosesan `TeacherSubject` memengaruhi hasil — kombinasi yang diproses lebih dulu "mengambil" slot yang mungkin dibutuhkan kombinasi lain yang lebih terbatas ketersediaannya. **Sejak v2.8 urutan dibuat deterministik** dengan `.order_by('teacher_subject_id')` (sebelumnya tanpa `ORDER BY` sehingga urutan bergantung plan database — hasil generate bisa berbeda antar eksekusi).
- Round-robin memastikan jam tersebar merata antar hari, tapi hasil tetap **tidak dijamin optimal** — cukup cepat dan hasilnya bisa langsung disempurnakan manual lewat drag-and-drop.

## 9. Output & Fitur Pendukung (Sudah Aktif)

| Fitur | Keterangan |
|---|---|
| **6 Mode Tampilan** | Kelas Standar/Kompak, Guru Standar/Kompak, Ruangan Standar/Kompak |
| **Panel Belum Dijadwalkan** | Menampilkan Lesson yang jam-nya belum penuh terisi, dengan sisa jam |
| **Drag-and-Drop** | Jadwalkan dari pool, pindahkan antar slot, hapus slot — real-time tanpa reload; di mode Kelas, drop hanya diterima ke baris kelas yang sama (validasi `target_grade_id` di client & server) |
| **Filter** | Berdasarkan kelas/guru/ruangan (sesuai mode aktif), disimpan di `localStorage` per jadwal |
| **Analisis Beban Mengajar** | Card ringkasan pemanfaatan guru & ruangan (jam terjadwal / tersedia) dengan progress bar berwarna |
| **Export PDF** | Sesuai mode tampilan aktif, via `xhtml2pdf`, ukuran A4 landscape |
| **Subject Colors** | 12 warna berbeda per mapel (berdasarkan hash `subject_id`), konsisten di semua mode |
| **Dark Mode** | Didukung penuh di semua komponen grid |
| **Frozen Column** | Kolom label (kelas/guru/ruangan) tetap terlihat saat scroll horizontal |

## 10. Endpoints (As-Built)

| URL | Method | Fungsi |
|---|---|---|
| `/kurikulum/jadwal/` | GET | Index jadwal |
| `/kurikulum/jadwal/add/` | GET/POST | Tambah jadwal |
| `/kurikulum/jadwal/<id>/update/` | GET/POST | Edit jadwal |
| `/kurikulum/jadwal/<id>/delete/` | POST | Hapus jadwal |
| `/kurikulum/jadwal/<id>/grid/` | GET | Grid view (6 mode) |
| `/kurikulum/jadwal/<id>/export-pdf/` | GET | Export PDF sesuai mode aktif |
| `/kurikulum/jadwal/ajax/save-periods/` | POST | Simpan periode |
| `/kurikulum/jadwal/ajax/save-availability/` | POST | Simpan ketersediaan guru |
| `/kurikulum/jadwal/ajax/save-room-availability/` | POST | Simpan ketersediaan ruangan |
| `/kurikulum/jadwal/ajax/save-grade-availability/` | POST | Simpan ketersediaan kelas |
| `/kurikulum/jadwal/view/<id>/generate/` | POST | **Auto-generate jadwal** |
| `/kurikulum/jadwal/ajax/schedule-lesson/` | POST | Jadwalkan manual dari pool |
| `/kurikulum/jadwal/ajax/move-slot/` | POST | Pindahkan slot (drag-drop) |
| `/kurikulum/jadwal/ajax/delete-slot/` | POST | Hapus slot |

## 11. Non-Functional Requirements

| Aspek | Implementasi |
|---|---|
| Stack | Django 5.0.6, Python 3.11, MySQL, jQuery 3.x + AJAX |
| UI | Soft UI Dashboard (Argon/Bootstrap 5), DataTables untuk index |
| Bahasa | Bahasa Indonesia (`id`), Timezone Asia/Jakarta (naive datetime, `USE_TZ=False`) |
| Audit Trail | `entry_date`, `entry_by`, `update_date`, `update_by` di setiap model (via `django-crum`) |
| Cetak | PDF via `xhtml2pdf` (Pisa), Excel via `xlwt`/`xlsxwriter` |
| Otorisasi | RBAC per menu via tabel `Auth`, Menu ID `JADWAL` |

## 12. Kriteria Keberhasilan

- 0% konflik guru/ruangan/kelas pada jadwal berstatus `published`.
- Panel "Belum Dijadwalkan" kosong (atau minim) setelah kombinasi generate + pelengkapan manual.
- Waktu proses generate untuk satu Timetable selesai dalam hitungan detik (algoritma first-fit ringan secara komputasi).

## 13. Gap Analysis — Rekomendasi Peningkatan

Item-item berikut ada di draf PRD awal (versi generik/teoretis) tapi **belum** ada di implementasi Sekolah Islam saat ini. Disusun sebagai backlog, bukan requirement yang sudah terpenuhi:

| Item | Status Saat Ini | Rekomendasi |
|---|---|---|
| Validasi kapasitas ruangan vs jumlah siswa | Field `Room.capacity` ada (default 0) tapi **tidak divalidasi** saat generate | Cek `Room.capacity` vs jumlah siswa kelas saat generate (abaikan jika capacity=0) |
| Batas maksimal jam mengajar guru/minggu | Tidak ada field/limit di `Teacher`, tidak divalidasi | Tambah field `max_hours_per_week`, cek saat generate |
| Distribusi jam merata per hari | **Sudah diimplementasi** (round-robin antar hari, offset per-lesson) | — |
| Menghindari gap kosong di jadwal kelas/guru | Tidak ada | Tambah scoring soft-constraint pasca slot-pertama-valid |
| Sesi 2 jam otomatis untuk semua mapel | **Sudah diimplementasi** — semua mapel diusahakan sesi 2 jam berturut-turut/hari (maks 2 jam/mapel/hari), bebas istirahat (wajib untuk Lab); fallback 1 jam/hari | Opsional: flag `prefer_double_period` di `GradeSubject` jika ingin aturan berlaku selektif per mapel |
| Prioritas/bobot constraint | Tidak ada | Perlu desain skema skor jika ingin soft-constraint dioptimalkan |
| Validasi kelengkapan data sebelum generate | Sebagian — hanya alert jika tahun ajaran/semester Timetable belum diisi | Tambah pre-check: apakah semua Grade sudah punya GradeSubject & TeacherSubject sebelum generate ditekan |
| Multi-draft/versioning jadwal | Tidak ada — satu Timetable = satu status draft/published | Bisa ditambah jika sekolah ingin membandingkan beberapa skenario |

## 14. Catatan Ketidaksesuaian Data

Dua hal berikut ditemukan saat membandingkan dokumen sumber, perlu dikonfirmasi ke tim/kode aktual:

1. **Field Kapasitas pada Room** — ~~Spesifikasi model `Room` di Product Spec (US-061) hanya mendefinisikan `room_id` dan `room_name`~~ **Terkonfirmasi:** model `Room` di `models.py` sudah punya field `capacity` (`PositiveIntegerField`, default 0). Product Spec US-061 perlu dilengkapi dengan field ini. Validasi kapasitas vs jumlah siswa saat generate masih menjadi backlog (§13).
2. **SubjectGroup sudah terhubung ke Subject** — ~~belum ada FK~~ **Terkonfirmasi:** model `Subject` di `models.py` punya field `group = ForeignKey(SubjectGroup)`. Kelompok mapel sudah bisa dipakai untuk pengelompokan mapel.

## 15. Glossary Tambahan

Istilah spesifik modul ini melengkapi Glossary utama di `PRD_SEKOLAH_ISLAM.md` §12:

| Istilah | Keterangan |
|---|---|
| **Lesson** | Model internal (tanpa CRUD UI) yang merepresentasikan "kebutuhan jam" satu kombinasi Guru+Mapel+Kelas dalam satu Timetable |
| **First-fit** | Strategi algoritma: ambil slot kosong valid pertama yang ditemukan, tanpa mengevaluasi alternatif lain |
| **Unscheduled Pool** | Panel berisi Lesson yang jam-nya belum (sepenuhnya) terisi ke TimetableSlot |
| **is_manual** | Flag pada TimetableSlot untuk membedakan slot hasil generate otomatis vs input manual (drag-drop) |

---

**Status Dokumen:** Revisi ini menggantikan draf v1.0 sebagai referensi yang selaras dengan kode yang berjalan di produksi. Bagian §13 dan §14 sebaiknya didiskusikan dengan tim pengembang sebelum dieksekusi sebagai backlog resmi.
