from tkinter import *
from tkinter import ttk
import tkinter.filedialog as filedialog
from tkinter import messagebox
from PIL import Image,ImageDraw,ImageFont
from PIL import ImageTk,ImageGrab
from PIL.ExifTags import TAGS,GPSTAGS
import cv2
import numpy as np
import os
from predictionModel import predictionCNN
import rooster_batch

root=Tk()
root.title('Rootster v.0 ')
root.geometry("")
root.option_add('*tearoff',False)
emptymenu=Menu(root)
root.config(menu=emptymenu)
screenheight=root.winfo_screenheight()
screenwidth=root.winfo_screenwidth()
print('screenheight',screenheight,'screenwidth',screenwidth)
screenstd=min(screenheight-100,screenwidth-100,850)

# -----variables------

viewopt_var=StringVar()
scaleval=DoubleVar()
# RGBbands=None
RGBimg=None
gridimg=None
gridnum=0
zoom=None
hasGrid=False
hasMap=False
predictlabels=None
confidence=None
hasPred=False
rownum=0
colnum=0
csvname=''
e1=None


# ------functions-----

def init_canvas(path):
    import zoom_example
    global panelA,zoom
    rownum=int(rowentry.get())
    colnum=int(colentry.get())
    zoom=zoom_example.Zoom_Advanced(imageframe,panelA,path,rownum,colnum,1440,900)



def Open_File():
    global RGBimg,filename
    head_tail = os.path.split(filename)
    originfile, extension = os.path.splitext(head_tail[1])
    print(originfile,extension)
    if 'HEIC' in extension:
        import pyheif
        heif_file=pyheif.read(filename)
        RGBimg=Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw",
            heif_file.mode,
            heif_file.stride,
        )
        RGBimg.save(head_tail[0]+'/'+originfile+'.jpg',"JPEG")
        filename=head_tail[0]+'/'+originfile+'.jpg'
        return True

    '''batch process HEIC pictures'''
    # files=os.listdir(head_tail[0])
    # import pyheif
    # for tempname in files:
    #     if 'HEIC' in tempname:
    #         originfile, extension = os.path.splitext(tempname)
    #         heif_file = pyheif.read(head_tail[0]+'/'+tempname)
    #         RGBimg=Image.frombytes(
    #             heif_file.mode,
    #             heif_file.size,
    #             heif_file.data,
    #             "raw",
    #             heif_file.mode,
    #             heif_file.stride,
    #         )
    #         RGBimg.save(head_tail[0]+'/'+originfile+'.jpg',"JPEG")
    #         filename=head_tail[0]+'/'+originfile+'.jpg'
    #         print(filename)
    # return True



    try:
        Filersc=cv2.imread(filename,flags=cv2.IMREAD_ANYCOLOR)
        h,w,c=np.shape(Filersc)
        print('image size:',h,w)
        # RGBbands=cv2.cvtColor(Filersc,cv2.COLOR_BGR2RGB)
        RGBimg=Image.open(filename)
        imginfo=RGBimg.getexif()
        exif_table={}
        for tag,value in imginfo.items():
            decoded=TAGS.get(tag,tag)
            exif_table[decoded]=value
        gps_info={}
        for key in exif_table['GPSInfo'].keys():
            decoded=GPSTAGS.get(key,key)
            gps_info[decoded]=exif_table['GPSInfo'][key]
        GPS_Lat=list(gps_info['GPSLatitude'])
        GPS_Long=list(gps_info['GPSLongitude'])
        print(GPS_Lat[0][0],GPS_Lat[1][0])
        print(GPS_Long[0][0],GPS_Long[1][0])
        # head_tail = os.path.split(filename)
        # originfile, extension = os.path.splitext(head_tail[1])
        # print('head_tail',head_tail,'originfile',originfile,'extension',extension)
    except:
        return False
    return True

def zoomimage(opt):
    global zoom
    print(opt)
    try:
        zoom.wheel(opt)
    except:
        return

