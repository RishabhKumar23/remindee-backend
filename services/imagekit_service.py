from imagekitio import ImageKit

from config import IMAGEKIT_PRIVATE_KEY, IMAGEKIT_PUBLIC_KEY, IMAGEKIT_URL_ENDPOINT

imagekit = ImageKit(private_key=IMAGEKIT_PRIVATE_KEY)

##ANCHOR - Upload Service
def upload_file(file_bytes: bytes, file_name: str, folder: str, content_type: str = "image/png") -> str:
    """Uploads a file to ImageKit and returns the URL of the uploaded/CDN file."""

    # Upload from file
    response = imagekit.files.upload(
        file=(file_bytes, file_name, content_type),
        file_name=file_name,
        folder=folder,
        is_private_file=False,
        use_unique_file_name=True,
    )
    return response.url

##ANCHOR - Images Variants
def get_variants(base_url: str) -> dict:
    """Returns 3 sizes variant URL using imagekit transformation"""
    variants = {
        "Image": f"{base_url}?tr=w-1280,h-720, c-maintain_ration, fo-auto",
        "shots": f"{base_url}?tr=w-1080,h-1920, c-maintain_ration, fo-auto",
        "avatar": f"{base_url}?tr=w-256,h-256,fo-face:r-max"
    }
    return variants