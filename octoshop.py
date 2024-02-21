import streamlit as st
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

def octoshop(my_upload, meta_prompt, style):
    # Wrap all of this in a try block
    try:
        start = time.time()

        # UI columps
        colI, colO = st.columns(2)

        # Rotate image and perform some rescaling
        input_img = Image.open(my_upload)
        input_img = rotate_image(input_img)
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

        # Number of images generated
        num_imgs = 4
        octoshop_futures = {}
        for idx in range(num_imgs):
            # Query endpoint async
            octoshop_futures[idx] = oai_client.infer_async(
                f"{OCTOSHOP_ENDPOINT_URL}/generate",
                {
                    "prompt": meta_prompt,
                    "batch": 1,
                    "strength": 0.33,
                    "steps": 20,
                    "sampler": "K_EULER_ANCESTRAL",
                    "image": read_image(input_img),
                    "faceswap": True,
                    "style": style,
                    "octoai": False
                }
            )

        # Poll on completion - target 30s completion - hence the 0.25 time step
        finished_jobs = {}
        time_step = 0.25
        while len(finished_jobs) < num_imgs:
            time.sleep(time_step)
            percent_complete = min(99, percent_complete+1)
            if percent_complete == 99:
                progress_text = "OctoShopping is taking longer than usual, hang tight!"
            progress_bar.progress(percent_complete, text=progress_text)
            # Update completed jobs
            for idx, future in octoshop_futures.items():
                if idx not in finished_jobs:
                    if oai_client.is_future_ready(future):
                        finished_jobs[idx] = "done"

        # Process results
        end = time.time()
        progress_bar.empty()
        colO.write("OctoShopped images in {:.2f}s :star2:".format(end-start))
        colO_0, colO_1 = colO.columns(2)
        for idx in range(num_imgs):
            results = oai_client.get_future_result(octoshop_futures[idx])
            octoshopped_image = Image.open(BytesIO(b64decode(results["images"][0])))
            if idx == 0:
                colI.text_area("", value=results["clip"])
            if idx % 2 == 0:
                colO_0.image(octoshopped_image)
                colO_0.text_area("", value=results["story"])
            elif idx % 2 == 1:
                colO_1.image(octoshopped_image)
                colO_1.text_area("", value=results["story"])

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

st.write("## :tada: OctoShop Internal Version (OctoML Only)")
st.write("\n\n")
st.write("### :camera: Transform photos with words!")
st.write(
    "### This is an internal version for OctoML employees only. Do not redistribute outside of OctoML."
)
st.markdown(
    "Alpha mode: I don't handle pictures with people great! **I may accidentally flip people's gender and ethnicities!** Be patient and try different ways to get to the result you want! Sometimes it takes a few tries to get it right! And don't hesitate to submit feedback/issues via the form so I can get better over time!"
)

st.sidebar.image("assets/octoai_electric_blue.png")
my_upload = st.sidebar.file_uploader("Upload a photo", type=["png", "jpg", "jpeg"])
style = st.selectbox(
    'Style',
    (
        'base',
        'photographic',
        '3d-model',
        'analog-film',
        'anime',
        'cinematic',
        'comic-book',
        'Craft Clay',
        'digital-art',
        'enhance',
        'fantasy-art',
        'isometric',
        'line-art',
        'enhance',
        'low-poly',
        'modeling-compound',
        'neon-punk',
        'origami',
        'photographic',
        'pixel-art',
        'texture',
        'tile-texture'
    ), index=1)

st.sidebar.markdown(
    ":thumbsup: :thumbsdown: Give us your [feedback](https://forms.gle/7sfoQDjXt2SNjmp86) to help us improve OctoShop! Or join our discord [here](https://discord.com/invite/rXTPeRBcG7) and hop on to the #octoshop channel to provide feedback or ask questions."
)
st.sidebar.markdown(
    ":bug: Report bugs, issues, or problematic content [here](https://forms.gle/vWVAXa8CU7wXPGcq6)!"
)
st.sidebar.markdown(
    ":warning: **Disclaimer** OctoShop is built on the foundation of CLIP Interrogator, SDXL, LLAMA2, and is therefore likely to carry forward the potential dangers inherent in these base models."
)

meta_prompt = st.text_input("OctoShop prompt", value="Set in 60s San Francisco")

if my_upload is not None:
    if st.button('OctoShop!'):
        octoshop(my_upload, meta_prompt, style)
