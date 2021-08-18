import tkinter.filedialog as filedialog
from tkinter import messagebox
import os
from predictionModel import predictionCNN
from PIL import Image,ImageDraw,ImageFont
from PIL.ExifTags import TAGS,GPSTAGS
import numpy as np

import multiprocessing
import time

FOLDER=''
exportpath=''
batch_filenames=[]

class batch_ser_func():
    def __init__(self,filename,dlinput,inputconfidence):
        self.file=filename
        self.folder=FOLDER
        self.exportpath=exportpath
        self.dlinput=dlinput
        self.confidence=None
        self.confidthres=inputconfidence
        self.RGBimg=Image.open(os.path.join(FOLDER,self.file))
        self.rgbwidth,self.rgbheight=self.RGBimg.size
        self.imgsize={}
        self.imgsize.update({'row':self.rgbheight})
        self.imgsize.update({'col':self.rgbwidth})
        self.npimage=None
        self.localdlinput=None
        self.predres=None


    def addbars(self,locs):
        x0=min(locs[1])
        y0=min(locs[0])
        x1=max(locs[1])
        y1=max(locs[0])
        draw=ImageDraw.Draw(self.RGBimg)
        # endx=int(x0+(x1-x0)/2)
        # endy=int(y0+(y1-y0)/2)
        draw.line(((x0,y0),(x1,y0)),fill='red',width=5) #draw up red line
        draw.line(((x0,y0),(x0,y1)),fill='red',width=5) #draw left red line
        # self.show_image()

    def export_single(self):
        #draw gridimg
        for i in range(len(self.predres)):
            if self.predres[i]==1:
                locs=np.where(self.npimage==(i+1))
                self.addbars(locs)
        filenamepart=os.path.splitext(self.file)
        outputname=filenamepart[0]+'_gridimg.png'
        totalhealthy=self.predres.count(0)
        totalinfect=self.predres.count(1)

        imginfo=self.RGBimg.getexif()
        if len(imginfo)>0:
            exif_table={}
            for tag,value in imginfo.items():
                decoded=TAGS.get(tag,tag)
                exif_table[decoded]=value
            print(exif_table.keys())
            if 'GPSInfo' in exif_table.keys():
                gps_info={}
                for key in exif_table['GPSInfo'].keys():
                    decoded=GPSTAGS.get(key,key)
                    gps_info[decoded]=exif_table['GPSInfo'][key]
                GPS_Lat=list(gps_info['GPSLatitude'])
                GPS_Long=list(gps_info['GPSLongitude'])
                latitude=str(GPS_Lat[0][0])+'.'+str(GPS_Lat[1][0])+"'"+str(GPS_Lat[2][0])+"''"
                # print()
                longitude=str(GPS_Long[0][0])+'.'+str(GPS_Long[1][0])+"'"+str(GPS_Long[2][0])+"''"
            else:
                longitude=0
                latitude=0
            # print
        else:
            longitude=0
            latitude=0
        avg_confid=np.mean(np.array(self.confidence))
        std_confid=np.std(np.array(self.confidence))
        max_confid=np.max(np.array(self.confidence))
        min_confid=np.min(np.array(self.confidence))
        summary=[self.file,totalhealthy,totalinfect,longitude,latitude,avg_confid,std_confid,max_confid,min_confid]

        import csv
        outputcsv=os.path.join(self.exportpath,outputname+'_output.csv')
        headline=['index','row','col','label','prediction','confidence']
        with open(outputcsv,mode='w') as f:
            csvwriter=csv.writer(f,lineterminator='\n')
            csvwriter.writerow(headline)
            rownum=self.localdlinput['row']
            colnum=self.localdlinput['col']
            gridnum=rownum*colnum
            # outputimg=labelimage.copy()
            draw=ImageDraw.Draw(self.RGBimg)
            for i in range(gridnum):
                index=i+1
                row=int(i/colnum)
                col=i%colnum
                locs=np.where(self.npimage==index)
                x0=min(locs[1])
                y0=min(locs[0])
                x1=max(locs[1])
                y1=max(locs[0])
                # if int(imageexport.get())==1:
                #     cropimage=RGBimg.crop((x0,y0,x1,y1))
                #     cropimage.save(outpath+'/'+originfile+'_crop_'+str(index)+'.png','PNG')
                midx=x0+5
                midy=y0+5
                state='crop-'+str(index)
                draw.text((midx-1, midy+1), text=state, fill='white')
                draw.text((midx+1, midy+1), text=state, fill='white')
                draw.text((midx-1, midy-1), text=state, fill='white')
                draw.text((midx+1, midy-1), text=state, fill='white')
                draw.text((midx,midy),text=state,fill='black')
                # if exportoption.get()=='P':
                #     label=predictlabels[i]
                # if exportoption.get()=='C':
                # label=infectedlist[i]
                label=0
                # if confidence!=None:
                #     pred_label= 1 if list(confidence)[i]>=float(slider.get()) else 0
                #     confidvalue=list(confidence)[i]
                #     content=[index,row,col,label,pred_label,confidvalue]
                # else:
                #     content = [index, row, col, label,0,0]
                confidvalue=self.confidence[i]
                pred_label=self.predres[i]
                content=[index,row,col,label,pred_label,confidvalue]
                csvwriter.writerow(content)
                print(index)
            self.RGBimg.save(os.path.join(self.exportpath,outputname),'PNG')
            del draw
        f.close()

        return summary

    def prediction(self):
        self.confidence=predictionCNN(self.localdlinput)
        temppred=[0 for i in range(len(self.confidence))]
        satisfiedpred=np.where(np.array(self.confidence)>=self.confidthres)
        temppred=np.array(temppred)
        temppred[satisfiedpred]=1
        self.predres=list(temppred.copy())
        pass

    def drawgrid(self):
        row_stepsize = int(self.rgbheight / self.localdlinput['row'])
        col_stepsize = int(self.rgbwidth / self.localdlinput['col'])
        draw = ImageDraw.Draw(self.RGBimg)
        row_start = 0
        row_end = self.rgbheight
        col_start = 0
        col_end = self.rgbwidth
        for col in range(0, col_end, col_stepsize):
            line = ((col, row_start), (col, row_end))
            draw.line(line, fill='white', width=5)

        for row in range(0, row_end, row_stepsize):
            line = ((col_start, row), (col_end, row))
            draw.line(line, fill='white', width=5)

        del draw
        pass

    def updatenpimage(self):
        gridnum=self.localdlinput['row']*self.localdlinput['col']
        row_stepsize=int(self.rgbheight/self.localdlinput['row'])
        col_stepsize=int(self.rgbwidth/self.localdlinput['col'])
        print(gridnum,row_stepsize,col_stepsize)
        self.npimage=np.zeros((self.rgbheight,self.rgbwidth))
        for i in range(gridnum):
            c=i%self.localdlinput['col']
            r=int(i/self.localdlinput['col'])
            print(r,c)
            self.npimage[r*row_stepsize:(r+1)*row_stepsize,c*col_stepsize:(c+1)*col_stepsize]=i+1
        print(self.npimage)

    def process(self):
        orient={k:v for k,v in sorted(self.imgsize.items(), key=lambda item: item[1],reverse=True)}
        # orient=sorted(self.imgsize.items(),reverse=True)
        print(orient)
        orientkeys=[key for key in orient.keys()]
        print(orientkeys)
        self.localdlinput=self.dlinput.copy()
        if self.localdlinput[orientkeys[0]]<self.localdlinput[orientkeys[1]]:
            temp=self.localdlinput[orientkeys[0]]
            self.localdlinput[orientkeys[0]]=localdlinput[orientkeys[1]]
            self.localdlinput[orientkeys[1]]=temp

        self.drawgrid()
        self.updatenpimage()
        self.prediction()
        summary=self.export_single()
        return summary