def Open_Multifile():
    global gridbutton,rowentry,colentry,exportbutton,filename,zoombar,mapfilebutton,hasMap,hasGrid,hasPred
    global reversebutton,predictbutton,slider,predictlabels,confidence
    if proc_mode[proc_name].get()=='1':
        filename=rooster_batch.Open_batchfolder()
        if Open_File()!=False:
            root.update()
            mapfilebutton.configure(state=DISABLED)
            # gridbutton.configure(state=DISABLED)
            reversebutton.configure(state=DISABLED)
            zoomin.configure(state=NORMAL)
            zoomout.configure(state=NORMAL)
            rowentry.configure(state=NORMAL)
            colentry.configure(state=NORMAL)
            gridbutton.configure(state=NORMAL)
            exportbutton.configure(state=NORMAL)
            # predictbutton.configure(state=NORMAL)
            confidence=None
            hasGrid=False
            init_canvas(filename)
            slider.state(["!disabled"])
            # slider.bind('<ButtonRelease-1>',changeconfidencerange)
        return
    filename=filedialog.askopenfilename()
    root.update()
    if Open_File()!=False:
        gridbutton.configure(state=NORMAL)
        rowentry.configure(state=NORMAL)
        colentry.configure(state=NORMAL)
        exportbutton.configure(state=NORMAL)
        zoomout.configure(state=NORMAL)
        zoomin.configure(state=NORMAL)
        mapfilebutton.configure(state=NORMAL)
        predictbutton.configure(state=NORMAL)
        reversebutton.configure(state=DISABLED)
        predictbutton.configure(state=DISABLED)
        predictlabels=None
        confidence=None
        init_canvas(filename)
        slider.unbind('<ButtonRelease-1>')
        hasMap=False
        hasGrid=False
        hasPred=False

def Open_Map():
    mapfile=filedialog.askopenfilename()
    if '.csv' not in mapfile:
        messagebox.showerror('Error',message='Map file should be a csv file.')
        return
    else:
        import csv
        rows=[]
        transrows=[]
        if os.name=='nt':
            mapfile=r'%s' % mapfile
        with open(mapfile,'r',encoding='utf-8-sig') as f:
            csvreader=csv.reader(f)
            for row in csvreader:
                if len(row)!=0:
                    rows.append(row)
            rows.pop(0)
            totalgrid=len(rows)
            for i in range(totalgrid):
                temprow=[int(rows[i][e]) for e in range(4)]
                transrows.append(temprow)
                # print(temprow)
        arrayrow=np.array(transrows)
        print(arrayrow.shape)
        if arrayrow.shape[1]!=4:
            messagebox.showerror('Error', message='Incorrect contents to open. \n Contents shape is:'
                                                  +str(arrayrow.shape[0])+'x'+str(arrayrow.shape[1]))
            return
        rownum=max(arrayrow[:,1])+1
        colnum=max(arrayrow[:,2])+1
        infected=np.where(arrayrow[:,3]==1)
        infected=list(infected)[0]
        infected=[ele for ele in infected]
        print(totalgrid,rownum,colnum,infected)
        global hasGrid,rowentry,colentry,hasMap
        global reversebutton,predictbutton,gridbutton
        hasGrid=False
        hasMap=True
        rowentry.configure(state=NORMAL)
        rowentry.delete(0,END)
        rowentry.insert(END,rownum)
        rowentry.configure(state=DISABLED)
        colentry.configure(state=NORMAL)
        colentry.delete(0,END)
        colentry.insert(END,colnum)
        colentry.configure(state=DISABLED)
        reversebutton.configure(state=DISABLED)
        predictbutton.configure(state=NORMAL)
        gridbutton.configure(state=DISABLED)
        zoom.resetlabels()
        setGrid(resetimage=True)
        zoom.labelmulti(infected)








