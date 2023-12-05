from fastapi import FastAPI
import numpy as np
import json, codecs
import os
import cv2 as cv

app = FastAPI(title="Data Manipulation")

@app.get('/')
async def root():
    return {'Title': 'Data Manipulation'}

@app.post('/json/{path: str}')
async def get_json(path: str):
    if os.path.isdir(path):
        for file in os.listdir(path):
            if file[-4: ] == '.npy':
                numpy_path = os.path.join(path, file)
                numpy_array = np.load(numpy_path, allow_pickle=True)
                array_json = []
                for object in numpy_array:
                    arr_dict = {'ObjectClassName': str(object[0]), 'Left': int(object[1]), 'Top': int(object[2]), 'Right': int(object[3]), 'Bottom': int(object[4]), 'precision?/confidence?': str(object[5])}

                    # arr_dict = {'ObjectClassName': str(object[2]), 'Left': int(object[-4]), 'Top': int(object[-3]), 'Right': int(object[-2]), 'Bottom': int(object[-1]), 'precision?/confidence?': str(object[5])}

                    array_json.append(arr_dict)
                file_serialized = json.dumps(array_json, separators=(',', ':'), indent=4)
                json_file_path = path +"/"+ file[: -4] + ".json"
                with codecs.open(json_file_path, 'w', encoding='utf-8') as f:
                    f.write(file_serialized)

        return json.dumps({"Files created": f"{path}"})
    else:
        return json.dumps({f'{path}': "is not a valid directory"})

@app.post('/bounding_box/{path: str}')
async def draw_bbox(path: str):
    if os.path.isdir(path):
        img_path = os.path.join(path, "images")
        for file in os.listdir(img_path):
            if file[-4: ] == '.png':
                img = cv.imread(os.path.join(img_path, file))
                json_exists = False
                json_path = os.path.join(path, "labels", "json")
                for json_file in os.listdir(json_path):
                    if json_file[-5: ] == ".json" and json_file[: -4] == file[: -3]:
                        print(f"Opening: {json_file}")
                        with open(os.path.join(json_path, json_file)) as f:
                            data = json.load(f)
                            for object in data:
                                object_Id = object['Id']
                                object_class_name = object['ObjectClassName']
                                xmin = object['Left']
                                ymin = object['Top']
                                xmax = object['Right']
                                ymax = object['Bottom']

                                color_dict = {
                                    'stillage': (255, 0, 0),
                                    'pallet': (0, 255, 0),
                                    'jack': (0, 0, 255),
                                    'safety_cone': (255, 255, 0),
                                    'dolly': (0, 255, 255),
                                    'fklt_box_6410': (255, 0, 255),
                                    'scratch': (150, 200, 50),
                                    'car': (200, 100, 50)
                                }
                                if object_class_name in color_dict:
                                    color = color_dict[object_class_name]
                                else:
                                    color = (255, 255, 255)

                                cv.rectangle(img, (xmin, ymin), (xmax, ymax), color=color, thickness=2)
                                new_path = os.path.join(path, ("annotated_" + file))
                                cv.imwrite(new_path, img)
            
                            json_exists = True
                if not json_exists:
                    os.remove(os.path.join(img_path, file))

        return json.dumps({"Files created": f"{path}"})
    else:
        return json.dumps({f'{path}': "is not a valid directory"})
    
@app.post('/remove_small_bounding_boxes/{path: str}')
async def remove_small_bbox(path: str, min_size: int):
    if os.path.isdir(path):
        img_path = os.path.join(path, "images")
        img_files = os.listdir(img_path)
        img_files.sort()
        json_path = os.path.join(path, "labels", "json")
        json_files = os.listdir(json_path)
        json_files.sort()

        img_index = 0
        json_index = 0

        def check_area(bbox):
            xmin = bbox['Left']
            ymin = bbox['Top']
            xmax = bbox['Right']
            ymax = bbox['Bottom']

            width = xmax - xmin
            height = ymax - ymin

            area = width * height

            return area >= min_size

        while img_index < len(img_files) and json_index < len(json_files):
            img_name = img_files[img_index][: -4]
            json_name = json_files[json_index][: -5]

            if img_name == json_name:
                with open(os.path.join(json_path, json_files[json_index])) as f:
                    data = json.load(f)

                    new_data = list(filter(check_area, data))
                    
                    if new_data == []:
                        os.remove(os.path.join(json_path, json_files[json_index]))
                        os.remove(os.path.join(img_path, img_files[img_index]))
                    else:
                        new_path = os.path.join(path, "new_json")
                        if not os.path.isdir(new_path):
                            os.mkdir(new_path)
                        with open(os.path.join(new_path, json_files[json_index]), 'w') as fp:
                            json.dump(new_data, fp)

                img_index = img_index + 1
                json_index = json_index + 1
                        
            elif img_name < json_name:
                os.remove(os.path.join(img_path, img_files[img_index]))
                img_index = img_index + 1
            else:
                os.remove(os.path.join(json_path, json_files[json_index]))
                json_index = json_index + 1

        while json_index < len(json_files):
            json_file = json_files[json_index]
            os.remove(os.path.join(json_path, json_file))
            json_index = json_index + 1

        while img_index < len(img_files):
            img_file = img_files[img_index]
            os.remove(os.path.join(img_path, img_file))
            img_index = img_index + 1

        return json.dumps({"Files created": f"{path}"})

    else:
        return json.dumps({f'{path}': "is not a valid directory"})
    
