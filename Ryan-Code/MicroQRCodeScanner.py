import cv2
import time
import os
import json
import numpy as np
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askdirectory
import matplotlib.pyplot as plt

#Get Image and Scanner Pathname
print("Image File")
imgpath = askopenfilename()
#imgpath = "C:/users/rwojtowi_stu/desktop/testimage123.png"
imgname = imgpath[imgpath.rfind("/")+1:imgpath.rfind(".")]
imgFile = imgpath[imgpath.rfind("/")+1:len(imgpath)]
print(imgname)
print("applications.jar file")
#scannerPath = askopenfilename()
scannerPath = "C:/users/rwojtowi_stu/Desktop/boofcv implementation/boofcv/applications/applications.jar"
print("json output directory")
#outputPath = askdirectory()
outputPath = "C:/users/rwojtowi_stu/desktop"
#AI Upscale Model path
print("AI Upscale model path")
#AIpath = askopenfilename()
AIpath = "C:\\Users\\rwojtowi_stu\\downloads\\espcn_x2.pb"

sr = cv2.dnn_superres.DnnSuperResImpl_create()
sr.readModel(AIpath)
sr.setModel("espcn",2)

SR = [[None]]
shape = [[None]]

start = time.time()
#Read Image
img = cv2.imread(imgpath)
imgX = img.shape[1]
imgY = img.shape[0]
#Run MicroQR Scanner
os.system("java -jar \""+scannerPath+"\" BatchScanMicroQrCodes -i \""+imgpath+"\" -o \""+outputPath+"/"+imgname+".json\"")

#Set Json Paths
jsonPath = outputPath+"/"+imgname+".json"
jsonFailPath = outputPath+"/"+imgname+"Fail.json"

#Load Failed MicroQRCode Data
#print(jsonFailPath)
failData = json.load(open(jsonFailPath))
#print(failData.items())
#Get Position pattern of each failed microQR
increment = 0
minXArr = []
minYArr = []
for file,MQRCode in failData.items():   
    for MQRName,MQRCodeBounds in MQRCode.items():
        bounding_box = MQRCodeBounds["BoundingBox"]
        coordinates = [
            (int(bounding_box["Point1"]["x"]), int(bounding_box["Point1"]["y"])),
            (int(bounding_box["Point2"]["x"]), int(bounding_box["Point2"]["y"])),
            (int(bounding_box["Point3"]["x"]), int(bounding_box["Point3"]["y"])),
            (int(bounding_box["Point4"]["x"]), int(bounding_box["Point4"]["y"]))
        ]
        #Find center of position pattern bounding box
        cx=0
        cy=0
        for x,y in coordinates:
            cx+=x
            cy+=y
        cx/=4
        cy/=4
        s = (4,2)
        newCoords = np.zeros(s)
        for i in range(4):
            newCoords[i][0] = cx+(3.85714286)*(coordinates[i][0]-cx)    #3.85714286 is the scale factor for the position pattern to full MQR Code
            if newCoords[i][0] > imgX:
                newCoords[i][0] = imgX
            if newCoords[i][0] < 0:
                newCoords[i][0] = 0
            newCoords[i][1] = cy+(3.85714286)*(coordinates[i][1]-cy) 
            if newCoords[i][1] > imgY:
                newCoords[i][1] = imgY
            if newCoords[i][1] < 0:
                newCoords[i][1] = 0
        #Find max and min x and y in newCoords to partition image
        maxX,maxY = 0,0
        minX,minY = 10000000000,10000000000
        for i in range(4):
            if maxX < newCoords[i][0]:
                maxX = newCoords[i][0]
            if maxY < newCoords[i][1]:
                maxY = newCoords[i][1]
            if minX > newCoords[i][0]:
                minX = newCoords[i][0]
            if minY > newCoords[i][1]:
                minY = newCoords[i][1]
        
        minXArr.append(minX)
        minYArr.append(minY)
        minXArr.append(minX)
        minYArr.append(minY)
        #Initialize sub Image
        print(maxX-minX)
        subImg = img[int(minY):int(maxY),int(minX):int(maxX)]
        ##Display Sub Image
        #cv2.imshow("subImage",subImg)
        #cv2.waitKey(0)
        ##End display
        #Super Resolution
        SR[increment][0] = sr.upsample(subImg)
        #Resized x0.5
        SR[increment].append(sr.upsample(cv2.resize(subImg,dsize=None,fx=.5,fy=.5)))
        SR.append([None])
        increment += 1
