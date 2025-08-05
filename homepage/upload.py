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
