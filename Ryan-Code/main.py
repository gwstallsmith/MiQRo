import json
import os
import svgwrite
from PIL import Image
import base64
import math
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askdirectory
import time


def get_image_data(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_image_size(image_path):
    with Image.open(image_path) as img:
        return img.size


def calculate_text_position(coordinates, text, font_size, spacing):
    # Calculate the center of the polygon
    center_x = sum(x for x, y in coordinates) // len(coordinates)
    center_y = sum(y for x, y in coordinates) // len(coordinates)

    # Estimate the width of the text using a simple formula (adjust as needed)
    text_width = len(text) * font_size * 0.6

    # Calculate the distance between the original coordinates and the desired text position
    distance = (text_width / 2) + spacing

    # Calculate the angle of the line connecting the original center to the new center
    angle = math.atan2(coordinates[0][1] - center_y, coordinates[0][0] - center_x)

    # Calculate the new coordinates based on the Pythagorean theorem
    new_x = center_x + distance * math.cos(angle)
    new_y = center_y + distance * math.sin(angle)

    return new_x, new_y


def create_svg(json_path, output_path, image_path):
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)

        for image_name, qr_codes in data.items():
            if not qr_codes:
                continue

            image_data = get_image_data(image_path)
            image_size = get_image_size(image_path)

            dwg = svgwrite.Drawing(os.path.join(output_path, f"{image_name}.svg"), size=image_size)

            # Embed the image data in the SVG
            dwg.add(dwg.image(href=f"data:image/png;base64,{image_data}", insert=(0, 0), size=image_size))

            #Pulls the coordinates from the JSON file
            for qr_code_name, qr_code_data in qr_codes.items():
                if "BoundingBox" in qr_code_data:
                    bounding_box = qr_code_data["BoundingBox"]
                    coordinates = [
                        (int(bounding_box["Point1"]["x"]), int(bounding_box["Point1"]["y"])),
                        (int(bounding_box["Point2"]["x"]), int(bounding_box["Point2"]["y"])),
                        (int(bounding_box["Point3"]["x"]), int(bounding_box["Point3"]["y"])),
                        (int(bounding_box["Point4"]["x"]), int(bounding_box["Point4"]["y"]))
                    ]
                    
                    data_text = str(calculateDistance(qr_code_data.get("Data", ""),bounding_box,image_size))
                    
                    #qr_code_data.get("Data", "")  # Get the data variable

                    # Calculate the position for the text with spacing
                    text_x, text_y = calculate_text_position(coordinates, data_text, font_size=16, spacing=10)

                    # Add a polygon to the SVG
                    dwg.add(dwg.polygon(points=coordinates, stroke=svgwrite.rgb(255, 0, 0, '%'), fill='none'))

                    # Add text to the SVG with the adjusted position
                    dwg.add(dwg.text(data_text, insert=(text_x, text_y),
                                     font_size=16, font_family="Arial", fill=svgwrite.rgb(255, 0, 0, '%')))

            dwg.save()
def calculateDistance(data,bb,size):
    r = 1#float(data)
    x1 = int(bb["Point1"]["x"])
    y1 = int(bb["Point1"]["y"])
    x2 = int(bb["Point2"]["x"])
    y2 = int(bb["Point2"]["y"])
    x3 = int(bb["Point4"]["x"])
    y3 = int(bb["Point4"]["y"])

    P1=x2-x1
    P2=y2-y1
    P3=x3-x1
    P4=y3-y1

    S=math.sqrt((P1*P1+P2*P2+P3*P3+P4*P4+math.sqrt(math.pow(P1*P1+P2*P2+P3*P3+P4*P4,2)-4*math.pow(P1*P4-P2*P3,2)))/2)/r
    P=size[1]
    A=60
    d=P/(2*math.tan(math.pi/180*A/2))
    return round(100*math.sqrt(math.pow(x1-P/2,2)+math.pow(x1-P/2,2)+math.pow(d,2))/S)/100
    

if __name__ == "__main__":
    print("JSON File")
    json_file_path = askopenfilename()
    print("Output Directory")
    output_directory = askdirectory()
    print("Image path")
    image_path = askopenfilename()
    #json_file_path = "C:\\Users\\rwojtowi_stu\\Desktop\\MQRTest2.json"  # Replace with the path to your JSON file
    #output_directory = "C:\\Users\\rwojtowi_stu\\Desktop"  # Replace with the desired output directory
    #image_path = os.path.join("C:\\Users\\rwojtowi_stu\\Desktop\\ImageTesting\\ImageTest2.png")  # Replace with the path to your image
    create_svg(json_file_path, output_directory, image_path)
