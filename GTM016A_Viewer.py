import PySimpleGUI as sg
import numpy as np
import sys,os
import cv2
import time
from plotter import *
from pl23c3 import Pl23c3

def resource_path(relative_path):
  """ Get absolute path to resource, works for dev and for PyInstaller """
  try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = sys._MEIPASS
  except Exception:
    base_path = os.path.abspath(".")
  return os.path.join(base_path, relative_path)

########################################
# Var
########################################
param={
  "WINDOW_TITLE":"GTM016 Viewer",
  'VERSION':'1.0',
  'MODIFY_DATE':'24 Nov, 2021',
  'ICON_WINDOW':resource_path('tools.ico'),
  'BRANCH_LIST':['main','intel','sales'],
  'BRANCH_SELECTED':'main',
  'DLL_ARCHITECTURE':'./HidDeviceSdk_x64.dll' if os.environ['PROCESSOR_ARCHITECTURE'].endswith('64') else './HidDeviceSdk_x86.dll',
  'FRAME_SIZE':(16,16),
  'DISPLAY_SIZE':(480,480),
  'DISPLAY_RESIZE':(30,30),
  'APP_STATUS_LIST':['stop','start'],
  'app_status':'stop',
  'DISP_STATUS_LIST':['off','on'],
  'disp_status':'off',
  'DATA_TYPE_LIST':[100,200,210,220],
  'SENSOR_GAIN_LIST':[1,2,4,8],
  'SENSOR_IPIX_LIST':[5,10,15,20,25,30,35,40],
  'AVG_SIZE':8,
  'MAXIMUM_TEMPERATURE':100,
  'RESOLUTION_TEMPERATURE':1,
}

draw_MinMax=0

click_pos=[(0,0),0]
temp_area_out=np.zeros(param['FRAME_SIZE'],dtype=np.uint16)
temp_area_buffer=np.zeros((param['FRAME_SIZE']),dtype=np.uint32)
temp_area_pointer=0
reconnect_timer=0
last_time=0

board_temp=2500

########################################
# Sub func
########################################
def TestResult():
  visable=True if param['BRANCH_SELECTED']==param['BRANCH_LIST'][0] else False
  return(
    [
      [
        sg.Input(default_text='Device connected',size=(30,1),disabled=True,justification='center',key='__SCON__',expand_x=True)
      ],
      [
        sg.Text(text='Image stream',size=(10,1)),
        sg.Button(button_text='START',size=(5,1)),
        sg.Button(button_text='Calibrate',size=(7,1),visible=visable,expand_x=True)
      ],
      [
        sg.Button(button_text='Display Maximum',size=(26,1),key='__DMIMA__',expand_x=True)
      ],
      [
        sg.Text(text='Interpolation:',size=(10,1)),
        sg.Combo(values=['OFF','LINEAR_64'],default_value='LINEAR_64',size=(15,1),key='__INTERP__',expand_x=True)
      ],
      [
        sg.Text(text='Max',size=(10,1)),
        sg.Slider(
          range=(1,param['MAXIMUM_TEMPERATURE']),
          default_value=40,
          resolution=param['RESOLUTION_TEMPERATURE'],
          orientation='horizontal',
          enable_events=True,
          key='__MAX_TEMP__'
        ),
      ],
      [
        sg.Text(text='Min',size=(10,1)),
        sg.Slider(
          range=(0,param['MAXIMUM_TEMPERATURE']-1),
          default_value=20,
          resolution=param['RESOLUTION_TEMPERATURE'],
          orientation='horizontal',
          enable_events=True,
          key='__MIN_TEMP__'
        ),
      ],
      # [
      #   sg.Text(text='Disp contrast',size=(10,1)),
      #   sg.Combo(values=[5,10,15,20],default_value=10,size=(15,1),key='__DISP__',expand_x=True),
      # ],
      [
        sg.Text(text='FPS',size=(10,1)),
        sg.Text(text='0',size=(10,1),key='__FPS__',expand_x=True)
      ],
      [
        sg.Text(text='Cursor Temp.',size=(10,1),text_color='lime'),
        sg.Text(text='0',size=(4,1),font=('Helvetica','20'),text_color='lime',key='__CTMP__',expand_x=True),
        sg.Text(text='°C',size=(2,1),font=('Helvetica','20'),text_color='lime'),
      ],
      # [
      #   sg.Text(text='Min Temp.',size=(10,1),text_color='blue'),
      #   sg.Text(text='0',size=(4,1),font=('Helvetica','20'),text_color='blue',key='__MINT__',expand_x=True),
      #   sg.Text(text='°C',size=(2,1),font=('Helvetica','20'),text_color='blue'),
      # ],
      [
        sg.Text(text='Max Temp.',size=(10,1),text_color='red'),
        sg.Text(text='0',size=(4,1),font=('Helvetica','20'),text_color='red',key='__MAXT__',expand_x=True),
        sg.Text(text='°C',size=(2,1),font=('Helvetica','20'),text_color='red'),
      ],
      [
        sg.Text(text='')
      ],
      [
        sg.Button(button_text='EXIT',size=(26,1),expand_x=True)
      ],
    ]
  )

