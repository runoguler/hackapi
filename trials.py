import cloudinary
from cloudinary import uploader

cloudinary.config(
  cloud_name = 'dku6odlrx',
  api_key = '719974798677889',
  api_secret = '6RkpNRe-cV0SuD7FFCuIh85Y9n0'
)


response = cloudinary.uploader.upload("deneme.jpg", ocr="adv_ocr")
if response['info']['ocr']['adv_ocr']['status'] == 'complete':
    data = response['info']['ocr']['adv_ocr']['data']
    ann = data[0]["textAnnotations"]
    result = ""
    max_area = 0
    for d in ann:
        if "\n" in d["description"]:
            continue
        x1, x2, y1, y2 = 0, 0, 0, 0
        x1 = d["boundingPoly"]["vertices"][0]['x']
        y1 = d["boundingPoly"]["vertices"][0]['y']
        x2 = d["boundingPoly"]["vertices"][1]['x']
        y2 = d["boundingPoly"]["vertices"][2]['y']
        area = (x2 - x1) * (y2 - y1)
        if area > max_area:
            result = d["description"]
            max_area = area

    print(result)