def setGrid(resetimage=False):
    global gridimg,hasGrid,reversebutton,gridbutton
    global rownum, colnum, confidence,slider
    print('hasGrid',hasGrid)
    if resetimage==True:
        rownum=int(rowentry.get())
        colnum=int(colentry.get())
        print(resetimage,rownum,colnum)
        confidence = None
        if proc_mode[proc_name].get()=='0':
            slider.state(["disabled"])
        slider.unbind('<Leave>')
        rgbwidth, rgbheight = RGBimg.size
        row_stepsize = int(rgbheight / rownum)
        col_stepsize = int(rgbwidth / colnum)
        gridimg = RGBimg.copy()
        draw = ImageDraw.Draw(gridimg)
        row_start = 0
        row_end = rgbheight
        col_start = 0
        col_end = rgbwidth
        for col in range(0, col_end, col_stepsize):
            line = ((col, row_start), (col, row_end))
            draw.line(line, fill='white', width=5)

        for row in range(0, row_end, row_stepsize):
            line = ((col_start, row), (col_end, row))
            draw.line(line, fill='white', width=5)

        del draw
        # gridimg.show()
        zoom.changeimage(gridimg, rownum, colnum, False)
        hasGrid = True
        return
    if hasGrid==False:
        try:
            temprownum=int(rowentry.get())
            tempcolnum=int(colentry.get())
        except:
            return
        if rownum != 0 and (rownum != temprownum or colnum != tempcolnum):
            res = messagebox.askquestion('Warning', 'Changes happened to rows or cols. Do you want to continue?')
            if res == 'no':
                return
            if res=='yes':
                zoom.resetlabels()

        rownum=temprownum
        colnum=tempcolnum
        confidence=None
        if proc_mode[proc_name].get()=='0':
            slider.state(["disabled"])
        slider.unbind('<Leave>')
        rgbwidth,rgbheight=RGBimg.size
        row_stepsize=int(rgbheight/rownum)
        col_stepsize=int(rgbwidth/colnum)
        gridimg=RGBimg.copy()
        draw=ImageDraw.Draw(gridimg)
        row_start=0
        row_end=rgbheight
        col_start=0
        col_end=rgbwidth
        for col in range(0,col_end,col_stepsize):
            line=((col,row_start),(col,row_end))
            draw.line(line,fill='white',width=5)

        for row in range(0,row_end,row_stepsize):
            line=((col_start,row),(col_end,row))
            draw.line(line,fill='white',width=5)

        del draw
        # gridimg.show()
        zoom.changeimage(gridimg,rownum,colnum,hasGrid)
        hasGrid=True
        if proc_mode[proc_name].get()=='0':
            reversebutton.configure(state=NORMAL)
            predictbutton.configure(state=NORMAL)
    else:
        zoom.changeimage(gridimg,0,0,hasGrid)
        hasGrid=False
        reversebutton.configure(state=DISABLED)
        predictbutton.configure(state=DISABLED)

def setReverse():
    zoom.labelall()

def printimageexport():
    print(imageexport.get())

def exportopts():
    global exportoption,imageexport,csvname,e1
    exportoption=StringVar()
    imageexport=IntVar()
    exportoption.set('P')
    opt_window=Toplevel()
    opt_window.geometry('300x150')
    opt_window.title('Export options')
    # optionframe=Frame(opt_window)
    # optionframe.pack()
    checkframe=Frame(opt_window)
    checkframe.pack()
    # radiostyle=ttk.Style()
    # radiostyle.configure('R.TRadiobutton',foreground='White')
    # Radiobutton(optionframe,text='Export Prediction',variable=exportoption,value='P').pack(side=LEFT,padx=10,pady=10)
    # Radiobutton(optionframe,text='Export Current',variable=exportoption,value='C').pack(side=LEFT,padx=10,pady=10)
    Checkbutton(checkframe,text='Export Grid Pictures',variable=imageexport,command=printimageexport).pack(padx=10,pady=10)
    head_tail = os.path.split(filename)
    originfile, extension = os.path.splitext(head_tail[1])
    csvname = originfile + '_labeloutput_' + 'confidthres=' + str(slider.get()) + '.csv'
    intro = Label(checkframe, text='Out put csv file name:')
    intro.pack()
    e1 = Entry(checkframe)
    e1.pack()
    e1.insert(END, csvname)
    Button(checkframe,text='Export!',command=lambda: implementexport(opt_window)).pack(padx=10,pady=10)
    opt_window.transient(root)
    opt_window.grab_set()