def layout_ui():
  return(
    [
      [
        sg.Image(background_color='black',size=param['DISPLAY_SIZE'],key='__CANVAS__'),
        sg.Frame(title='',layout=[
            [
              sg.Frame(title='Test Result',layout=TestResult())
            ],
          ],
          border_width=0
        )
      ],
    ]
  )

def event_handler(window,event):
  if event=='START':
    if param['app_status']==param['APP_STATUS_LIST'][0]:
      param['app_status']=param['APP_STATUS_LIST'][1]
      window['START'].update('STOP')
    else:
      param['app_status']=param['APP_STATUS_LIST'][0]
      window['START'].update('START')
  if event=='OFF':
    if param['disp_status']==param['DISP_STATUS_LIST'][0]:
      param['disp_status']=param['DISP_STATUS_LIST'][1]
      window['OFF'].update('ON')
    else:
      param['disp_status']=param['DISP_STATUS_LIST'][0]
      window['OFF'].update('OFF')
  if event=='__CANVAS__click':
    pos_x=window['__CANVAS__'].user_bind_event.x
    pos_y=window['__CANVAS__'].user_bind_event.y
    click_pos[0]=(pos_x//param['DISPLAY_RESIZE'][0],pos_y//param['DISPLAY_RESIZE'][1])
    if param['app_status']==param['APP_STATUS_LIST'][1]:
      click_pos[1]=1

  if event=='__DMIMA__':
    global draw_MinMax
    if draw_MinMax==0:
      draw_MinMax=1
    else:
      draw_MinMax=0

  if event=='Calibrate':
    param['app_status']=param['APP_STATUS_LIST'][0]
    device.I2C_read(address=38,write_length=1,read_length=1)
    param['app_status']=param['APP_STATUS_LIST'][1]

def draw_MinMaxPixel(frame):
  min_ind,max_ind=cv2.minMaxLoc(cv2.normalize(src=frame,dst=None,alpha=255,beta=0,norm_type=cv2.NORM_MINMAX))[-2:]
  min_temp,max_temp,pos_temp=frame[min_ind[1]][min_ind[0]],frame[max_ind[1]][max_ind[0]],frame[click_pos[0][1]][click_pos[0][0]]

  # window['__MINT__'].update(str(min_temp//100)+'.'+str(min_temp%100))
  window['__MAXT__'].update(str(max_temp//100)+'.'+str(max_temp%100)[:1])
  if click_pos[1]>0:
    window['__CTMP__'].update(str(pos_temp//100)+'.'+str(pos_temp%100)[:1])
  return(min_ind,max_ind)

########################################
# Init
########################################
window=sg.Window(title=param['WINDOW_TITLE'],layout=layout_ui(),icon=param['ICON_WINDOW']).finalize()

p=Plot_cv(window['__CANVAS__'],param['DISPLAY_SIZE'])

device=Pl23c3(param['DLL_ARCHITECTURE'])
device.open_communication()

window['__CANVAS__'].bind('<Button-1>','click')

########################################
# Main loop
########################################
while(True):
  event,values=window.read(timeout=1)
  event_handler(window,event)

  if device.error_count>16 or reconnect_timer>10:
    reconnect_timer=0
    device.close_communication()
    device=Pl23c3(param['DLL_ARCHITECTURE'])
    device.open_communication(48)
    ret,id=device.I2C_read(address=0,write_length=1,read_length=1)
    if ret=='OK':
      window['__SCON__'].update('Device connected',text_color='green')
    else:
      window['__SCON__'].update('Device disconnect',text_color='red')
  else:
    reconnect_timer+=1

  if event in (sg.WIN_CLOSED,'EXIT'):
    break

  if event=='__MAX_TEMP__':
    if values['__MAX_TEMP__'] < values['__MIN_TEMP__']:
      window['__MIN_TEMP__'].update(values['__MAX_TEMP__']-1)

  if event=='__MIN_TEMP__':
    if values['__MIN_TEMP__'] > values['__MAX_TEMP__']:
      window['__MAX_TEMP__'].update(values['__MIN_TEMP__']+1)

  if param['app_status']==param['APP_STATUS_LIST'][1]:
    ret,ntc=device.I2C_read(address=20,write_length=1,read_length=2)
    if ret=='OK':
      board_temp=int.from_bytes(ntc,byteorder='big',signed=True)

    # ret,frame='OK',np.random.randint(255,size=512)
    ret,frame=device.I2C_read(address=100,write_length=1,read_length=512)

    if ret=='OK' and event=='__TIMEOUT__':
      out=np.zeros(shape=param['FRAME_SIZE'],dtype=np.uint8)
      
      image=np.reshape(np.frombuffer(bytes(frame),dtype=np.dtype(np.uint16).newbyteorder('>')),newshape=param['FRAME_SIZE']).copy()

      # locate top right corner
      # image[0][param['FRAME_SIZE'][1]-1]=0

      image=np.clip(image,values['__MIN_TEMP__']*100,values['__MAX_TEMP__']*100).astype(np.uint32)  # range for body temperature measuring

      # Moving average filter using Circular Buffer
      # temp_area_buffer[temp_area_pointer]=image
      # temp_area_pointer=temp_area_pointer+1 if temp_area_pointer<7 else 0
      # temp_area_out=np.average(temp_area_buffer,0).astype(np.uint16)

      # Normal average filter
      if temp_area_pointer<param['AVG_SIZE']:
        temp_area_buffer+=image
        temp_area_pointer+=1
      else:
        temp_area_out=(temp_area_buffer//param['AVG_SIZE']).astype(np.uint16)
        temp_area_buffer=np.zeros((param['FRAME_SIZE']),dtype=np.uint32)
        temp_area_pointer=0
        

      min_ind,max_ind=draw_MinMaxPixel(temp_area_out)
      # min_lim,max_lim=(board_temp-values['__DISP__']*100,board_temp+values['__DISP__']*100)
      min_lim,max_lim=(values['__MIN_TEMP__']*100,values['__MAX_TEMP__']*100)
      if min_lim<max_lim:
        image=np.clip(image,min_lim,max_lim)
        a=255/(max_lim-min_lim)
        b=255-a*max_lim
        out=np.clip((image*a+b),0,255).astype(np.uint8)

      out=cv2.applyColorMap(out,cv2.COLORMAP_INFERNO)

      if values['__INTERP__']=='LINEAR_64':
        out=cv2.resize(out,(64,64),interpolation=cv2.INTER_LINEAR)

      out=cv2.resize(out,param['DISPLAY_SIZE'],interpolation=cv2.INTER_NEAREST)

      if draw_MinMax:
        # cv2.rectangle(
        #   out,
        #   (min_ind[0]*param['DISPLAY_RESIZE'][0],min_ind[1]*param['DISPLAY_RESIZE'][1]),
        #   ((min_ind[0]+1)*param['DISPLAY_RESIZE'][0],(min_ind[1]+1)*param['DISPLAY_RESIZE'][1]),
        #   (255,0,0),
        #   thickness=5
        # )
        cv2.rectangle(
          out,
          (max_ind[0]*param['DISPLAY_RESIZE'][0],max_ind[1]*param['DISPLAY_RESIZE'][1]),
          ((max_ind[0]+1)*param['DISPLAY_RESIZE'][0],(max_ind[1]+1)*param['DISPLAY_RESIZE'][1]),
          (0,0,255),
          thickness=5
        )
      if click_pos[1]>0:
        cv2.rectangle(
          out,
          (click_pos[0][0]*param['DISPLAY_RESIZE'][0],click_pos[0][1]*param['DISPLAY_RESIZE'][1]),
          ((click_pos[0][0]+1)*param['DISPLAY_RESIZE'][0],(click_pos[0][1]+1)*param['DISPLAY_RESIZE'][1]),
          (0,255,0),
          thickness=5
        )

      p.canvas_redraw(out)

      window['__FPS__'].update('%05.2f'%(1/(time.time()-last_time)))
      last_time=time.time()


########################################
# Memery recycle
########################################
device.close_communication()
window.close()
