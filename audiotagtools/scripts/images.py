from os.path import splitext

import click
from wand.image import Image


@click.command()
@click.option('-w', '--width', help='Desired width of the output image.', default=1000, show_default=True)
@click.option('-n', '--name', default='folder', help='Filename of the output image.', show_default=True)
@click.argument('image')
def resize_image(image, width, name):
    """
    Formats an image to a specific pixel-width, 1000 by default.\n
    Converts the image to JPEG format, if necessary.\n
    Renames the output to "folder.jpg" This WILL overwrite any file named "folder.jpg".
    """
    with Image(filename=image) as img:
        fname, ext = splitext(image)
        if ext not in ['jpg', 'jpeg']:
            img.format = 'jpeg'
        if img.width > width:
            sf = width / img.width
            new_height = int(round(sf * img.height))
            img.resize(width=width, height=new_height)
        img.save(filename=f'{name}.jpg')


def test_function(image):
    with Image(filename=image) as img:
        fname, ext = splitext(image)
        if ext not in ['jpg', 'jpeg']:
            img.format = 'jpeg'
        if img.width > 1000:
            sf = 1000 / img.width
            new_height = int(round(sf * img.height))
            img.resize(width=1000, height=new_height)
        img.save(filename=f'{fname}_resized.jpg')
