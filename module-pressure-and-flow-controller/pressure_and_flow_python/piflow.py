import time
import spidev

class PiFlow:
  DEVICE_ID                       = 'MICROFLOW'
  STX                             = 2
  PACKET_TYPE_GET_ID              = 1
  PACKET_TYPE_SET_PRESSURE_TARGET = 2
  PACKET_TYPE_GET_PRESSURE_TARGET = 3
  PACKET_TYPE_GET_PRESSURE_ACTUAL = 4
  num_controllers                 = 4
  
  def __init__( self, spi, reply_pause_s ):
    self.spi = spi
    self.reply_pause_s = reply_pause_s
  
  def read_bytes( self, bytes ):
    data = []
    for x in range( bytes ):
      data.extend( self.spi.xfer2( [0] ) )
    return data
  
  def packet_read( self ):
    valid = False
    data = self.read_bytes( 1 )
    if ( data[0] == self.STX ):
      data.extend( self.read_bytes( 2 ) )
      size = data[1]
      type = data[2]
      data.extend( self.read_bytes( size - 3 ) )
      checksum = sum( data ) & 0xFF
      if ( checksum == 0 ):
        data = data[3:(size-1)]
        valid = True
    if not valid:
      data = []
    return valid, data
  
  def packet_write( self, type, data ):
    msg = [2, len(data)+4, type] + data
    checksum = ( -( sum( msg ) & 0xFF ) ) & 0xFF
    msg.append( checksum )
    self.spi.xfer2( msg )
    
  def get_id( self ):
    self.packet_write( self.PACKET_TYPE_GET_ID, [] )
    time.sleep( self.reply_pause_s )
    valid, data = self.packet_read()
    id = data[1:-1]
    id_valid = ( bytes(id).decode("ascii") == self.DEVICE_ID )
    return ( valid and ( data[0] == 0 ), id, id_valid )

  def set_pressure( self, pressures_mbar ):
    pressures_mbar_bytes = []
    for i in range(self.num_controllers):
      mask = 1 << i
      pressures_mbar_bytes.extend( [mask] + list( pressures_mbar[i].to_bytes( 2, 'little', signed=False ) ) )
    self.packet_write( self.PACKET_TYPE_SET_PRESSURE_TARGET, pressures_mbar_bytes )
    time.sleep( self.reply_pause_s )
    time.sleep( 1 )
    valid, data = self.packet_read()
#    actual_wait_ns = int.from_bytes( data[1:5], byteorder='little', signed=False )
#    print( "data={}, wait={}, period={}, wait_bytes={}".format( data, actual_wait_ns, actual_period_ns, data[1:5] ) )
    return ( ( valid and ( data[0] == 0 ) ) )
