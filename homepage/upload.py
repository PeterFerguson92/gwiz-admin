import os


def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    _, ext = os.path.splitext(base_name)
    return ext


def homepage_logo_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"homepage/banner/{instance.id}/logo{ext}"


def homepage_slide1_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"homepage/banner/{instance.id}/slide1{ext}"


def homepage_slide2_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"homepage/banner/{instance.id}/slide2{ext}"


def homepage_slide3_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"homepage/banner/{instance.id}/slide3{ext}"


# About us uploader.
def about_us_cover_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"homepage/aboutus/cover/{instance.id}/img{ext}"


def about_us_homepage_upload_image1_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"homepage/aboutus/homepage/{instance.id}/img1{ext}"


def about_us_homepage_upload_image2_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"homepage/aboutus/homepage/{instance.id}/img2{ext}"


def about_us_section_upload_image1_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"homepage/aboutus/section{instance.id}/img1{ext}"


def about_us_section_upload_image2_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"homepage/aboutus/section{instance.id}/img2{ext}"


# Trainer/Team.
def team_trainer_profile_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"homepage/team/trainers/profile/{instance.id}/img{ext}"


# Trainer/Team.
def service_cover_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"service/{instance.id}/img{ext}"


# Contact.
def contact_background_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"contact/{instance.id}/img{ext}"


# footer.
def footer_logo_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"footer/{instance.id}/img{ext}"


# assets.
def assets_login_cover_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"assets/{instance.id}/login_cover{ext}"


def assets_personal_area_cover_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"assets/{instance.id}/personal_area_cover{ext}"


def assets_main_events_cover_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"assets/{instance.id}/main_events_cover{ext}"


def assets_main_classes_cover_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"assets/{instance.id}/main_classes_cover{ext}"


def assets_personal_tickets_cover_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"assets/{instance.id}/personal_tickets_cover{ext}"


def assets_personal_bookings_cover_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"assets/{instance.id}/personal_bookings_cover{ext}"


def assets_contact_us_cover_upload_image_path(instance, filename):
    ext = get_filename_ext(filename)
    return f"assets/{instance.id}/contact_us_cover{ext}"
