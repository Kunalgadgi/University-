"""
app.py  —  Master Control System
University Admission Portal | Admin-only Flask application
"""

import os, logging
from functools import wraps
from datetime import datetime
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, send_from_directory)
from werkzeug.utils import secure_filename

# ── App Setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__,
            template_folder="master_control/templates",
            static_folder="master_control/static")

app.secret_key = os.environ.get("SECRET_KEY", "mc-super-secret-change-in-prod-2024")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024          # 5 MB
UPLOAD_DIR = os.path.join("master_control", "static", "master_control", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMG  = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_FILE = {"pdf", "doc", "docx", "png", "jpg", "jpeg"}

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("master_control.log")]
)
logger = logging.getLogger("master_control")

# ── Models ────────────────────────────────────────────────────────────────────
from master_control.models import (
    init_db, get_portal_settings, save_portal_settings,
    get_all_courses, get_active_courses, get_course, save_course,
    delete_course, bulk_toggle_courses,
    get_all_form_configs, get_form_config, save_form_config, delete_form_config,
    get_all_advertisements, get_active_advertisements, get_advertisement,
    save_advertisement, delete_advertisement, bulk_toggle_advertisements,
    get_all_notices, get_active_notices, get_notice, save_notice,
    delete_notice, bulk_toggle_notices,
    get_all_sliders, get_active_sliders, get_slider, save_slider,
    delete_slider, bulk_toggle_sliders,
    get_admin_user, verify_password, create_superuser, get_dashboard_stats
)

with app.app_context():
    init_db()

# ── Context Processor (Django-equivalent) ─────────────────────────────────────
@app.context_processor
def global_context():
    """Inject portal-wide data into every template — mirrors Django context processors."""
    s = get_portal_settings()
    return dict(
        portal_settings=s,
        active_courses=get_active_courses(),
        active_advertisements=get_active_advertisements(),
        active_notices=get_active_notices(),
        active_sliders=get_active_sliders(),
        maintenance_mode=bool(s.get("maintenance_mode", 0)),
        current_academic_year=s.get("current_academic_year", ""),
        current_user=session.get("admin_user"),
        now=datetime.now(),
    )

# ── Auth Helpers ──────────────────────────────────────────────────────────────
def staff_member_required(f):
    """Mirrors Django's @staff_member_required decorator."""
    @wraps(f)
    def wrapped(*a, **kw):
        u = session.get("admin_user")
        if not u:
            flash("Please log in to access the admin panel.", "warning")
            return redirect(url_for("login"))
        if not (u.get("is_staff") or u.get("is_superuser")):
            flash("Access denied. Staff privileges required.", "danger")
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapped

# ── File Upload Helpers ────────────────────────────────────────────────────────
def _ext(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

def upload_file(file_obj, allowed):
    if file_obj and file_obj.filename:
        if _ext(file_obj.filename) not in allowed:
            flash("Invalid file type.", "danger")
            return None
        fname = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{secure_filename(file_obj.filename)}"
        file_obj.save(os.path.join(UPLOAD_DIR, fname))
        return fname
    return None

# ─────────────────────────────────────────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/admin/login", methods=["GET","POST"])
def login():
    if session.get("admin_user"):
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        user = verify_password(username, password)
        if user:
            session["admin_user"] = {
                "id": user["id"], "username": user["username"],
                "is_superuser": bool(user["is_superuser"]),
                "is_staff": bool(user["is_staff"])
            }
            logger.info(f"Login: {username}")
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("dashboard"))
        error = "Invalid credentials. Please try again."
        logger.warning(f"Failed login: {username}")
    return render_template("master_control/login.html", error=error)


@app.route("/admin/logout")
def logout():
    u = session.get("admin_user",{}).get("username","?")
    session.clear()
    logger.info(f"Logout: {u}")
    flash("Signed out successfully.", "info")
    return redirect(url_for("login"))


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
@app.route("/admin/")
@app.route("/admin/dashboard")
@staff_member_required
def dashboard():
    return render_template("master_control/dashboard.html",
                           stats=get_dashboard_stats(),
                           settings=get_portal_settings())


# ─────────────────────────────────────────────────────────────────────────────
# PORTAL SETTINGS  (Singleton)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/admin/settings", methods=["GET","POST"])
@staff_member_required
def portal_settings_view():
    if request.method == "POST":
        s, e = request.form.get("application_start_date"), request.form.get("application_end_date")
        if s and e and s > e:
            flash("Start date must be before end date.", "danger")
            return redirect(url_for("portal_settings_view"))
        save_portal_settings({
            "portal_name":           request.form.get("portal_name","").strip(),
            "current_academic_year": request.form.get("current_academic_year","").strip(),
            "is_portal_active":      request.form.get("is_portal_active"),
            "maintenance_mode":      request.form.get("maintenance_mode"),
            "application_start_date": s or "",
            "application_end_date":   e or "",
            "contact_email":  request.form.get("contact_email","").strip(),
            "support_phone":  request.form.get("support_phone","").strip(),
        })
        flash("Portal settings saved successfully.", "success")
        return redirect(url_for("portal_settings_view"))
    return render_template("master_control/settings.html", settings=get_portal_settings())


