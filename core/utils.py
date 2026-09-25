from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def get_exif_data(image_path):
    try:
        img = Image.open(image_path)
        exif = img._getexif()
        if not exif: return None, None
        gps_info = {}
        for tag, value in exif.items():
            decoded = TAGS.get(tag, tag)
            if decoded == 'GPSInfo':
                for t in value:
                    gps_info[GPSTAGS.get(t, t)] = value[t]
        if not gps_info: return None, None

        def to_degrees(value):
            d = float(value[0]); m = float(value[1]); s = float(value[2])
            return d + (m/60.0) + (s/3600.0)

        lat = to_degrees(gps_info['GPSLatitude'])
        if gps_info['GPSLatitudeRef']!= 'N': lat = -lat
        lng = to_degrees(gps_info['GPSLongitude'])
        if gps_info['GPSLongitudeRef']!= 'E': lng = -lng
        return lat, lng
    except Exception as e:
        print("EXIF error:", e)
        return None, None