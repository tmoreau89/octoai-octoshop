import streamlit as st
from streamlit_image_select import image_select
from octoai.client import Client
from octoai.errors import OctoAIClientError, OctoAIServerError
from io import BytesIO
from base64 import b64encode, b64decode
import requests
from PIL import Image, ExifTags
import os
import time

OCTOSHOP_ENDPOINT_URL = os.environ["OCTOSHOP_ENDPOINT_URL"]
OCTOAI_TOKEN = os.environ["OCTOAI_TOKEN"]

# OctoAI client
oai_client = Client(OCTOAI_TOKEN)

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


def octoshop(my_upload, meta_prompt):
    # Wrap all of this in a try block
    try:
        start = time.time()

        # UI columps
        colI, colO = st.columns(2)

        # Rotate image and perform some rescaling
        input_img = rotate_image(my_upload)
        input_img = rescale_image(input_img)
        colI.write("Input image")
        colI.image(input_img)
        progress_text = "OctoShopping in action..."
        percent_complete = 0
        progress_bar = colO.progress(percent_complete, text=progress_text)

        # Look for easter egg "octoshirt"
        octoai = False
        if "octoshirt" in meta_prompt:
            print(meta_prompt.replace('octoshirt', ''))
            octoai = True
            print("OctoShirt Mode Engaged!")

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
                "style": "base",
                "faceswap": True,
                "octoai": octoai
            }
        )

        # Poll on completion - target 30s completion - hence the 0.25 time step
        time_step = 0.25
        while not oai_client.is_future_ready(future):
            time.sleep(time_step)
            percent_complete = min(99, percent_complete+1)
            if percent_complete == 99:
                progress_text = "OctoShopping is taking longer than usual, hang tight!"
            progress_bar.progress(percent_complete, text=progress_text)

        # Process results
        end = time.time()
        progress_bar.empty()
        colO.write("OctoShopped images in {:.2f}s :star2:".format(end-start))
        results = oai_client.get_future_result(future)
        for _, im_str in enumerate(results["images"]):
            octoshopped_image = Image.open(BytesIO(b64decode(im_str)))
            colO.image(octoshopped_image)

    except OctoAIClientError as e:
        progress_bar.empty()
        colO.write("Oops something went wrong (client error)! Please hit OctoShop again or [report the issue if this is a recurring problem](https://forms.gle/vWVAXa8CU7wXPGcq6)! Join our discord [here](https://discord.com/invite/rXTPeRBcG7) and hop on to the #octoshop channel to provide feedback or ask questions.")

    except OctoAIServerError as e:
        progress_bar.empty()
        colO.write("Oops something went wrong (server error)! Please hit OctoShop again or [report the issue if this is a recurring problem](https://forms.gle/vWVAXa8CU7wXPGcq6)! Join our discord [here](https://discord.com/invite/rXTPeRBcG7) and hop on to the #octoshop channel to provide feedback or ask questions.")

    except Exception as e:
        progress_bar.empty()
        colO.write("Oops something went wrong (unexpected error)! Please hit OctoShop again or [report the issue if this is a recurring problem](https://forms.gle/vWVAXa8CU7wXPGcq6)! Join our discord [here](https://discord.com/invite/rXTPeRBcG7) and hop on to the #octoshop channel to provide feedback or ask questions.")



st.set_page_config(layout="wide", page_title="OctoShop")

st.write("## :tada: OctoShop Alpha Preview")
# st.write("### We're undergoing maintenance for the next few minutes!")
st.write("\n\n")
st.write("### :camera: Transform photos with words!")
st.markdown(
    "OctoShop is powered by OctoAI compute services. Try OctoAI and start building with powerful, easy-to-use generative models like Stable Diffusion XL, LLaMa2, and more. [Sign up today and receive 25 free GPU hours.](https://octoml.ai/?utm_source=octoshop&utm_medium=referral&utm_campaign=sdxl)"
)

st.sidebar.image("assets/octoai_electric_blue.png")
st.sidebar.markdown(
    ":thumbsup: :thumbsdown: Give us your [feedback](https://forms.gle/7sfoQDjXt2SNjmp86) to help us improve OctoShop! Or join our discord [here](https://discord.com/invite/rXTPeRBcG7) and hop on to the #octoshop channel to provide feedback or ask questions."
)
st.sidebar.markdown(
    ":bug: Report bugs, issues, or problematic content [here](https://forms.gle/vWVAXa8CU7wXPGcq6)!"
)
st.sidebar.markdown(
    ":warning: **Disclaimer** OctoShop is built on the foundation of CLIP Interrogator, SDXL, LLAMA2, and is therefore likely to carry forward the potential dangers inherent in these base models."
)

input_image = image_select(
    label="Select a photo",
    images=[
        Image.open("assets/monalisa.jpg"),
        Image.open("assets/business_person.png"),
        Image.open("assets/cat.jpg"),
        Image.open("assets/baby_penguin.jpeg"),
        Image.open("assets/modern_car.jpeg"),
        Image.open("assets/mall.jpg"),
        Image.open("assets/office.jpg"),
    ],
    captions=["Mona Lisa", "Person", "Cat", "Penguin", "Car", "Mall", "Office"],
    use_container_width=False
)

meta_prompt = st.text_input("OctoShop prompt", value="Set the photograph in 60s San Francisco")

if st.button('OctoShop!'):
    octoshop(input_image, meta_prompt)