def Open_batchfolder():
    global batch_filenames
    global FOLDER

    batch_filenames=[]

    FOLDER=filedialog.askdirectory()
    if len(FOLDER)>0:
        print(FOLDER)
        files=os.listdir(FOLDER)
        for filename in files:
            if 'jpg' in filename or 'jpeg' in filename or 'JPG' in filename:
                batch_filenames.append(filename)
    batch_filenames.sort()
    print('filenames',batch_filenames)
    return os.path.join(FOLDER,batch_filenames[0])

def batch_exportpath():
    global exportpath
    exportpath=filedialog.askdirectory()
    while len(exportpath)==0:
        exportpath=filedialog.askdirectory()

def batch_process(dlinput,inputconfidence):
    if len(batch_filenames)==0:
        messagebox.showerror('No files','Please load images to process')
        return
    cpunum=multiprocessing.cpu_count()
    print('# of CPUs',cpunum)
    starttime=time.time()
    print('start time',starttime)
    batch_summary=[]
    head=['filename','healthy#','infected#','Longitude(E,W)','Latitude(N,S)','avg-confid','std-confid','max-confid','min-confid']
    batch_summary.append(head)
    for file in batch_filenames:
        procobj=batch_ser_func(file,dlinput,inputconfidence)
        filesummary=procobj.process()
        batch_summary.append(filesummary)
        del procobj
    import csv
    outputcsv=os.path.join(exportpath,'summary'+'_confidthres='+str(inputconfidence)+'_.csv')
    with open(outputcsv,mode='w') as f:
        csvwriter=csv.writer(f,lineterminator='\n')
        for ele in batch_summary:
            csvwriter.writerow(ele)
        f.close()
    print('used time',time.time()-starttime)
    messagebox.showinfo('Batch processing done','Batch process done!')