def implementexport(popup):
    outpath=filedialog.askdirectory()
    root.update()
    res=zoom.output()
    npimage=res['npimage']
    labelimage=res['labeledimage']
    infectedlist=res['infectedlist']
    import csv
    head_tail=os.path.split(filename)
    originfile,extension=os.path.splitext(head_tail[1])
    # if exportoption.get()=='P':
    #     outputcsv=outpath+'/'+originfile+'_prediction.csv'
    #     headline=['index','row','col','prediction']
    # if exportoption.get()=='C':
    outputcsv=outpath+'/'+e1.get()
    headline=['index','row','col','label','prediction','confidence']
    with open(outputcsv,mode='w') as f:
        csvwriter=csv.writer(f,lineterminator='\n')
        csvwriter.writerow(headline)
        rownum=int(rowentry.get())
        colnum=int(colentry.get())
        gridnum=rownum*colnum
        outputimg=labelimage.copy()
        draw=ImageDraw.Draw(outputimg)
        for i in range(gridnum):
            index=i+1
            row=int(i/colnum)
            col=i%colnum
            locs=np.where(npimage==index)
            x0=min(locs[1])
            y0=min(locs[0])
            x1=max(locs[1])
            y1=max(locs[0])
            if int(imageexport.get())==1:
                cropimage=RGBimg.crop((x0,y0,x1,y1))
                cropimage.save(outpath+'/'+originfile+'_crop_'+str(index)+'.png','PNG')
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
            label=infectedlist[i]
            if confidence!=None:
                pred_label= 1 if list(confidence)[i]>=float(slider.get()) else 0
                confidvalue=list(confidence)[i]
                content=[index,row,col,label,pred_label,confidvalue]
            else:
                content = [index, row, col, label,0,0]
            csvwriter.writerow(content)
            print(index)
        del draw
        f.close()
    outputimg.save(outpath+'/'+originfile+'_gridimg'+'.png','PNG')
    messagebox.showinfo('Output Done!',message='Results are output to'+outpath)
    popup.destroy()


def export():
    if proc_mode[proc_name].get()=='1':
        rooster_batch.batch_exportpath()
        if hasGrid==True:
            global predictbutton
            predictbutton.configure(state=NORMAL)
        return
    if hasGrid==False:
        return
    exportopts()
    try:
        print(exportoption.get(),imageexport.get())
    except:
        return

def changeconfidencerange(event):
    # newconfid=scaleval.get()
    newconfid=slider.get()
    print(newconfid)
    # zoom.changeconfidance(newconfid[0],newconfid[1])
    zoom.changeconfidance(newconfid)

def prediction():
    global predictlabels,confidence,hasPred
    global slider
    if confidence is not None:
        zoom.showcomparison(confidence,hasPred)
        hasPred=-hasPred
        return
    dlparameter=filedialog.askopenfilename()
    root.update()
    if dlparameter!='':
        if '.pth' not in dlparameter:
            messagebox.showerror('Document type error',message='Please load weight document ends with .pth')
            return
        tail=dlparameter.find('_')
        dlmodel=dlparameter[:tail]
        dlinput={}  #input for deep learning model prediction
        # global rownum,colnum
        rownumdict={'row':rownum}
        colnumdict={'col':colnum}
        imgpath={'imagepath':filename}
        dlparapath={'weight':dlparameter}
        dlmodelvalue={'model':dlmodel}
        dlinput.update(rownumdict)
        dlinput.update(colnumdict)
        dlinput.update(imgpath)
        dlinput.update(dlparapath)
        dlinput.update(dlmodelvalue)
        if proc_mode[proc_name].get()=='1':
            rooster_batch.batch_process(dlinput,slider.get())
            return
        confidence = predictionCNN(dlinput)
        #dlinput is the arguments for deep learning model prediction
        #return of deep learning model should be probability of being diseases
    else:
        import random
        gridnum = int(rowentry.get()) * int(colentry.get())
        randomlabel=(np.array(random.sample(range(0,gridnum),int(gridnum/3))),)
        # predictlabels=np.array([0 for i in range(gridnum)])
        # predictlabels[randomlabel]=1
        confidence=list(np.random.uniform(0.00,1.00,gridnum))
    print(len(confidence))

    zoom.showcomparison(list(confidence),hasPred)
    hasPred=-hasPred

    slider.set(0.50)
    slider.state(["!disabled"])
    slider.bind('<ButtonRelease-1>',changeconfidencerange)
    # slider.state(NORMAL,changeconfidencerange)
    # global hasGrid
    # hasGrid=False
    # setGrid()
    # zoom.labelmulti(randomlabel)




# ----Display-----
display_fr=Frame(root,width=screenwidth,height=screenheight)
bottomframe=Frame(root)
bottomframe.pack(side=BOTTOM)
display_fr.pack(anchor='center')

imageframe=LabelFrame(display_fr,bd=0)
imageframe.pack()

w=760
l=640

panelA=Canvas(imageframe,width=w,height=l,bg='black')
panelA.grid(padx=20,pady=20)

