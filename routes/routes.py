from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select
import os
import logging
import asyncio
import json

#ANCHOR - Internal
from database import get_session
from models import Job, Image
from services.generator import process_job, STYLE_ORDER
from services.imagekit_service import get_variants, upload_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# request response schemas

class CreateJobRequest(BaseModel):
    prompt: str
    nums_images: int
    headshot: UploadFile

class CreateJobResponse(BaseModel):
    job_id: str

class ImageResponse(BaseModel):
    image_id: str
    style_name: str
    status: str
    imagekit_url: str | None = None
    error_message: str | None = None
    variant: dict | None = None

class JobResponse(BaseModel):
    job_id: int
    prompt: str
    headshot_url: str
    num_Images: int
    status: str
    images: list[ImageResponse]

@router.post("/upload-headshot")
async def upload_headshot(file: UploadFile = File(...)):
    contents = await file.read()  # Read the file to ensure it's fully uploaded
    url = upload_file(
        file_bytes=contents,
        file_name=file.filename or "headshot.png",
        folder="headshots",
        content_type=file.content_type or "image/png"
    )

    return {"url": url}

@router.post("/jobs", response_model=CreateJobResponse)
async def create_job(request: CreateJobRequest, session: Session = Depends(get_session)):
    if request.nums_images < 1 or request.nums_images > len(STYLE_ORDER):
        raise HTTPException(status_code=400, detail=f"nums_images must be between 1 and {len(STYLE_ORDER)}")

    job = Job(
        prompt=request.prompt,
        headshot_url=request.headshot.filename,
        num_Images=request.nums_images,
    )
    session.add(job)

    styles = STYLE_ORDER[:request.nums_images]
    for style in styles:
        image = Image(
            job_id=job.id,
            style_name=style,
        )
        session.add(image)

    session.commit()

    #NOTE - Fire and forgot style - based image generation
    asyncio.create_task(process_job(job.id))
    return CreateJobResponse(job_id=job.id)

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    images = session.exec(
        select(Image).where(Image.job_id == job_id)
    ).all()

    image_responses = []
    for image in images:
        variants = get_variants(image.imagekit_url) if image.imagekit_url else None

        image_responses.append(
            ImageResponse(
                image_id=image.id,
                style_name=image.style_name,
                status=image.status,
                imagekit_url=image.imagekit_url,
                error_message=image.error_message,
                variant=variants
            )
        )
    return JobResponse(
        job_id=job.id,
        prompt=job.prompt,
        headshot_url=job.headshot_url,
        num_Images=job.num_Images,
        status=job.status,
        images=image_responses
    )

#NOTE - SSE (server-sent events) endpoint to stream updates about job status and images as they are generated and uploaded
@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str):
    async def event_generator():
        from database import engine
        sent_images = set()
        while True:
            with Session(engine) as session:
                job = session.get(Job, job_id)
                if not job:
                    yield f"event: error\ndata: {json.dumps({'detail': 'Job not found'})}\n\n"
                    return
                images = session.exec(
                    select(Image).where(Image.job_id == job_id)
                ).all()

                for i in images:
                    if i.id in sent_images:
                        continue
                    if i.status in "uploaded":
                        variants = get_variants(i.imagekit_url)
                        data = json.dumps({
                            "image_id": i.id,
                            "style_name": i.style_name,
                            "imagekit_url": i.imagekit_url,
                            "variant": variants
                        })
                        yield f"event: image_uploaded\ndata: {data}\n\n"
                        sent_images.add(i.id)
                    elif i.status == "failed":
                        data = json.dumps({
                            "image_id": i.id,
                            "style_name": i.style_name,
                            "error_message": i.error_message
                        })
                        yield f"event: image_failed\ndata: {data}\n\n"
                        sent_images.add(i.id)
                all_done = all(i.status in ["uploaded", "failed"] for i in images)
                if all_done and len(sent_images) == len(images):
                    data = json.dumps({
                        "job_id": job_id,
                        "status": job.status
                    })
                    yield f"event: job completed\ndata: {data}\n\n"
                    return
            await asyncio.sleep(2)  # Poll every 2 seconds

    return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

