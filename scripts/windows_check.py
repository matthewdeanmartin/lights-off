import sys, os
sys.path.insert(0, '.')
from lights_off import Tolk
Tolk.try_sapi(True)
Tolk.prefer_sapi(True)
Tolk.load()
print('loaded:', Tolk.is_loaded())
print('screen reader:', Tolk.detect_screen_reader())
print('has speech:', Tolk.has_speech())
result = Tolk.speak('Hello, this is a test')
print('speak result:', result)
input('Press Enter...')
Tolk.unload()
  
