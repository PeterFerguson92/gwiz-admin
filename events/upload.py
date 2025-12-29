import uuid


def event_cover_upload_image_path(instance, filename):
    """
    Upload path for event cover images.
    Groups uploads by event id (UUID) to keep S3 organized.
    """
    event_id = instance.id or uuid.uuid4()
    return f"events/{event_id}/cover/{filename}"
