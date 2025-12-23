from imagekit import ImageSpec
from imagekit.registry import register
from imagekit.processors import ResizeToFill, ResizeToFit

class ProductThumbnail(ImageSpec):
    processors = [ResizeToFill(100, 100)]
    format = 'JPEG'
    options = {'quality': 85}

class ProductMedium(ImageSpec):
    processors = [ResizeToFit(500, 500)]
    format = 'JPEG'
    options = {'quality': 85}

class ProductLarge(ImageSpec):
    processors = [ResizeToFit(800, 800)]
    format = 'JPEG'
    options = {'quality': 85}

class ProductWebP(ImageSpec):
    processors = [ResizeToFit(800, 800)]
    format = 'WEBP'
    options = {'quality': 85}

class AdminThumbnail(ImageSpec):
    processors = [ResizeToFill(50, 50)]
    format = 'JPEG'
    options = {'quality': 60}