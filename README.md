# Tarteel | ترتيل

Telegram bot that tracks a daily Quran wird and sends only today's pages. The whole UI is
Egyptian Arabic.

## Files
`bot.py` (the bot) · `prayer.py` (offline prayer-time calculator, no extra dependency) ·
`requirements.txt` · `.env.example`

## Setup
1. Create the bot with @BotFather (`/newbot`), name it **Tarteel | ترتيل**, copy the token.
2. **Backup group:** add the bot to your private group (-1004383995976) and make it an
   **admin** with *Pin messages* and *Delete messages*.
3. Put your Quran PDF next to `bot.py` as `quran.pdf` (604-page Madani mushaf works best).
4. `cp .env.example .env`, paste the token. If the PDF has cover pages before Quran page 1,
   set `PDF_OFFSET` to that number.
5. Install and run:
   ```
   pip install -r requirements.txt
   python bot.py
   ```
6. In BotFather, `/setcommands`:
   ```
   today - ورد النهاردة
   settings - الإعدادات
   goal - هدف الختمة
   prayer - تنبيهات الصلاة
   progress - تقدّمي
   pages - عدد الصفحات في اليوم
   time - ميعاد التذكير
   timezone - المدينة والمنطقة
   setpage - ابدأ من صفحة
   stop - وقّف التذكير
   menu - القائمة
   ```
   (`/health` and `/backup` are admin-only; leave them out of the public menu.)

## Settings keyboard (⚙️ الإعدادات)
One screen with: pages per day · khatma goal · reminder time · city & timezone · prayer warnings.

### 🎯 Khatma goal
Pick 15 / 30 / 60 / 90 days (or type 7-365) and the bot sets pages per day (`ceil(604 / days)`,
e.g. 30 days = 21 pages). `/progress` then shows pages done, and whether you are on schedule,
ahead or behind (in days), and how many pages a day you'd need to catch up. Finishing all 604
pages under the goal congratulates you and clears it. If you set a goal after already finishing
today's wird, it starts tomorrow so you aren't shown as a day behind.

### 🌍 City & timezone
Buttons for 19 Egyptian/Gulf/Jordan cities (sets timezone **and** location for prayer times),
London / New York / Istanbul (timezone only), 📍 share your location (stored rounded to ~1 km;
the nearest city's timezone is used if within 400 km), or type an IANA timezone by hand.

### 🕌 Prayer warnings
For each enabled prayer the bot sends a warning **1 hour before** and **30 minutes before**
with a **«✅ لقد صليت»** button. Pressing it cancels the remaining warning for that prayer.
Per-prayer on/off switches (so you can mute Fajr). Times are computed offline from your
location with the Egyptian General Authority method for Egypt, Umm al-Qura for Saudi/Qatar/
Bahrain/Yemen, and Muslim World League elsewhere. They are **approximate** (about a minute),
so the screen tells users to confirm from an official source. Verified against an independent
solar-position model, including daylight saving. Where twilight never reaches the Fajr/Isha
angle (high latitudes in summer) those two are simply skipped.

## Sending queue
Every reminder, catch-up wird and prayer warning goes through one queue that sends one user at
a time with `SEND_GAP` seconds between them (default 0.35). It obeys Telegram flood-waits (waits,
retries up to 3 times, then gives up), never queues the same job twice, and one failing job
can't stop the others.

## Blocked users
When a user blocks the bot (Telegram notifies instantly, or a send fails with "Forbidden"), they
are marked blocked: reminders, catch-up and prayer warnings stop, they're excluded from the
"reminders on" counts, and `/health` shows how many are blocked. If they message the bot again
or unblock it, everything resumes automatically.

## Missed reminders (catch-up)
A few seconds after startup, any user whose reminder time already passed today (in their
timezone), who hasn't finished or received today's wird, gets it through the queue with a
message saying the reminder was missed. Same day only. New users, and users who change their
reminder time or timezone after it has passed, start from the next day; users from an older
backup are skipped on the first run after upgrading.

## /health (admin only)
Works inside the backup group, or in private chat for IDs in `ADMIN_IDS`. Shows total users,
blocked users, users with reminders / prayer warnings / a goal, and for **today / last 7 days /
last 30 days**: active users, wirds completed, pages read (per-day averages) and average pages
per user who finished. "Active" = pressed a button or sent a message that day (Cairo time).

## How storage works (no database)
- All data is one file, `tarteel_data.zip` (a zip holding `tarteel_data.json`, about 2-3% of its
  raw size; old plain `.json` backups still load and migrate to zip on the next change).
- When anything changes, the bot (checking every 30s, and again on shutdown) uploads the file to
  the group, **pins it**, and deletes the previous copy, so the group always holds exactly one backup.
- On startup it reads the **pinned** file, restores everyone, and re-schedules every reminder.
- Collision-proofing: every change bumps a revision counter; storage is "dirty" while it differs
  from the last uploaded revision. Uploads run one at a time from a consistent snapshot, so a
  change made mid-upload is never lost, and simultaneous flushes collapse into one. Nothing
  uploads before the pinned backup has been read.
- If a pinned backup exists but can't be read, the bot refuses to start rather than overwrite it.
  If a pin fails, the old pinned copy is kept and it retries.
- `/backup` (admin) forces an immediate backup.
- Prayer-warning bookkeeping ("already warned", "I prayed") lives in memory only, so it doesn't
  cause backup churn; after a restart you might get one repeated warning at worst.

## Rules for the backup group
- Keep it private (the file contains chat IDs and approximate locations).
- Don't pin other messages there, and don't unpin/delete the bot's file.
- Run only **one** instance of the bot at a time.

## How the wird works
- Today's wird = the next N pages from the user's pointer; it only advances when they tap
  **✅ خلّصت وردي**, so missed days never skip pages. Wraps from 604 back to 1.
- Pages are rendered to JPG once and cached in `page_cache/`.

## Hosting
Needs to run 24/7 for reminders: a small VPS, Railway, or Fly.io. No persistent volume is
required for user data, since it restores from the pinned file.
