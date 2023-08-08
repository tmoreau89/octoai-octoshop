import streamlit as st
from octoai.client import Client
from io import BytesIO
from base64 import b64encode, b64decode
import requests
from PIL import Image, ExifTags
import os
import time

OCTOSHOP_ENDPOINT_URL = os.environ["OCTOSHOP_ENDPOINT_URL"]
OCTOAI_TOKEN = os.environ["OCTOAI_TOKEN"]


def read_image(image):
    buffer = BytesIO()
    image.save(buffer, format="png")
    im_base64 = b64encode(buffer.getvalue()).decode("utf-8")
    return im_base64

def rotate_image(image):
    try:
        # Rotate based on Exif Data
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                break
        exif = image._getexif()
        if exif[orientation] == 3:
            image=image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image=image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image=image.rotate(90, expand=True)
        return image
    except:
        return image

def rescale_image(image):
    w, h = image.size
    if w == h:
        width = 1024
        height = 1024
    elif w > h:
        width = 1024
        height = 1024 * h // w
    else:
        width = 1024 * w // h
        height = 1024
    image = image.resize((width, height))
    return image

def query_octoshop(payload):
     # Send to SDXL endpoint - async request
    headers = {
        "Content-type": "application/json",
        "X-OctoAI-Async": "1",
        "Authorization": f"Bearer {OCTOAI_TOKEN}",
    }
    url = f"{OCTOSHOP_ENDPOINT_URL}/generate"
    # Send image for generation with roop
    response = requests.post(url=url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def octoshop(my_upload, meta_prompt):
    # UI columps
    colI, colO = st.columns(2)

    # OctoAI client
    oai_client = Client(OCTOAI_TOKEN)

    # Rotate image and perform some rescaling
    input_img = Image.open(my_upload)
    input_img = rotate_image(input_img)
    input_img = rescale_image(input_img)
    colI.write("Input image")
    colI.image(input_img)
    progress_text = "OctoShopping in action..."
    percent_complete = 0
    progress_bar = colO.progress(percent_complete, text=progress_text)

    # Query endpoint async
    future = oai_client.infer_async(
        f"{OCTOSHOP_ENDPOINT_URL}/generate",
        {
            "prompt": meta_prompt,
            "batch": 1,
            "strength": 0.75,
            "steps": 20,
            "sampler": "DPM++ 2M SDE Karras",
            "image": read_image(input_img),
            "faceswap": False
        }
    )
    # Poll on completion
    time_step = 0.2
    while not oai_client.is_future_ready(future):
        time.sleep(time_step)
        percent_complete = min(99, percent_complete+1)
        if percent_complete == 99:
            progress_text = "OctoShopping is taking longer than usual, hang tight!"
        progress_bar.progress(percent_complete, text=progress_text)
    # Process results
    results = oai_client.get_future_result(future)
    progress_bar.empty()
    colO.write("OctoShopped images :star2:")
    for _, im_str in enumerate(results["images"]):
        octoshopped_image = Image.open(BytesIO(b64decode(im_str)))
        colO.image(octoshopped_image)


st.set_page_config(layout="wide", page_title="OctoShop")

# Powered by OctoML displayed in top right
st.markdown("""
<style>
.powered-by {
    position: absolute;
    top: -10px;
    right: 0;
    float: right;
}
.powered-by span {
    padding-right: 5;
</style>
<div class="powered-by">
<span>Powered by </span> <a href="https://octoai.cloud/"><img src="https://i.ibb.co/T1X1CHG/octoml-octo-ai-logo-vertical-container-white.png" alt="octoml-octo-ai-logo-vertical-container-white" border="0" width="200"></a>
</div>
""", unsafe_allow_html=True)

st.write("## :tada: OctoShop Internal Version (OctoML Only)")
st.write("\n\n")
st.write("### :camera: Transform photos with words!")
st.markdown(
    "OctoShop is powered by OctoAI compute services. Try OctoAI and start building with powerful, easy-to-use generative models like Stable Diffusion XL, LLaMa2, and more. [Sign up today and receive 25 free GPU hours.](https://octoml.ai/?utm_source=octoshop&utm_medium=referral&utm_campaign=sdxl)"
)
st.markdown(
    "*Alpha mode engaged*: I can't handle photos with multiple subjects right now! I can handle at most one person in the frame! If you didn't get good results, try again!"
)

st.sidebar.image("octoml-octo-ai-logo-color.png")
my_upload = st.sidebar.file_uploader("Upload a photo", type=["png", "jpg", "jpeg"])
st.sidebar.markdown(
    "**Disclaimer** OctoShop is built on the foundation of CLIP Interrogator, SDXL, LLAMA2, and is therefore likely to carry forward the potential dangers inherent in these base models."
)

meta_prompt = st.text_input("OctoShop prompt", value="Set the photograph in 60s San Francisco")

if my_upload is not None:
    if st.button('OctoShop!'):
        octoshop(my_upload, meta_prompt)