# ─────────────────────────────────────────────────────────────────────────────
# COURSES
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/admin/courses")
@staff_member_required
def courses():
    return render_template("master_control/courses.html",
        courses=get_all_courses(
            search=request.args.get("search",""),
            filter_active=request.args.get("is_active","")),
        search=request.args.get("search",""),
        filter_active=request.args.get("is_active",""))


@app.route("/admin/courses/add", methods=["GET","POST"])
@staff_member_required
def add_course():
    if request.method == "POST":
        save_course({
            "course_name":     request.form.get("course_name","").strip(),
            "department_name": request.form.get("department_name","").strip(),
            "degree_type":     request.form.get("degree_type","").strip(),
            "duration_years":  request.form.get("duration_years",3),
            "total_seats":     request.form.get("total_seats",60),
            "is_active":       request.form.get("is_active"),
            "display_priority":request.form.get("display_priority",0),
        })
        flash("Course created successfully.", "success")
        return redirect(url_for("courses"))
    return render_template("master_control/course_form.html", course=None, action="Add")


@app.route("/admin/courses/edit/<int:cid>", methods=["GET","POST"])
@staff_member_required
def edit_course(cid):
    c = get_course(cid)
    if not c: flash("Course not found.", "danger"); return redirect(url_for("courses"))
    if request.method == "POST":
        save_course({
            "course_name":     request.form.get("course_name","").strip(),
            "department_name": request.form.get("department_name","").strip(),
            "degree_type":     request.form.get("degree_type","").strip(),
            "duration_years":  request.form.get("duration_years",3),
            "total_seats":     request.form.get("total_seats",60),
            "is_active":       request.form.get("is_active"),
            "display_priority":request.form.get("display_priority",0),
        }, cid)
        flash("Course updated successfully.", "success")
        return redirect(url_for("courses"))
    return render_template("master_control/course_form.html", course=c, action="Edit")


@app.route("/admin/courses/delete/<int:cid>", methods=["POST"])
@staff_member_required
def delete_course_view(cid):
    delete_course(cid); flash("Course deleted.", "info")
    return redirect(url_for("courses"))


@app.route("/admin/courses/bulk", methods=["POST"])
@staff_member_required
def bulk_courses():
    ids = [int(i) for i in request.form.getlist("ids")]
    act = request.form.get("action")
    if ids and act in ("activate","deactivate"):
        bulk_toggle_courses(ids, act=="activate")
        flash(f"{len(ids)} course(s) {'activated' if act=='activate' else 'deactivated'}.", "success")
    return redirect(url_for("courses"))


# ─────────────────────────────────────────────────────────────────────────────
# FORM CONFIGURATIONS
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/admin/form-configs")
@staff_member_required
def form_configs():
    return render_template("master_control/form_configs.html",
                           configs=get_all_form_configs(),
                           all_courses=get_all_courses())


@app.route("/admin/form-configs/add", methods=["GET","POST"])
@staff_member_required
def add_form_config():
    if request.method == "POST":
        s,e = request.form.get("form_start_date"), request.form.get("form_end_date")
        if s and e and s > e:
            flash("Start date must be before end date.", "danger")
            return redirect(url_for("add_form_config"))
        save_form_config({
            "course_id":               request.form.get("course_id"),
            "is_form_open":            request.form.get("is_form_open"),
            "is_payment_required":     request.form.get("is_payment_required"),
            "application_fee":         request.form.get("application_fee",0),
            "max_applications_allowed":request.form.get("max_applications_allowed",100),
            "form_start_date":         s or "",
            "form_end_date":           e or "",
        })
        flash("Form configuration created.", "success")
        return redirect(url_for("form_configs"))
    return render_template("master_control/form_config_form.html",
                           config=None, courses=get_all_courses(), action="Add")


