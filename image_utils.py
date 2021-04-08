import os
import urllib.request
from PIL import Image
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import config


def save_image_from_message(message, telbot):
    cid = message.chat.id
    image_id = get_image_id_from_message(message)

    # prepare image for downloading
    file_path = telbot.get_file(image_id).file_path

    # generate image download url
    image_url = "https://api.telegram.org/file/bot{0}/{1}".format(config.TOKEN, file_path)

    # create folder to store image temporary, if it doesnt exist
    if not os.path.exists(config.result_storage_path):
        os.makedirs(config.result_storage_path)

    # retrieve and save image
    image_name = "{0}.jpg".format(image_id)
    urllib.request.urlretrieve(image_url, "{0}/{1}".format(config.result_storage_path, image_name))

    return image_name


def get_image_id_from_message(message):
    # there are multiple array of images, check the biggest
    return message.photo[len(message.photo) - 1].file_id


def handle_image(image_name, cid):
    if config.dict_styles_established[cid] == 'standard style established':
        style_number = config.dict_styles[cid]
        del config.dict_styles[cid]
        style_image_name = "handled_style{0}.jpg".format(style_number)
        style_image = Image.open("{0}/{1}".format(config.result_storage_path, style_image_name))
    else:
        style_image_name = config.dict_styles_established[cid]
        style_image = Image.open("{0}/{1}".format(config.result_storage_path, style_image_name))
        style_image = image_to_square(style_image, 256)

    style_img = np.array(style_image)
    style_img = style_img.astype(np.float32)[np.newaxis, ...] / 255.

    content_image = Image.open("{0}/{1}".format(config.result_storage_path, image_name))
    image_resized = image_reduce(content_image, 384)
    content_img = np.array(image_resized)
    content_img = content_img.astype(np.float32)[np.newaxis, ...] / 255.

    hub_module = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')

    outputs = hub_module(tf.constant(content_img), tf.constant(style_img))
    stylized_image = outputs[0]

    result_img = tf.squeeze(stylized_image)
    result_im = tf.cast(result_img * 255, tf.uint8)
    result_img_pillow = Image.fromarray(result_im.numpy())

    image_name_new = "handled_image_" + image_name
    result_img_pillow.save("{0}/{1}".format(config.result_storage_path, image_name_new))
    return image_name_new


def cleanup_remove_images(image_name, image_name_new, style_image_name):
    os.remove('{0}/{1}'.format(config.result_storage_path, image_name))
    os.remove('{0}/{1}'.format(config.result_storage_path, image_name_new))
    if style_image_name != 'standard style established':
        os.remove('{0}/{1}'.format(config.result_storage_path, style_image_name))


def get_save_style_image(number):
    # create folder to store image temporary, if it doesnt exist
    if not os.path.exists(config.result_storage_path):
        os.makedirs(config.result_storage_path)

    if not os.path.exists("{0}/handled_style{1}.jpg".format(config.result_storage_path, number)):
        image_mame = "style{0}.jpg".format(number)
        image_path = "static/" + image_mame
        style_image = Image.open(image_path)
        image_square_resized = image_to_square(style_image, 256)
        style_image_name = "handled_" + image_mame
        image_square_resized.save("{0}/{1}".format(config.result_storage_path, style_image_name))
    else:
        style_image_name = "handled_style{0}.jpg".format(number)

    return style_image_name


def image_to_square(image_name, image_size):
    width = image_name.width
    height = image_name.height
    if width == height:
        image_square_resized = image_name.resize((image_size, image_size))
    elif width > height:
        image_crop = image_name.crop(((width // 2 - height // 2), 0, (width // 2 - height // 2) + height, height))
        image_square_resized = image_crop.resize((image_size, image_size))
    else:
        image_crop = image_name.crop((0, (height // 2 - width // 2), width, (height // 2 - width // 2) + width))
        image_square_resized = image_crop.resize((image_size, image_size))

    return image_square_resized


def image_reduce(image_name, width_size):
    width = image_name.width
    height = image_name.height
    if width == height & width > width_size:
        image_resized = image_name.resize((width_size, width_size))
    elif width > width_size:
        factor = width / width_size
        image_resized = image_name.resize((width_size, round(height / factor)))
    else:
        image_resized = image_name

    return image_resized
