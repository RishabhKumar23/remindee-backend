from openai import AsyncOpenAI
import base64

from config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# generate images
async def generate_images(prompt: str, self_prompt: str, headshot_url: str) -> bytes:
    """
    Use the response API with gpt-image-2 as a built-in image_generation tool.
    Pass the headshot URL directly as an input_image
    returns raw png bytes
    """
    full_prompt = (
        f"{self_prompt}\n\n"
        f"User request: {prompt}\n\n"
        "IMPORTANT: The generated images MUST prominently feature the person"
        "Shown in the provided headshot photo, keep their likness and accurate."
    )

    response = client.responses.create(
        mode="gpt-4o",
        input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_image", "url": headshot_url},
                        {"type": "text", "text": full_prompt}
                    ]
                }
            ],
        tools=[
                {
                    "type": "image_generation",
                    "model": "gpt-image-2",
                    "size": "1024x1024",
                    "quality": "standard",
                    "output_format": "png",
                },
            ]
    )

    for item in response.output:
        if item.type == "image_generation_call" and item.result:
            return base64.b64decode(item.result)

    raise RuntimeError("No image generation result found in the response.")