@app.route("/admin/form-configs/edit/<int:fid>", methods=["GET","POST"])
@staff_member_required
def edit_form_config(fid):
    fc = get_form_config(fid)
    if not fc: flash("Not found.", "danger"); return redirect(url_for("form_configs"))
    if request.method == "POST":
        s,e = request.form.get("form_start_date"), request.form.get("form_end_date")
        if s and e and s > e:
            flash("Start date must be before end date.", "danger")
            return redirect(url_for("edit_form_config", fid=fid))
        save_form_config({
            "course_id":               request.form.get("course_id"),
            "is_form_open":            request.form.get("is_form_open"),
            "is_payment_required":     request.form.get("is_payment_required"),
            "application_fee":         request.form.get("application_fee",0),
            "max_applications_allowed":request.form.get("max_applications_allowed",100),
            "form_start_date":         s or "",
            "form_end_date":           e or "",
        }, fid)
        flash("Form configuration updated.", "success")
        return redirect(url_for("form_configs"))
    return render_template("master_control/form_config_form.html",
                           config=fc, courses=get_all_courses(), action="Edit")


@app.route("/admin/form-configs/delete/<int:fid>", methods=["POST"])
@staff_member_required
def delete_form_config_view(fid):
    delete_form_config(fid); flash("Configuration deleted.", "info")
    return redirect(url_for("form_configs"))


# ─────────────────────────────────────────────────────────────────────────────
# ADVERTISEMENTS
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/admin/advertisements")
@staff_member_required
def advertisements():
    return render_template("master_control/advertisements.html",
        ads=get_all_advertisements(
            search=request.args.get("search",""),
            filter_active=request.args.get("is_active",""),
            filter_type=request.args.get("display_type","")),
        search=request.args.get("search",""),
        filter_active=request.args.get("is_active",""),
        filter_type=request.args.get("display_type",""))


@app.route("/admin/advertisements/add", methods=["GET","POST"])
@staff_member_required
def add_advertisement():
    if request.method == "POST":
        s,e = request.form.get("start_date"), request.form.get("end_date")
        if s and e and s > e:
            flash("Start date must be before end date.", "danger")
            return redirect(url_for("add_advertisement"))
        img = upload_file(request.files.get("image"), ALLOWED_IMG)
        save_advertisement({
            "title":        request.form.get("title","").strip(),
            "description":  request.form.get("description","").strip(),
            "image":        img or "",
            "redirect_url": request.form.get("redirect_url","").strip(),
            "display_type": request.form.get("display_type","banner"),
            "priority":     request.form.get("priority",0),
            "start_date":   s, "end_date": e,
            "is_active":    request.form.get("is_active"),
        })
        flash("Advertisement created.", "success")
        return redirect(url_for("advertisements"))
    return render_template("master_control/advertisement_form.html", ad=None, action="Add")


@app.route("/admin/advertisements/edit/<int:aid>", methods=["GET","POST"])
@staff_member_required
def edit_advertisement(aid):
    ad = get_advertisement(aid)
    if not ad: flash("Not found.", "danger"); return redirect(url_for("advertisements"))
    if request.method == "POST":
        s,e = request.form.get("start_date"), request.form.get("end_date")
        if s and e and s > e:
            flash("Start date must be before end date.", "danger")
            return redirect(url_for("edit_advertisement", aid=aid))
        img = upload_file(request.files.get("image"), ALLOWED_IMG) or ad.get("image","")
        save_advertisement({
            "title":        request.form.get("title","").strip(),
            "description":  request.form.get("description","").strip(),
            "image":        img,
            "redirect_url": request.form.get("redirect_url","").strip(),
            "display_type": request.form.get("display_type","banner"),
            "priority":     request.form.get("priority",0),
            "start_date":   s, "end_date": e,
            "is_active":    request.form.get("is_active"),
        }, aid)
        flash("Advertisement updated.", "success")
        return redirect(url_for("advertisements"))
    return render_template("master_control/advertisement_form.html", ad=ad, action="Edit")


@app.route("/admin/advertisements/delete/<int:aid>", methods=["POST"])
@staff_member_required
def delete_advertisement_view(aid):
    delete_advertisement(aid); flash("Advertisement deleted.", "info")
    return redirect(url_for("advertisements"))


@app.route("/admin/advertisements/bulk", methods=["POST"])
@staff_member_required
def bulk_advertisements():
    ids = [int(i) for i in request.form.getlist("ids")]
    act = request.form.get("action")
    if ids and act in ("activate","deactivate"):
        bulk_toggle_advertisements(ids, act=="activate")
        flash(f"{len(ids)} advertisement(s) updated.", "success")
    return redirect(url_for("advertisements"))


# ─────────────────────────────────────────────────────────────────────────────
# NOTICES
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/admin/notices")
@staff_member_required
def notices():
    return render_template("master_control/notices.html",
        notices=get_all_notices(
            search=request.args.get("search",""),
            filter_active=request.args.get("is_active","")),
        search=request.args.get("search",""),
        filter_active=request.args.get("is_active",""))


