import cv2

from matplotlib import pyplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LinearSegmentedColormap,Normalize
from matplotlib.cm import ScalarMappable

class Plot_matlab:
  def __init__(self,canvas,title):
    self.figure,self.axes=pyplot.subplots()
    self.figure_canvas_agg=FigureCanvasTkAgg(self.figure,canvas)
    self.figure_canvas_agg.get_tk_widget().pack(side='top',fill='both',expand=1)
    self.axes.set_title(title)
    self.axes.get_xaxis().set_visible(False)
    self.axes.get_yaxis().set_visible(False)

  def custom_colour_map(self,colours):
    return(LinearSegmentedColormap.from_list("mycmap",colours))

  def set_colour_map(self,cmap,range):
    self.cmap=cmap
    self.range=range
    self.figure.colorbar(ScalarMappable(norm=Normalize(vmin=self.range[0],vmax=self.range[1]),cmap=self.cmap),ax=self.axes)
    self.axes.pcolor([[0]],cmap=self.cmap,vmin=self.range[0],vmax=self.range[1])
    self.figure.tight_layout()
    
  def canvas_redraw(self,frame):
    # redraw by matplotlib using 0.0166~0.0219s
    self.axes.pcolor(frame,cmap=self.cmap,vmin=self.range[0],vmax=self.range[1])
    self.figure_canvas_agg.draw()


class Plot_cv:
  def __init__(self,canvas,resolution):
    self.canvas=canvas
    self.resolution=resolution

  def custom_colour_map(self,colours):
    pass

  def set_colour_map(self,cmap,range):
    pass

  def draw_rectangle(self,frame,pt1,pt2,colour,thickness=5):
    cv2.rectangle(frame,pt1,pt2,colour,thickness)
    return(frame)

  def canvas_redraw(self,frame):
    # output=cv2.resize(src=frame,dsize=self.resolution,interpolation=cv2.INTER_NEAREST)
    # self.draw_rectangle()
    self.canvas.update(data=cv2.imencode(ext='.png',img=frame)[1].tobytes())