SR.pop(len(SR)-1)
maxW = max(max([img[0].shape[1],img[1].shape[1]]) for img in SR)
SRnew = [] # New list of images
height = []  #The subsequent "height" that each image ends at
scale = [] # The scale factor on each image to vertically concatenate
sum = 0
scaleby2 = 2 ## The first image is Super resolution by 2. the second is scaled down by 0.5
for i in range(len(SR)):
    for j in range(2):
        SRnew.append(cv2.resize(SR[i][j],(maxW,int(SR[i][j].shape[0]*maxW/SR[i][j].shape[1])),interpolation=cv2.INTER_CUBIC)) #New images
        sum += int(SR[i][j].shape[0]*maxW/SR[i][j].shape[1]) #get the height values
        height.append(sum)
        scale.append(1/(maxW/SR[i][j].shape[1]*scaleby2)) #scale factor
        if scaleby2 == 2:
            scaleby2 = 1 #Same as resize Scale * upsample amount (0.5*2)
        else:
            scaleby2 = 2

totalImg = cv2.vconcat(SRnew) #Concatenate images
#cv2.imshow("TotalImg",totalImg)
#cv2.waitKey(0)
 #Image path for the image concatenation
failimgPath = outputPath+"/TestImage123.png"
#Save image concatenation
cv2.imwrite(failimgPath,totalImg,params=None) 
#Scan new image for micro qr codes
os.system("java -jar \""+scannerPath+"\" BatchScanMicroQrCodes -i \""+failimgPath+"\" -o \""+outputPath+"/"+"TestImage123"+".json\"") 
#The json file with the new set of scans
jsonPathTwo = outputPath+"/"+"TestImage123"+".json"
increment = 0
newScan = []
data = json.load(open(jsonPathTwo))
jsonFile = open(jsonPath,"r+")
oldData = json.load(jsonFile)
noMQRs = len(oldData[imgFile])
increment2 = 0
for image_name, qr_codes in data.items():
    for qr_code_name, qr_code_data in qr_codes.items():
        newScan.append(qr_code_data.get("Data", ""))
        bounding_box = qr_code_data["BoundingBox"]
        coordinates = [
            (int(bounding_box["Point1"]["x"]), int(bounding_box["Point1"]["y"])),
            (int(bounding_box["Point2"]["x"]), int(bounding_box["Point2"]["y"])),
            (int(bounding_box["Point3"]["x"]), int(bounding_box["Point3"]["y"])),
            (int(bounding_box["Point4"]["x"]), int(bounding_box["Point4"]["y"]))
        ]
        increment = 0
        for h in height:
            if coordinates[0][1] < h:
                break
            increment += 1
        if increment < len(minXArr):
            h = 0
            if increment != 0:
                h = height[increment-1]
            coordinates2 = [
                (int(float(bounding_box["Point1"]["x"])*scale[increment]+minXArr[increment]), (int((float(bounding_box["Point1"]["y"])-h)*scale[increment]+minYArr[increment]))),
                (int(float(bounding_box["Point2"]["x"])*scale[increment]+minXArr[increment]), (int((float(bounding_box["Point2"]["y"])-h)*scale[increment]+minYArr[increment]))),
                (int(float(bounding_box["Point3"]["x"])*scale[increment]+minXArr[increment]), (int((float(bounding_box["Point3"]["y"])-h)*scale[increment]+minYArr[increment]))),
                (int(float(bounding_box["Point4"]["x"])*scale[increment]+minXArr[increment]), (int((float(bounding_box["Point4"]["y"])-h)*scale[increment]+minYArr[increment])))
            ]
            #MQR = {"MicroQRCode"+str(increment2+noMQRs):[{"Data":newScan[increment2]},{"BoundingBox":[{"Point1":[{"x":coordinates2[0][0]},{"y":coordinates2[0][1]}]},{"Point2":[{"x":coordinates2[1][0]},{"y":coordinates2[1][1]}]},{"Point3":[{"x":coordinates2[2][0]},{"y":coordinates2[2][1]}]},{"Point4":[{"x":coordinates2[3][0]},{"y":coordinates2[3][1]}]}]}]}
            MQR = {"Data":newScan[increment2],"BoundingBox":{"Point1":{"x":coordinates2[0][0],"y":coordinates2[0][1]},"Point2":{"x":coordinates2[1][0],"y":coordinates2[1][1]},"Point3":{"x":coordinates2[2][0],"y":coordinates2[2][1]},"Point4":{"x":coordinates2[3][0],"y":coordinates2[3][1]}}}
            increment2 += 1
            oldData[imgFile]["MicroQRCode"+str(increment2+noMQRs)] = MQR
            ###Debug
            #print(coordinates)
            #print(coordinates2)
            #print(minXArr[increment])
            #print(minYArr[increment])
#print(oldData)
jsonFile.seek(0)
json.dump(oldData, jsonFile, indent = 4)
end = time.time()
print(end-start)
        
        

    