proc_name='batch_mode'
proc_mode={proc_name:Variable()}
proc_mode[proc_name].set('0')
proc_but=Checkbutton(bottomframe,text=proc_name,variable=proc_mode[proc_name])
proc_but.pack(side=LEFT,padx=20,pady=5)


buttondisplay=LabelFrame(bottomframe,bd=0)
buttondisplay.config(cursor='hand2')
buttondisplay.pack(side=LEFT)

labeloptframe=LabelFrame(bottomframe,bd=0)
labeloptframe.config(cursor='hand2')
labeloptframe.pack(side=LEFT)

gridoptframe=LabelFrame(bottomframe,bd=0)
gridoptframe.config(cursor='hand2')
gridoptframe.pack(side=LEFT)

gridbuttondisplay=LabelFrame(bottomframe,bd=0)
gridbuttondisplay.config(cursor='hand2')
gridbuttondisplay.pack(side=LEFT)

confidframe=LabelFrame(bottomframe,bd=0)
confidframe.config(cursor='hand2')
confidframe.pack(side=LEFT)

outputframe=LabelFrame(bottomframe,bd=0)
outputframe.config(cursor='hand2')
outputframe.pack(side=LEFT)

# ------button opts---------

openfilebutton=Button(buttondisplay,text='Image',cursor='hand2',command=Open_Multifile)
openfilebutton.pack(side=LEFT,padx=20,pady=5)
mapfilebutton=Button(buttondisplay,text='Map',cursor='hand2',command=Open_Map)
mapfilebutton.pack(side=LEFT,padx=20,pady=5)
mapfilebutton.configure(state=DISABLED)


# zoombar=Scale(labeloptframe,from_=50,to=150,orient=HORIZONTAL,command=zoomimage,variable=scaleval)
# scaleval.set(100)
# zoombar.pack(side=LEFT,padx=5)
# zoombar.configure(state=DISABLED,repeatinterval=10)
zoomin=Button(labeloptframe,text=' + ',cursor='hand2',command=lambda: zoomimage(1))
zoomin.pack(side=LEFT)
zoomin.configure(state=DISABLED)
zoomout=Button(labeloptframe,text=' - ',cursor='hand2',command=lambda: zoomimage(0))
zoomout.pack(side=LEFT)
zoomout.configure(state=DISABLED)

rowdef=Label(gridoptframe,text='Row')
rowdef.pack(side=LEFT)
rowentry=Entry(gridoptframe,width=5)
rowentry.insert(END,10)
rowentry.pack(side=LEFT,padx=2)

coldef=Label(gridoptframe,text='Col')
coldef.pack(side=LEFT)
colentry=Entry(gridoptframe,width=5)
colentry.insert(END,10)
colentry.pack(side=LEFT,padx=2)

for widget in gridoptframe.winfo_children():
    widget.config(state=DISABLED)

gridbutton=Button(gridbuttondisplay,text='Grid!',cursor='hand2',command=setGrid)
gridbutton.pack(side=LEFT,padx=10)
gridbutton.configure(state=DISABLED)
reversebutton=Button(gridbuttondisplay,text='Reverse',cursor='hand2',command=setReverse)
reversebutton.pack(side=LEFT,padx=10)
reversebutton.configure(state=DISABLED)

predictbutton=Button(gridbuttondisplay,text='Predict',cursor='hand2',command=prediction)
predictbutton.pack(side=LEFT,padx=10)
predictbutton.configure(state=DISABLED)
confidbutton=Label(confidframe,text='Threshold',cursor='hand2')
confidbutton.pack(side=TOP,padx=10)
# confidbutton.configure(state=DISABLED)
# from tkSliderWidget import Slider
# slider=Slider(confidframe,width=100,height=30,min_val=0.50,max_val=1.00,init_lis=[0.75,0.95],show_value=False)
# slider.pack(side=BOTTOM)
# slider.state(DISABLED,changeconfidencerange)
slider=ttk.Scale(confidframe,from_=0.0,to=1.00,orient=HORIZONTAL)
slider.set(0.50)
slider.pack(side=BOTTOM)
slider.state(["disabled"])

exportbutton=Button(outputframe,text='Export',cursor='hand2',command=export)
exportbutton.pack(side=LEFT,padx=10)
exportbutton.configure(state=DISABLED)

root.mainloop()
