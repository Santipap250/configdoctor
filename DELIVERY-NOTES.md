# Phase 1–2 Delivery Notes — OBIX Config Doctor

**สถานะ:** ทดสอบผ่าน 322/322 tests ทุกครั้งหลังแก้ + smoke-test ทุก route ที่ย้ายด้วย Flask test client (ทั้งหมด 200/302, ไม่มี 500)

## วิธีติดตั้ง
1. **ลบไฟล์**: `nav.html` ที่ root ของ repo (ไฟล์กำพร้า ไม่มีที่ไหนอ้างอิง — ยืนยันด้วย grep ทั้งโปรเจกต์แล้ว)
2. **แทนที่ไฟล์เดิม**: `app.py`, `static/manifest.json`, `static/css/site-theme.css`, `static/css/style.css`
3. **เพิ่มไฟล์ใหม่**: โฟลเดอร์ `blueprints/` ทั้งหมด (`__init__.py`, `content_pages.py`, `tools_vtx.py`, `tools_static.py`, `tools_advisor.py`)
4. รัน `pytest` เพื่อยืนยัน (ควรได้ 322 passed)

## สิ่งที่เปลี่ยน

### `app.py` — แตกเป็น Blueprints (Phase 2, บางส่วน)
ย้าย 21 routes ที่เป็น render-only ไม่มี business logic ออกไปเป็น Blueprint แยกตามหมวด:
- `blueprints/content_pages.py` → `/about /team /changelog /military-uas`
- `blueprints/tools_vtx.py` → `/vtx /vtx-range /vtx-smartaudio`
- `blueprints/tools_static.py` → `/landing / /ping /fpv /cli_surgeon /rates-visualizer /cli-comparator /blackbox /esc-checker /fpv-trainer /flight-quiz /bf-wizard /build-card /tuning-log /leaderboard /battery-health /motor-thermal /loop-analyzer`
- `blueprints/tools_advisor.py` → `/pid-advisor /quick-tune /api/symptom/<id>`

**ที่ตั้งใจ "ไม่ย้าย" ในรอบนี้** (ยังอยู่ใน `app.py`): route ที่มี business logic ผูกกับ global state (`_get_db`, rate limiter, gear module, analyzer modules) เช่น `/app`, `/motor-prop`, `/fpv-gear`, `/blackbox/analyze`, `/analyze_cli`, `/compare_cli`, `/osd*`, `/api/*`, `/downloads*`, `/rpm-filter`, sitemap/robots/healthz — เพราะย้ายตอนนี้เสี่ยง circular-import/สภาวะ race มากกว่าจะได้ประโยชน์ ควรทำเป็น Phase ถัดไปโดยแยก shared state (`_get_db`, `_rate`, `PRESET_GROUPS` ฯลฯ) ออกเป็น `core.py`/`extensions.py` ก่อน แล้วค่อยย้าย route กลุ่มนี้

Helper functions ที่ test เดิมอ้างถึงโดยตรง (`validate_input`, `_handle_analysis_post`, `app`) **ไม่ถูกย้าย** เพื่อไม่ให้ `import app as A` ใน `tests/test_analyzer_route_fixes.py` พัง

### `static/manifest.json` — แก้ PWA icon mapping
- ไอคอน 512px ชี้ไปที่ `/static/img/icon-512.png` (ของจริง) แทน `favicon.png` (ผิดไฟล์เดิม)
- เพิ่ม icon variant `purpose: "maskable"` สำหรับ Android adaptive icon — **หมายเหตุ:** ไอคอนปัจจุบันอาจไม่มี safe-zone padding ที่ถูกออกแบบมาสำหรับ maskable โดยเฉพาะ ถ้าโลโก้ถูกครอปมุมบนมือถือ Android ควรออกแบบไอคอนเวอร์ชัน maskable แยกต่างหาก (มี safe zone 40% ตรงกลาง)

### `static/css/site-theme.css` + `static/css/style.css` — รวมค่าสีให้ตรงกัน
พบว่าทั้งสองไฟล์ประกาศ CSS custom properties (`--bg`, `--border`, `--blue`, `--red`, `--purple` ฯลฯ) คนละค่ากัน แต่หลายหน้าในเว็บโหลดคนละไฟล์ (`about.html` ใช้ `site-theme.css`, `cli_comparator.html` ใช้ `style.css`) ทำให้สีพื้นหลัง/เส้นขอบไม่ตรงกันข้ามหน้า **แก้แบบไม่เสี่ยง**: ปรับให้ "ค่า" ตรงกัน โดย **ไม่เปลี่ยนชื่อตัวแปร** เลย — เพื่อไม่ให้ selector ใด ๆ ในเทมเพลตที่อ้างอิงชื่อเดิมพัง

## สิ่งที่ยังไม่ได้ทำ (Next Phase — ตามแผนในรายงาน audit)
- ดึง inline `<style>` ที่ซ้ำในทุกเทมเพลต (30/30) ออกมาเป็น `components.css` กลาง
- เพิ่ม Jinja2 `{% extends %}` + `base.html` (ตอนนี้ทุกหน้าเป็น standalone HTML เต็มรูปแบบ ไม่มี template inheritance เลย)
- บีบอัดวิดีโอพื้นหลัง (~21MB รวม)
- ย้าย route ที่มี business logic ที่เหลือเข้า Blueprints (ต้องแยก shared state ออกเป็น core module ก่อน)
