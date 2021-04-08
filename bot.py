# coding: utf-8
import telebot
from image_utils import get_save_style_image, save_image_from_message, handle_image, cleanup_remove_images
import config

#tf.enable_eager_execution()

telbot = telebot.TeleBot(config.TOKEN)


@telbot.message_handler(commands=['start'])
def welcome(message):
    telbot.send_message(message.chat.id, config.welcome_text)

    for number in range(1, 9):
        style_image_name = get_save_style_image(number)
        telbot.send_photo(message.chat.id, open('{0}/{1}'.format(config.result_storage_path, style_image_name), 'rb'),
                          'Style image {0}'.format(number))

    telbot.send_message(message.chat.id,
                        'Send number of style image or upload own style image')


@telbot.message_handler(content_types=['text'])
def handle_text(message):
    cid = message.chat.id
    if message.text.isdigit():
        style_number = int(message.text)
        if 0 < style_number <= 8:
            config.dict_styles[cid] = style_number
            config.dict_styles_established[cid] = 'standard style established'
            get_save_style_image(style_number)
            telbot.send_message(message.chat.id,
                                'You have chosen Style image ' + str(style_number) + '. Now upload image for stylizing.')
        else:
            telbot.send_message(message.chat.id,
                                'Number is not correct. Send number of style image or upload own style image')
    else:
        telbot.send_message(message.chat.id,
                            'Input is not correct. Send number of style image or upload own style image')


@telbot.message_handler(content_types=['photo'])
def handle_photo(message):
    cid = message.chat.id

    # If photo is content photo
    if cid in config.dict_styles_established:
        image_name = save_image_from_message(message, telbot)
        telbot.send_message(cid, '⏳️Image have been received and processing now, be patient! ⏳️')
        image_name_new = handle_image(image_name, cid)
        telbot.send_photo(message.chat.id, open('{0}/{1}'.format(config.result_storage_path, image_name_new), 'rb'),
                          'Handled image ⌛️')
        telbot.send_message(message.chat.id,
                            'Want to try it again? Send number of style image or upload own style image')
        cleanup_remove_images(image_name, image_name_new, config.dict_styles_established[cid])
        del config.dict_styles_established[cid]
    # If photo is style photo
    else:
        image_name = save_image_from_message(message, telbot)
        config.dict_styles_established[cid] = image_name
        telbot.send_message(cid, 'Style image have been received. Now upload image for stylizing.')


# RUN
if __name__ == "__main__":
    telbot.polling(none_stop=True)
