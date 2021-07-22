import torch
from torchvision import transforms, models
import torch.nn as nn
from PIL import Image
import os
import time


def crop(img, h=224, w=224, output="./example/tile"):
    im = Image.open(img)
    im_name = img.split("/")[-1]
    im_name = im_name.replace('.JPG','')
#     print(im_name)
    W, H = im.size
    for i in range(0,H,h):
        raw_n = int(i/224 + 1)
        for j in range(0,W,w):
            col_n = int(j/224 + 1)
            box = (j, i, j+w, i+h)
            tile = im.crop(box)
            tile.save(output + "/%s_%s_%s.png" % (im_name, raw_n, col_n))


def resnet18(weight='./models/torch_2class_resnet_3.pth'):
    # define model
    model = models.resnet18(pretrained=False)
    num_fc_in = model.fc.in_features
    model.fc = nn.Linear(num_fc_in, 2)
    # load weight
    weights = torch.load(weight, map_location='cpu')
    model.load_state_dict(weights)
    return model

def predictionCNN(dlinput):
    print("start prediction!")
    rownum = dlinput['row']
    colnum = dlinput['col']
    img = dlinput['imagepath']
    weight = dlinput['weight']
    model_name = dlinput['model']

    img = Image.open(img)
    if img.format!='JPEG':
        img=img.convert('RGB')
    print("row num is %s" % rownum)
    print("col num is %s" % colnum)
    print("++++++")
    print(img.size)
    rgbwidth, rgbheight = img.size
    row_stepsize = int(rgbheight / rownum)
    col_stepsize = int(rgbwidth / colnum)

    # model to cpu or gpu
    model = resnet18(weight)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    # prediction
    y_pred = []
    model.eval()
    with torch.no_grad():
        for col in range(0,rgbwidth,col_stepsize):
            if col + col_stepsize <= rgbwidth:
                for row in range(0, rgbheight, row_stepsize):
                    if row + row_stepsize <= rgbheight:
                        b_w, b_h = 0,0

                        if col + col_stepsize * 2 > rgbwidth:
                            b_w = rgbwidth - col
                        else:
                            b_w = col_stepsize

                        if row + row_stepsize * 2 > rgbheight:
                            b_h = rgbheight - row
                        else:
                            b_h = row_stepsize


                        box = (col, row, col+b_w, row+b_h)
                        print(box)

                        input_img = img.crop(box)
                        transform = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor()])
                        input_tensor = transform(input_img)
                        input_batch = input_tensor.unsqueeze(0)
                        input_batch = input_batch.to(device)
                        output = model(input_batch)
                        probabilities = torch.nn.functional.softmax(output[0], dim=0)
                        probabilities = probabilities.tolist()
                        print(probabilities)
                        y_pred.append(probabilities[0])


    # print(y_pred)
    print(len(y_pred))

    return y_pred

if __name__ == '__main__':
    start = time.time()
    # crop('./example/DJI_0197.JPG')
    # predictionCNN(rownum=10,colnum=10)
    # end = time.time()
    t = end - start
    print("time is %s s"%(t))