@app.post('/json_to_yolo/{path: str}')
async def convert_json_to_yolo(path: str):
    if os.path.isdir(path):
        img_path = os.path.join(path, "images")
        img_files = os.listdir(img_path)
        img_files.sort()
        json_path = os.path.join(path, "labels", "json")
        json_files = os.listdir(json_path)
        json_files.sort()

        img_index = 0
        json_index = 0
        
        class_mapping = {
            "dolly": 0,
            "stillage": 1,
            "jack": 2,
            "pallet": 3,
            "fklt_box_6410": 4,
            "safety_cone": 5
        }

        while img_index < len(img_files) and json_index < len(json_files):
            img_name = img_files[img_index][: -4]
            json_name = json_files[json_index][: -5]

            if img_name == json_name:
                
                img = cv.imread(os.path.join(img_path, img_files[img_index]))
                image_height, image_width, channels = img.shape

                with open(os.path.join(json_path, json_files[json_index])) as f:
                    data = json.load(f)

                    objects = data
                    yolo_lines = []

                    for obj in objects:
                        class_name = obj["ObjectClassName"]
                        if class_name in class_mapping:
                            class_number = class_mapping[class_name]
                            left = int(obj["Left"])
                            top = int(obj["Top"])
                            right = int(obj["Right"])
                            bottom = int(obj["Bottom"])

                            # Calculate YOLO format coordinates
                            x_center = (left + right) / 2 / int(image_width)
                            y_center = (top + bottom) / 2 / int(image_height)
                            width = (right - left) / int(image_width)
                            height = (bottom - top) / int(image_height)

                            yolo_line = f"{class_number} {x_center} {y_center} {width} {height}"
                            yolo_lines.append(yolo_line)

                    new_path = os.path.join(path, "yolo_labels")
                    if not os.path.isdir(new_path):
                        os.mkdir(new_path)

                    output_file_path = os.path.join(new_path, (json_name + ".txt"))
                    with open(output_file_path, "w") as file:
                        for line in yolo_lines:
                            file.write(line + "\n")

                img_index = img_index + 1
                json_index = json_index + 1
                        
            elif img_name < json_name:
                os.remove(os.path.join(img_path, img_files[img_index]))
                img_index = img_index + 1
            else:
                os.remove(os.path.join(json_path, json_files[json_index]))
                json_index = json_index + 1

        while json_index < len(json_files):
            json_file = json_files[json_index]
            os.remove(os.path.join(json_path, json_file))
            json_index = json_index + 1

        while img_index < len(img_files):
            img_file = img_files[img_index]
            os.remove(os.path.join(img_path, img_file))
            img_index = img_index + 1

        return json.dumps({"Files created": f"{path}"})

    else:
        return json.dumps({f'{path}': "is not a valid directory"})

@app.post('/resized_image/{path: str, width: int, height: int}')
async def resize_image(path: str, width: int, height: int):
    if os.path.isdir(path):
        for file in os.listdir(path):
            if file[-4: ] == '.png':
                img = cv.imread(os.path.join(path, file))
                json_exists = False
                for json_file in os.listdir(path):
                    if json_file[-5: ] == ".json" and json_file[-9: -4] == file[-8: -3]:
                        img_h, img_w = img.shape[0], img.shape[1]
                        HEIGHT = height
                        WIDTH = width
                        H_SCALE = img_h/HEIGHT
                        W_SCALE = img_w/WIDTH
                        img_resized = cv.resize(img, (WIDTH, HEIGHT))
                        img_path = os.path.join(path, file)
                        cv.imwrite(img_path, img_resized)

                        array_json = []

                        with open(os.path.join(path, json_file)) as f:
                            data = json.load(f)
                            for object in data:
                                object_class = object['class']
                                xmin = object['xmin']
                                ymin = object['ymin']
                                xmax = object['xmax']
                                ymax = object['ymax']
                                
                                xmin = int(xmin / W_SCALE)
                                ymin = int(ymin / H_SCALE)
                                xmax = int(xmax / W_SCALE)
                                ymax = int(ymax / H_SCALE)

                                arr_dict = {'class': object_class, 'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
                                array_json.append(arr_dict)

                                file_serialized = json.dumps(array_json, separators=(',', ':'), indent=4)
                                json_file_path = os.path.join(path, json_file)
                                with codecs.open(json_file_path, 'w', encoding='utf-8') as f:
                                    f.write(file_serialized)

                            json_exists = True
                if not json_exists:
                    os.remove(os.path.join(path, file))

        return json.dumps({"Files created": f"{path}"})
    else:
        return json.dumps({f'{path}': "is not a valid directory"})

        
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host='0.0.0.0', port=8888)
