"""حساب مواعيد الصلاة (تقريبية) بدون أي مكتبات خارجية.

الخوارزمية هي نفس طريقة PrayTimes.org (معادلات موقع الشمس). المواعيد
تقريبية (دقة حوالي دقيقة أو اتنين) فمتتعتمدش عليها كمرجع شرعي رسمي.
"""
import math
from datetime import date, datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

PRAYERS = ("fajr", "dhuhr", "asr", "maghrib", "isha")

# زوايا الفجر والعشاء لكل طريقة حساب.
METHODS = {
    "egypt": {"fajr": 19.5, "isha": 17.5},      # الهيئة المصرية العامة للمساحة
    "makkah": {"fajr": 18.5, "isha_min": 90},   # أم القرى (العشاء بعد المغرب بـ 90 دقيقة)
    "mwl": {"fajr": 18.0, "isha": 17.0},        # رابطة العالم الإسلامي
}
_MAKKAH_TZ = {"Asia/Riyadh", "Asia/Qatar", "Asia/Bahrain", "Asia/Aden"}


def method_for_tz(tz: str) -> str:
    if tz == "Africa/Cairo":
        return "egypt"
    if tz in _MAKKAH_TZ:
        return "makkah"
    return "mwl"


# ───────────── دوال رياضية بالدرجات ─────────────
def _sin(d): return math.sin(math.radians(d))
def _cos(d): return math.cos(math.radians(d))
def _fix(a, b): return a - b * math.floor(a / b)
def _fix_angle(a): return _fix(a, 360.0)
def _fix_hour(a): return _fix(a, 24.0)


def _julian(y: int, m: int, d: int) -> float:
    if m <= 2:
        y -= 1
        m += 12
    a = math.floor(y / 100)
    b = 2 - a + math.floor(a / 4)
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def _sun_position(jd: float):
    """(ميل الشمس بالدرجات، معادلة الزمن بالساعات)."""
    d = jd - 2451545.0
    g = _fix_angle(357.529 + 0.98560028 * d)
    q = _fix_angle(280.459 + 0.98564736 * d)
    big_l = _fix_angle(q + 1.915 * _sin(g) + 0.020 * _sin(2 * g))
    e = 23.439 - 0.00000036 * d
    ra = math.degrees(math.atan2(_cos(e) * _sin(big_l), _cos(big_l))) / 15.0
    ra = _fix_hour(ra)
    eqt = q / 15.0 - ra
    decl = math.degrees(math.asin(_sin(e) * _sin(big_l)))
    return decl, eqt


def _mid_day(jd: float, t: float) -> float:
    return _fix_hour(12 - _sun_position(jd + t)[1])


def _angle_time(jd: float, lat: float, angle: float, t: float, ccw: bool = False) -> float:
    decl = _sun_position(jd + t)[0]
    noon = _mid_day(jd, t)
    x = (-_sin(angle) - _sin(decl) * _sin(lat)) / (_cos(decl) * _cos(lat))
    if abs(x) > 1:
        return math.nan  # الشمس مبتوصلش للزاوية دي (مناطق قريبة من القطب)
    v = math.degrees(math.acos(x)) / 15.0
    return noon + (-v if ccw else v)


def _asr_time(jd: float, lat: float, factor: int, t: float) -> float:
    decl = _sun_position(jd + t)[0]
    angle = -math.degrees(math.atan(1.0 / (factor + math.tan(math.radians(abs(lat - decl))))))
    return _angle_time(jd, lat, angle, t)


@lru_cache(maxsize=8192)
def _compute(y: int, m: int, d: int, lat: float, lon: float, tz: str, method: str) -> dict:
    """المواعيد بالساعات (من منتصف الليل بتوقيت المدينة)."""
    params = METHODS[method]
    offset = datetime(y, m, d, 12, tzinfo=ZoneInfo(tz)).utcoffset().total_seconds() / 3600.0
    jd = _julian(y, m, d) - lon / (15.0 * 24.0)
    guess = {k: v / 24.0 for k, v in dict(
        fajr=5, sunrise=6, dhuhr=12, asr=13, sunset=18, isha=18).items()}
    rise_set = 0.833

    times = {
        "fajr": _angle_time(jd, lat, params["fajr"], guess["fajr"], ccw=True),
        "sunrise": _angle_time(jd, lat, rise_set, guess["sunrise"], ccw=True),
        "dhuhr": _mid_day(jd, guess["dhuhr"]),
        "asr": _asr_time(jd, lat, 1, guess["asr"]),
        "maghrib": _angle_time(jd, lat, rise_set, guess["sunset"]),
    }
    if "isha_min" in params:
        times["isha"] = times["maghrib"] + params["isha_min"] / 60.0
    else:
        times["isha"] = _angle_time(jd, lat, params["isha"], guess["isha"])

    shift = offset - lon / 15.0
    return {k: v + shift for k, v in times.items() if not math.isnan(v)}


def prayer_times(day: date, lat: float, lon: float, tz: str, method: str | None = None) -> dict:
    """{اسم: datetime بتوقيت المدينة}. الصلوات اللي مبتتحسبش (قطب) بتتشال."""
    method = method or method_for_tz(tz)
    hours = _compute(day.year, day.month, day.day, round(lat, 3), round(lon, 3), tz, method)
    base = datetime(day.year, day.month, day.day, tzinfo=ZoneInfo(tz))
    return {k: base + timedelta(minutes=round(v * 60)) for k, v in hours.items()}


def next_prayer(lat: float, lon: float, tz: str, now: datetime, method: str | None = None):
    """(اسم الصلاة، وقتها، تاريخها المحلي ISO) لأقرب صلاة بعد now، أو None."""
    local = now.astimezone(ZoneInfo(tz))
    for add in (0, 1):
        day = local.date() + timedelta(days=add)
        times = prayer_times(day, lat, lon, tz, method)
        for name in PRAYERS:
            t = times.get(name)
            if t is not None and t > now:
                return name, t, day.isoformat()
    return None
