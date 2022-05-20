
########################################
# Class
########################################
from ctypes import *

class Pl23c3:
  def __init__(self,dll):
    self.DEVICE_VID=c_uint16(1659)
    self.pl23c3=CDLL(dll)
    self.error_count=0

  def open_communication(self,I2C_address=48,I2C_frequency=1000):
    '''
      frequency from 94khz to 6Mhz
    '''
    self.handle=c_void_p()
    self.device_count=c_uint32(0)
    self.pl23c3.EnumDeviceByVid(byref(self.device_count),self.DEVICE_VID)
    if self.device_count.value>0:
      self.error_count=0
      self.pl23c3.OpenDeviceHandle(0,byref(self.handle))
      self.pl23c3.SetI2CDeviceAddress(self.handle,I2C_address)
      freq_divider=24000//I2C_frequency
      if freq_divider<4:
        freq_divider=4
      if freq_divider>250:
        freq_divider=250
      self.pl23c3.SetI2CFrequency(self.handle,freq_divider)

  def I2C_write(self,address,data,write_length,timeout=100):
    wData=create_string_buffer(1+write_length)
    rLength=c_uint16(0)
    ret='ERROR'
    wData.raw=address.to_bytes(1,byteorder='big')+data.to_bytes(write_length,byteorder='big')
    self.pl23c3.I2CWrite(
      self.handle,
      byref(wData),
      1+write_length,
      byref(rLength),
      timeout
    )
    if rLength.value==write_length+1:
      self.error_count=0
      ret='OK'
    else:
      self.error_count+=1
    return(ret)

  def I2C_read(self,address,write_length,read_length,timeout=100):
    wData=create_string_buffer(write_length)
    rData=create_string_buffer(read_length)
    rLength=c_uint32(0)
    ret='ERROR'
    wData.raw=address.to_bytes(write_length,byteorder='big')
    self.pl23c3.I2CWriteRead(
      self.handle,
      byref(wData),
      write_length,
      byref(rData),
      read_length,
      byref(rLength),
      timeout
    )
    if rLength.value==read_length:
      self.error_count=0
      ret='OK'
    else:
      self.error_count+=1
    return(ret,list(rData.raw))

  def close_communication(self):
    self.error_count=0
    self.pl23c3.CloseDeviceHandle(self.handle)
