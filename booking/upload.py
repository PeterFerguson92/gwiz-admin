import os


def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    _, ext = os.path.splitext(base_name)
    return ext


def fitness_class_cover_upload_image_path(instance, filename):
    """
    Store cover images under:
    booking/fitness_classes/<id>/cover.<ext>
    """
    ext = get_filename_ext(filename)
    return f"booking/fitness_classes/{instance.id}/cover{ext}"