@app.route("/admin/notices/add", methods=["GET","POST"])
@staff_member_required
def add_notice():
    if request.method == "POST":
        att = upload_file(request.files.get("attachment"), ALLOWED_FILE)
        save_notice({
            "title":      request.form.get("title","").strip(),
            "content":    request.form.get("content","").strip(),
            "attachment": att or "",
            "is_active":  request.form.get("is_active"),
            "priority":   request.form.get("priority",0),
        })
        flash("Notice published.", "success")
        return redirect(url_for("notices"))
    return render_template("master_control/notice_form.html", notice=None, action="Add")


@app.route("/admin/notices/edit/<int:nid>", methods=["GET","POST"])
@staff_member_required
def edit_notice(nid):
    n = get_notice(nid)
    if not n: flash("Not found.", "danger"); return redirect(url_for("notices"))
    if request.method == "POST":
        att = upload_file(request.files.get("attachment"), ALLOWED_FILE) or n.get("attachment","")
        save_notice({
            "title":      request.form.get("title","").strip(),
            "content":    request.form.get("content","").strip(),
            "attachment": att,
            "is_active":  request.form.get("is_active"),
            "priority":   request.form.get("priority",0),
        }, nid)
        flash("Notice updated.", "success")
        return redirect(url_for("notices"))
    return render_template("master_control/notice_form.html", notice=n, action="Edit")


@app.route("/admin/notices/delete/<int:nid>", methods=["POST"])
@staff_member_required
def delete_notice_view(nid):
    delete_notice(nid); flash("Notice deleted.", "info")
    return redirect(url_for("notices"))


@app.route("/admin/notices/bulk", methods=["POST"])
@staff_member_required
def bulk_notices():
    ids = [int(i) for i in request.form.getlist("ids")]
    act = request.form.get("action")
    if ids and act in ("activate","deactivate"):
        bulk_toggle_notices(ids, act=="activate")
        flash(f"{len(ids)} notice(s) updated.", "success")
    return redirect(url_for("notices"))


# ─────────────────────────────────────────────────────────────────────────────
# HOMEPAGE SLIDERS
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/admin/sliders")
@staff_member_required
def sliders():
    return render_template("master_control/sliders.html", sliders=get_all_sliders())


@app.route("/admin/sliders/add", methods=["GET","POST"])
@staff_member_required
def add_slider():
    if request.method == "POST":
        img = upload_file(request.files.get("image"), ALLOWED_IMG)
        save_slider({
            "title":    request.form.get("title","").strip(),
            "subtitle": request.form.get("subtitle","").strip(),
            "image":    img or "",
            "priority": request.form.get("priority",0),
            "is_active":request.form.get("is_active"),
        })
        flash("Slider created.", "success")
        return redirect(url_for("sliders"))
    return render_template("master_control/slider_form.html", slider=None, action="Add")


@app.route("/admin/sliders/edit/<int:sid>", methods=["GET","POST"])
@staff_member_required
def edit_slider(sid):
    sl = get_slider(sid)
    if not sl: flash("Not found.", "danger"); return redirect(url_for("sliders"))
    if request.method == "POST":
        img = upload_file(request.files.get("image"), ALLOWED_IMG) or sl.get("image","")
        save_slider({
            "title":    request.form.get("title","").strip(),
            "subtitle": request.form.get("subtitle","").strip(),
            "image":    img,
            "priority": request.form.get("priority",0),
            "is_active":request.form.get("is_active"),
        }, sid)
        flash("Slider updated.", "success")
        return redirect(url_for("sliders"))
    return render_template("master_control/slider_form.html", slider=sl, action="Edit")


@app.route("/admin/sliders/delete/<int:sid>", methods=["POST"])
@staff_member_required
def delete_slider_view(sid):
    delete_slider(sid); flash("Slider deleted.", "info")
    return redirect(url_for("sliders"))


@app.route("/admin/sliders/bulk", methods=["POST"])
@staff_member_required
def bulk_sliders():
    ids = [int(i) for i in request.form.getlist("ids")]
    act = request.form.get("action")
    if ids and act in ("activate","deactivate"):
        bulk_toggle_sliders(ids, act=="activate")
        flash(f"{len(ids)} slider(s) updated.", "success")
    return redirect(url_for("sliders"))


# ─────────────────────────────────────────────────────────────────────────────
# UPLOADS
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ─────────────────────────────────────────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("master_control/error.html", code=404,
                           message="Page Not Found",
                           detail="The page you requested does not exist."), 404

@app.errorhandler(413)
def too_large(e):
    flash("File is too large. Maximum size is 5 MB.", "danger")
    return redirect(request.referrer or url_for("dashboard"))


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not get_admin_user("admin"):
        create_superuser("admin", "admin123", "admin@university.edu")
        print("Default admin created  →  username: admin  |  password: admin123")
    app.run(debug=False, host="0.0.0.0", port=5000)
