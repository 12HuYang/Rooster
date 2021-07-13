from tkinter import *
from tkinter import ttk
import tkinter.filedialog as filedialog
from tkinter import messagebox
from PIL import Image,ImageDraw,ImageFont
from PIL import ImageTk,ImageGrab
import cv2
import numpy as np
import os

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
scaleval=IntVar()
RGBbands=None
RGBimg=None
gridimg=None
zoom=None
hasGrid=False


# ------functions-----

def init_canvas(path):
    import zoom_example
    global panelA,zoom
    rownum=int(rowentry.get())
    colnum=int(colentry.get())
    zoom=zoom_example.Zoom_Advanced(imageframe,panelA,path,rownum,colnum,1440,900)



def Open_File():
    global RGBbands,RGBimg
    try:
        Filersc=cv2.imread(filename,flags=cv2.IMREAD_ANYCOLOR)
        h,w,c=np.shape(Filersc)
        print('image size:',h,w)
        RGBbands=cv2.cvtColor(Filersc,cv2.COLOR_BGR2RGB)
        RGBimg=Image.open(filename)
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
    global gridbutton,rowentry,colentry,exportbutton,filename,zoombar,mapfilebutton
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
        init_canvas(filename)

def Open_Map():
    mapfile=filedialog.askopenfilename()
    if '.csv' not in mapfile:
        messagebox.showerror('Error',message='Map file should be a csv file.')
        return
    else:
        import csv
        rows=[]
        transrows=[]
        with open(mapfile,'r',encoding='utf-8-sig') as f:
            csvreader=csv.reader(f)
            for row in csvreader:
                rows.append(row)
            rows.pop(0)
            totalgrid=len(rows)
            for i in range(totalgrid):
                temprow=[int(ele) for ele in rows[i]]
                transrows.append(temprow)
                # print(temprow)
        arrayrow=np.array(transrows)
        rownum=max(arrayrow[:,1])+1
        colnum=max(arrayrow[:,2])+1
        infected=np.where(arrayrow[:,3]==1)
        infected=list(infected)[0]+1
        print(totalgrid,rownum,colnum,infected)
        global hasGrid,rowentry,colentry
        hasGrid=False
        rowentry.delete(0,END)
        rowentry.insert(END,rownum)
        colentry.delete(0,END)
        colentry.insert(END,colnum)
        setGrid()
        zoom.labelmulti(infected)








def setGrid():
    global gridimg,hasGrid,reversebutton
    if hasGrid==False:
        try:
            rownum=int(rowentry.get())
            colnum=int(colentry.get())
        except:
            return
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
        reversebutton.configure(state=NORMAL)

    else:
        zoom.changeimage(gridimg,0,0,hasGrid)
        hasGrid=False
        reversebutton.configure(state=DISABLED)

def setReverse():
    zoom.labelall()

def export():
    outpath=filedialog.askdirectory()
    res=zoom.output()
    npimage=res['npimage']
    labelimage=res['labeledimage']
    infectedlist=res['infectedlist']
    import csv
    head_tail=os.path.split(filename)
    originfile,extension=os.path.splitext(head_tail[1])
    outputcsv=outpath+'/'+originfile+'_labeloutput.csv'
    with open(outputcsv,mode='w') as f:
        csvwriter=csv.writer(f)
        headline=['index','row','col','label']
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
            label='0' if index not in infectedlist else '1'
            content=[index,row,col,label]
            csvwriter.writerow(content)
            print(index)
        del draw
        f.close()
    outputimg.save(outpath+'/'+originfile+'_gridimg'+'.png','PNG')
    messagebox.showinfo('Output Done!',message='Results are output to'+outpath)


def prediction():
    gridnum=int(rowentry.get())*int(colentry.get())
    import random
    randomlabel=random.sample(range(1,gridnum+1),int(gridnum/2))
    print(len(randomlabel),randomlabel)
    global hasGrid
    hasGrid=False
    setGrid()
    zoom.labelmulti(randomlabel)




# ----Display-----
display_fr=Frame(root,width=screenwidth,height=screenheight)
bottomframe=Frame(root)
bottomframe.pack(side=BOTTOM)
display_fr.pack(side=LEFT)

imageframe=LabelFrame(display_fr,bd=0)
imageframe.pack()

w=760
l=640

panelA=Canvas(imageframe,width=w,height=l,bg='black')
panelA.grid(padx=20,pady=20)

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
confidbutton=Button(confidframe,text='Confidence',cursor='hand2')
confidbutton.pack(side=TOP,padx=10)
confidbutton.configure(state=DISABLED)
from tkSliderWidget import Slider
slider=Slider(confidframe,width=100,height=30,min_val=0.50,max_val=1.00,init_lis=[0.75,0.95],show_value=True)
slider.pack(side=BOTTOM)
slider.state(DISABLED)

exportbutton=Button(outputframe,text='Export',cursor='hand2',command=export)
exportbutton.pack(side=LEFT,padx=10)
exportbutton.configure(state=DISABLED)

root.mainloop()