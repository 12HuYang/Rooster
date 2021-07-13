# -*- coding: utf-8 -*-
# Advanced zoom example. Like in Google Maps.
# It zooms only a tile, but not the whole image. So the zoomed tile occupies
# constant memory and not crams it with a huge resized image for the large zooms.
import random
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import tkinter.filedialog as filedialog
import cv2
import numpy as np

class AutoScrollbar(ttk.Scrollbar):
    ''' A scrollbar that hides itself if it's not needed.
        Works only if you use the grid geometry manager '''
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with this widget')

    def place(self, **kw):
        raise tk.TclError('Cannot use place with this widget')

class Zoom_Advanced(ttk.Frame):
    ''' Advanced zoom of the image '''
    def __init__(self, mainframe, canvas,path,rownum,colnum,canvasw,canvash):
        ''' Initialize the main Frame '''
        ttk.Frame.__init__(self, master=mainframe)
        # self.master.title('Zoom with mouse wheel')
        # Vertical and horizontal scrollbars for canvas
        vbar = AutoScrollbar(self.master, orient='vertical')
        hbar = AutoScrollbar(self.master, orient='horizontal')
        vbar.grid(row=0, column=1, sticky='ns')
        hbar.grid(row=1, column=0, sticky='we')
        # Create canvas and put image on it
        self.canvasw=canvasw
        self.canvash=canvash
        self.canvas = canvas
        self.canvas.configure(xscrollcommand=hbar.set,yscrollcommand=vbar.set)
        # tk.Canvas(self.master, highlightthickness=0,
        #                         xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.configure(width=canvasw,height=canvash)
        self.canvas.update()  # wait till canvas is created
        vbar.configure(command=self.scroll_y)  # bind scrollbars to the canvas
        hbar.configure(command=self.scroll_x)
        # Make the canvas expandable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.move_from)
        self.canvas.bind('<B1-Motion>',     self.move_to)
        # self.canvas.bind('<MouseWheel>', self.wheel)  # with Windows and MacOS, but not Linux
        self.canvas.bind('<Double-Button-1>',   self.labelimage)  # only with Linux, wheel scroll down
        # self.canvas.bind('<Button-4>',   self.wheel)  # only with Linux, wheel scroll up
        # self.image = Image.open(path)  # open image
        # imagearray=cv2.imread(path,flags=cv2.IMREAD_ANYCOLOR)
        # h,w,c=np.shape(imagearray)
        # RGBfile=cv2.cvtColor(imagearray,cv2.COLOR_BGR2RGB)
        self.path=path
        self.image=Image.open(self.path)
        self.npimage=np.zeros((self.image.height,self.image.width))
        # self.height, self.width,_ = np.shape(self.image)
        self.width, self.height = self.image.size
        print(self.width,self.height)
        self.imscale = 1.0  # scale for the canvaas image
        self.delta = 1.2  # zoom magnitude
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        # Plot some optional random rectangles for the test purposes
        # minsize, maxsize, number = 5, 20, 10
        # for n in range(number):
        #     x0 = random.randint(0, self.width - maxsize)
        #     y0 = random.randint(0, self.height - maxsize)
        #     x1 = x0 + random.randint(minsize, maxsize)
        #     y1 = y0 + random.randint(minsize, maxsize)
        #     color = ('red', 'orange', 'yellow', 'green', 'blue')[random.randint(0, 4)]
        #     self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, activefill='black')

        self.rownum=rownum
        self.colnum=colnum
        self.infectlist=[]
        self.getgrid=0
        # self.updatenpimage()

        # self.show_image()
        scale=max(self.canvasw/self.width,self.canvash/self.width)
        print('scale',scale)
        self.imscale=scale
        self.canvas.scale('all', 0, 0, scale, scale)  # rescale all canvas objects
        self.show_image()

    def updatenpimage(self):
        gridnum=self.rownum*self.colnum
        row_stepsize=int(self.height/self.rownum)
        col_stepsize=int(self.width/self.colnum)
        print(gridnum,row_stepsize,col_stepsize)
        self.npimage=np.zeros((self.image.height,self.image.width))
        for i in range(gridnum):
            c=i%self.colnum
            r=int(i/self.colnum)
            print(r,c)
            self.npimage[r*row_stepsize:(r+1)*row_stepsize,c*col_stepsize:(c+1)*col_stepsize]=i+1
        print(self.npimage)


    def scroll_y(self, *args, **kwargs):
        ''' Scroll canvas vertically and redraw the image '''
        self.canvas.yview(*args, **kwargs)  # scroll vertically
        self.show_image()  # redraw the image

    def scroll_x(self, *args, **kwargs):
        ''' Scroll canvas horizontally and redraw the image '''
        self.canvas.xview(*args, **kwargs)  # scroll horizontally
        self.show_image()  # redraw the image

    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.zoomx=event.x
        self.zoomy=event.y
        self.show_image()  # redraw the image

    def wheel(self, opt):
        ''' Zoom with mouse wheel '''
        # x = self.canvas.canvasx(event.x)
        # y = self.canvas.canvasy(event.y)
        # x=0
        # y=0
        try:
            x=self.zoomx
            y=self.zoomy
        except:
            bbox = self.canvas.bbox(self.container)  # get image area
            x=int((bbox[2]-bbox[0])/2)
            y=int((bbox[3]-bbox[1])/2)
        # if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
        # else: return  # zoom only inside image area


        scale = 1.0
        # # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if opt==0:  # scroll down
            i = min(self.width, self.height)
            if int(i * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.delta
            scale        /= self.delta
        if opt==1:
        # if event.num == 4 or event.delta == 120:  # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.delta
            scale        *= self.delta

        # x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        # y1 = max(bbox2[1] - bbox1[1], 0)
        # x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
        # y2 = min(bbox2[3], bbox1[3]) - bbox1[1]

        # if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
        #     x = min(int(x2 / self.imscale), self.width)   # sometimes it is larger on 1 pixel...
        #     y = min(int(y2 / self.imscale), self.height)  # ...and sometimes not
        #     # imagearray=self.image.astype('uint8')
        #     # self.image=Image.fromarray(self.image)
        #


        print(x,y,scale)

        self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.show_image()

    def show_image(self, event=None):
        ''' Show image on the Canvas '''
        bbox1 = self.canvas.bbox(self.container)  # get image area
        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
        bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                 self.canvas.canvasy(0),
                 self.canvas.canvasx(self.canvas.winfo_width()),
                 self.canvas.canvasy(self.canvas.winfo_height()))
        bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),  # get scroll region box
                max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3])]
        if bbox[0] == bbox2[0] and bbox[2] == bbox2[2]:  # whole image in the visible area
            bbox[0] = bbox1[0]
            bbox[2] = bbox1[2]
        if bbox[1] == bbox2[1] and bbox[3] == bbox2[3]:  # whole image in the visible area
            bbox[1] = bbox1[1]
            bbox[3] = bbox1[3]
        self.canvas.configure(scrollregion=bbox)  # set scroll region
        x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(bbox2[1] - bbox1[1], 0)
        x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
        y2 = min(bbox2[3], bbox1[3]) - bbox1[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            x = min(int(x2 / self.imscale), self.width)   # sometimes it is larger on 1 pixel...
            y = min(int(y2 / self.imscale), self.height)  # ...and sometimes not
            # imagearray=self.image.astype('uint8')
            # self.image=Image.fromarray(self.image)
            image = self.image.crop((int(x1 / self.imscale), int(y1 / self.imscale), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
            imageid = self.canvas.create_image(max(bbox2[0], bbox1[0]), max(bbox2[1], bbox1[1]),image=imagetk,
                                               anchor='nw')
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

    def changeimage(self,newimage,rownum,colnum,hasGrid):
        if hasGrid==False:
            self.rownum=rownum
            self.colnum=colnum
            # newimage_width,newimage_height=newimage.size
            self.image=newimage #.resize((int(newimage_width/2),int(newimage_height/2)))
            self.width, self.height = self.image.size
            print(self.width,self.height)
            self.infectlist=[]
            self.getgrid=1
            self.updatenpimage()
            self.show_image()
        else:
            self.image=Image.open(self.path)
            print(self.width,self.height)
            self.show_image()
            self.getgrid=0


    def addbars(self,locs):
        x0=min(locs[1])
        y0=min(locs[0])
        x1=max(locs[1])
        y1=max(locs[0])
        draw=ImageDraw.Draw(self.image)
        draw.line(((x0,y0),(x1,y0)),fill='red',width=5) #draw up red line
        draw.line(((x0,y0),(x0,y1)),fill='red',width=5) #draw left red line
        # self.show_image()


    def rmbars(self,locs):
        x0=min(locs[1])
        y0=min(locs[0])
        x1=max(locs[1])
        y1=max(locs[0])
        draw=ImageDraw.Draw(self.image)
        draw.line(((x0,y0),(x1,y0)),fill='white',width=5) #draw up red line
        draw.line(((x0,y0),(x0,y1)),fill='white',width=5) #draw left red line
        # self.show_image()

    def labelimage(self,event):
        if self.getgrid==0:
            return
        x = int(self.canvas.canvasx(event.x))
        y = int(self.canvas.canvasy(event.y))
        bbox = self.canvas.bbox(self.container)
        print(x,y)
        print(bbox)

        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
        else:
            print('outsie image area')
            return  # label only inside image area
        # x=int(x*self.imscale)
        # y=int(y*self.imscale)
        # print(x,y,self.imscale)
        x=x-bbox[0]
        y=y-bbox[1]
        mirrornpimage=self.npimage.copy()
        mirrornpimage=cv2.resize(mirrornpimage,(int(self.width*self.imscale),int(self.height*self.imscale)),interpolation=cv2.INTER_LINEAR)
        # mirrornpimage=cv2.resize(mirrornpimage,(bbox[2]-bbox[0],bbox[3]-bbox[1]),interpolation=cv2.INTER_LINEAR)
        # infectnum=self.npimage[y,x]
        infectnum=mirrornpimage[y,x]
        print(infectnum)
        if infectnum!=0:
            locs=np.where(self.npimage==int(infectnum))
            print(locs)
            if infectnum not in self.infectlist:
                self.infectlist.append(infectnum)
                self.addbars(locs)
            else:
                self.infectlist.remove(infectnum)
                self.rmbars(locs)
            print(len(self.infectlist))
        self.show_image()

    def labelmulti(self,infectlist):
        self.infectlist=infectlist.copy()
        for infectnum in self.infectlist:
            print(infectnum)
            if infectnum!=0:
                locs=np.where(self.npimage==int(infectnum))
                # print(locs)
                self.addbars(locs)
        self.show_image()

    def labelall(self):
        reverseinfect=list(np.arange(1,self.rownum*self.colnum+1))
        self.uninfect=[]
        for ele in self.infectlist:
            reverseinfect.remove(ele)
            self.uninfect.append(ele)
        self.infectlist=reverseinfect.copy()
        for infectnum in self.infectlist:
            print(infectnum)
            if infectnum!=0:
                locs=np.where(self.npimage==int(infectnum))
                # print(locs)
                self.addbars(locs)
        for uninfectnum in self.uninfect:
            print(uninfectnum)
            if uninfectnum!=0:
                locs=np.where(self.npimage==int(uninfectnum))
                # print(locs)
                self.rmbars(locs)
        self.show_image()

    def output(self):
        res={}
        res.update({'npimage':self.npimage})
        res.update({'labeledimage':self.image})
        res.update({'infectedlist':self.infectlist})
        return res







