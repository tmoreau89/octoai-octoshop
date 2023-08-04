import streamlit as st
# from octoai.client import Client
from io import BytesIO
from base64 import b64encode, b64decode
import requests
from PIL import Image, ExifTags
import os
import time

OCTOSHOP_ENDPOINT_URL = os.environ["OCTOSHOP_ENDPOINT_URL"]
OCTOAI_TOKEN = os.environ["OCTOAI_TOKEN"]


def get_request(url):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {OCTOAI_TOKEN}",
    }
    response = requests.get(url=url, headers=headers)
    response.raise_for_status()
    return response.json()

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

def travel_back(my_upload, meta_prompt):
    colI, colO = st.columns(2)

    # Rotate image and perform some rescaling
    input_img = Image.open(my_upload)
    input_img = rotate_image(input_img)
    input_img = rescale_image(input_img)
    colI.write("Input image")
    colI.image(input_img)
    progress_text = "OctoShopping in action..."
    percent_complete = 0
    progress_bar = colO.progress(percent_complete, text=progress_text)

    response = query_octoshop({
        "prompt": meta_prompt,
        "strength": 0.80,
        "steps": 20,
        "image": read_image(input_img),
        "faceswap": True
    })

    status = get_request(response["poll_url"])
    time_step = 0.1
    time_slept = 0
    while status["status"] == "pending":
        time.sleep(time_step)
        time_slept += time_step
        # print("Time Slept = {}, status = {}".format(time_slept, status))
        status = get_request(response["poll_url"])
        percent_complete = min(99, percent_complete+1)
        progress_bar.progress(percent_complete, text=progress_text)
    progress_bar.progress(100, text="Ready!")

    if status["status"] == "completed":
        results = get_request(status["response_url"])
        image_str = results["image"]
        octoshopped_image = Image.open(BytesIO(b64decode(image_str)))
        progress_bar.empty()
        colO.write("OctoShopped image :star2:")
        # Add watermark - TODO - increase robustness
        watermark = "assets/octoml-octopus-white.png" # watermark image
        imgS = octoshopped_image.convert("RGBA")
        imgW = Image.open(watermark)
        imgW = imgW.resize((200, 200)) # change the numbers to adjust the size
        imgS.paste(imgW, (0,0), imgW.convert("RGBA"))
        # Display final image
        colO.image(imgS)
    else:
        colO.write("Oops, something went wrong... OctoShop is in alpha preview, thank you for being patient!")

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

st.write("## :tada: OctoShop Preview")

st.write("### :camera: Transform photos with the power of words and generative AI!")

st.sidebar.image("octoml-octo-ai-logo-color.png")

my_upload = st.sidebar.file_uploader("Upload a photo", type=["png", "jpg", "jpeg"])

st.sidebar.markdown(
    "**Disclaimer** OctoShop is built on the foundation of CLIP Interrogator, SDXL, LLAMA2, and is therefore likely to carry forward the potential dangers inherent in these base models."
)

st.markdown(
    "*Alpha mode engaged*: I can't handle photos with multiple subjects right now! I can handle at most one person in the frame! If you didn't get good results, try again!"
)

meta_prompt = st.text_input("OctoShop prompt", value="Set the scene in 80s Tokyo")

if my_upload is not None:
    if st.button('OctoShop!'):
        travel_back(my_upload, meta_prompt)
