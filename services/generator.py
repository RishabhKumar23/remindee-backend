import asyncio
import logging

from sqlmodel import Session, select
from database import engine
from models import Job, Image
from services.openai_service import generate_images
from services.imagekit_service import upload_file

logger = logging.getLogger(__name__)

#ANCHOR - Prompts
STYLES = {
    "realistic": (
        "photo-realistic, ultra-detailed, shot on DSLR camera, natural lighting, "
        "8K resolution, hyperrealistic, sharp focus, cinematic composition, "
        "true-to-life colors, lifelike textures, photographic quality"
    ),
    "anime": (
        "anime style, Studio Ghibli inspired, vibrant cel-shading, clean line art, "
        "expressive character design, soft pastel color palette, hand-drawn look, "
        "2D illustrated, manga aesthetic, detailed anime background"
    ),
    "pixel_art": (
        "pixel art style, 16-bit retro aesthetic, crisp pixels, limited color palette, "
        "sprite art, pixelated details, retro video game art style, "
        "low resolution charm, dithering effects, classic arcade look"
    ),
    "cartoon": (
        "cartoon style, bold outlines, flat vivid colors, exaggerated proportions, "
        "playful and expressive, smooth cel-shaded look, western animation style, "
        "clean vector-like illustration, fun and whimsical, comic book aesthetic"
    ),
}

#ANCHOR - Style Order
STYLE_ORDER = ["realistic", "anime", "pixel_art", "cartoon"]

async def generate_single_image(image_id: str, prompt: str, headshot_url: str):
    # DB call to mark generating
    with Session(engine) as session:
        image = session.get(Image, image_id)
        image.status = "generating"
        style_name = image.style_name
        session.add(image)
        session.commit()
    style_prompt = STYLES[style_name]
    # Ai call to generate image
    try:
        image_byte = generate_images(prompt, style_prompt, headshot_url)
        #NOTE - To store image
        with Session(engine) as session:
            image = session.get(Image, image_id)
            job_id = image.job_id
            job = session.get(Job, job_id)
        #NOTE - upload image to image_kit
        url = upload_file(
                image_byte,
                file_name=f"{job_id}_{image_id}.png",
                folder_path=f"images/{job_id}/"
            )
        #NOTE - Db call to save the url and mark as uploaded
        with Session(engine) as session:
            image = session.get(Image, image_id)
            image.imagekit_url = url
            image.status = "uploaded"
            session.add(image)
            session.commit()
        logger.info(f"Successfully generated and uploaded image {image_id} for job {job_id}")

    except Exception as e:
        logger.error(f"Error generating image {image_id}: {e}")
        with Session(engine) as session:
            image = session.get(Image, image_id)
            image.status = "error"
            image.error_message = str(e)[:500]  # Truncate error message to fit in DB
            session.add(image)
            session.commit()

#ANCHOR - Process Job
async def process_job(job_id: str):
    with Session(engine) as session:
        job = session.get(Job, job_id)
        #NOTE - mark job as processing
        job.status = "processing"
        prompt = job.prompt
        headshot_url = job.headshot_url
        session.add(job)
        session.commit()

        #NOTE - find all images for the job
        images = session.exec(
            select(Image).where(Image.job_id == job_id)
        ).all()

        images_ids = [i.id for i in images]

        #NOTE - start one worker for each image
        tasks = [
            generate_single_image(image_id=iid, prompt=prompt, headshot_url=headshot_url)
            for iid in images_ids
        ]

        #NOTE - wait for all workers to finish
        await asyncio.gather(*tasks, return_exceptions=True)

        #NOTE - mark job as completed/error
        with Session(engine) as session:
            images = session.exec(
                select(Image).where(Image.job_id == job_id)
            ).all()
            all_failed = all(i.status == "failed" for i in images)
            job = session.get(Job, job_id)
            job.status = "failed" if all_failed else "completed"
            session.add(job)
            session.commit()