import streamlit as st
from io import BytesIO
from base64 import b64encode, b64decode
import requests
from PIL import Image, ExifTags
import os

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
     # Send to SDXL endpoint
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {OCTOAI_TOKEN}",
    }
    url = f"{OCTOSHOP_ENDPOINT_URL}/generate"
    # Send image for generation with roop
    response = requests.post(url=url, json=payload, headers=headers)
    # Turn into image
    image_str = response.json()["image"]
    image = Image.open(BytesIO(b64decode(image_str)))
    return image

def travel_back(my_upload, meta_prompt):
    colI, colO = st.columns(2)

    # Rotate image and perform some rescaling
    input_img = Image.open(my_upload)
    input_img = rotate_image(input_img)
    input_img = rescale_image(input_img)
    colI.write("Input image")
    colI.image(input_img)

    image_response = query_octoshop({
        "prompt": meta_prompt,
        "strength": 0.75,
        "steps": 20,
        "image": read_image(input_img),
        "faceswap": True
    })
    colO.write("Transformed image :star2:")
    colO.image(image_response)

st.set_page_config(layout="wide", page_title="OctoShop")

st.write("## :tada: OctoShop - Powered by OctoAI")

st.write("### :camera: Transform photos with the power of words and generative AI!")

st.markdown(
    "Note: I can't handle photos with multiple subjects. I can handle at most one person in the frame!"
)

my_upload = st.file_uploader("Upload a photo", type=["png", "jpg", "jpeg"])

meta_prompt = st.text_input("Transform the photo", value="Set the photo in 80s Tokyo")

if my_upload is not None:
    if st.button('(re-)OctoShop!'):
        travel_back(my_upload, meta_prompt)
