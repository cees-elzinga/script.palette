import xbmc
import xbmcgui
import xbmcaddon
import sys
import colorsys
import os
import shutil
from PIL import Image, ImageDraw

__addon__      = xbmcaddon.Addon()
__cwd__        = __addon__.getAddonInfo('path')
__icon__       = os.path.join(__cwd__, "icon.png")
__resource__   = xbmc.translatePath(os.path.join( __cwd__, 'resources', 'lib'))
__js__         = xbmc.translatePath(os.path.join( __cwd__, 'resources', 'js'))
__xml__        = os.path.join( __cwd__, 'addon.xml' )

sys.path.append (__resource__)
from settings import *


def notify(title, msg=""):
  global __icon__
  xbmc.executebuiltin("XBMC.Notification(%s, %s, 3, %s)" % (title, msg, __icon__))

xbmc.log("Palette service started")

capture = xbmc.RenderCapture()
fmt = capture.getImageFormat()
fmtRGBA = fmt == 'RGBA'


class Logger:
  scriptname = "Palette"

  def log(self, msg):
    xbmc.log("%s: %s" % (self.scriptname, msg))

class MyPlayer(xbmc.Player):
  playingvideo = None

  def __init__(self):
    xbmc.Player.__init__(self)

  def onPlayBackStarted(self):
    if self.isPlayingVideo():
      self.playingvideo = True
      state_changed("started")

  def onPlayBackStopped(self):
    if self.playingvideo:
      self.playingvideo = False
      state_changed("stopped")

  def onPlayBackEnded(self):
    if self.playingvideo:
      self.playingvideo = False
      state_changed("stopped")


class HSVRatio:

  def __init__(self, hue=0.0, saturation=0.0, value=0.0, ratio=0.0):
    self.h = hue
    self.s = saturation
    self.v = value
    self.ratio = ratio

  def average(self, h, s, v):
    self.h = (self.h + h) / 2
    self.s = (self.s + s) / 2
    self.v = (self.v + v) / 2

  def __repr__(self):
    return 'h: %s s: %s v: %s ratio: %s' % (self.h, self.s, self.v, self.ratio)


class Screenshot:
  def __init__(self, pixels, capture_width, capture_height):
    self.pixels = pixels
    self.capture_width = capture_width
    self.capture_height = capture_height

  def most_used_spectrum(self, spectrum, saturation, value, size, overall_value):
    colorHueRatio = 5
    hsvRatios = []
    hsvRatiosDict = {}

    # maybe: check PIL histogram
    for i in range(360):
      if spectrum.has_key(i):
        #shift index to the right so that groups are centered on primary and secondary colors
        colorIndex = int(((i+colorHueRatio/2) % 360)/colorHueRatio)
        pixelCount = spectrum[i]

        if hsvRatiosDict.has_key(colorIndex):
          hsvr = hsvRatiosDict[colorIndex]
          hsvr.average(i/360.0, saturation[i], value[i])
          hsvr.ratio = hsvr.ratio + pixelCount / float(size)

        else:
          hsvr = HSVRatio(i/360.0, saturation[i], value[i], pixelCount / float(size))
          hsvRatiosDict[colorIndex] = hsvr
          hsvRatios.append(hsvr)

    hsvRatios = sorted(hsvRatios, key=lambda hsvratio: hsvratio.ratio, reverse=True)
    return hsvRatios[0]

  def spectrum_hsv(self, pixels, width, height):
    spectrum = {}
    saturation = {}
    value = {}

    size = int(len(pixels)/4)
    pixel = 0

    i = 0
    s, v = 0, 0
    r, g, b = 0, 0, 0
    tmph, tmps, tmpv = 0, 0, 0
    
    for i in range(size):
      if fmtRGBA:
        r = pixels[pixel]
        g = pixels[pixel + 1]
        b = pixels[pixel + 2]
      else: #probably BGRA
        b = pixels[pixel]
        g = pixels[pixel + 1]
        r = pixels[pixel + 2]
      pixel += 4

      tmph, tmps, tmpv = colorsys.rgb_to_hsv(float(r/255.0), float(g/255.0), float(b/255.0))
      h = int(tmph * 360)
      s += tmps
      v += tmpv

      if spectrum.has_key(h):
        spectrum[h] += 1 # tmps * 2 * tmpv
        saturation[h] = (saturation[h] + tmps)/2
        value[h] = (value[h] + tmpv)/2
      else:
        spectrum[h] = 1 # tmps * 2 * tmpv
        saturation[h] = tmps
        value[h] = tmpv

    overall_value = v / float(i)
    return self.most_used_spectrum(spectrum, saturation, value, size, overall_value)

def swap(s):
  #string of pixels
  #input in BGRA
  #output in RGBA
  r = ""
  for i in range(len(s)/4):
    r += s[i*4+2] + s[i*4+1] + s[i*4+0] + s[i*4+3]
  return r

def save_image(filename, pixels, width, height):
  if not fmtRGBA:
    # assume format is BGRA
    pixels = swap(pixels)
  im = Image.fromstring("RGBA", (width, height), pixels)
  im.save(filename)

def generate_html(colors, html_dir):
  html = """<style>
    div.frame {float:left;width:3px;height:75px;}
    div#hue {display:none;}
  </style>

  <script src="jquery-2.0.3.min.js"></script>
  <script src="hue.js"></script>"""

  i = 0
  for color in colors:
    html += """
      <div class="frame" style="background-color: hsl(%s, %s%%, %s%%);"
       onmouseover='show_screen("screen_%s.png");set_light(%s, %s, %s);'></div>
    """ % (color.h*360, color.s*100, color.v*100,
          i,
          int(color.h*65535), int(color.s*254), int(color.v*254))
    i += 1

  html += """
<br style='clear:both' /><br />
<img id="still" src="screen_0.png" />
<br /><br />
<input type="button" onClick="jQuery('div#hue').toggle()" value="Enable communication with Hue bridge" /><br /><br />
<div id="hue">
  Bridge IP: <input type="text" id="bridge_ip"/><br />
  Username: <input type="text" id="username"/><br />
  Bulb: <input type="radio" name="light" value="1" checked>1</input>
      <input type="radio" name="light" value="2">2</input>
      <input type="radio" name="light" value="3">3</input><br />
  <input type="button" onClick="connect();" value="Connect" /><br />
  Status: <span id="status">not connected</span>
</div>
"""

  f = open("%s" % os.path.join(html_dir, "index.html"), "w")
  f.write(html)
  f.close()

def generate_png(colors, filename):
  height = 75
  width_p_s = 3
  width = len(colors)*width_p_s
  im = Image.new("RGB", (width, height))
  draw = ImageDraw.Draw(im)

  for i in range(len(colors)):
    color = 'hsl(%d, %d%%, %d%%)' % (colors[i].h*360, colors[i].s*100, colors[i].v*100)
    draw.rectangle([
        (i*width_p_s, 0),
        (i*width_p_s+width_p_s, height)
      ],
      fill=color
    )
  logger.log("saving to: %s" % filename)
  im.save(filename)

def run(logger):
  player = None
  still = 0
  notify("Palette started")

  while not xbmc.abortRequested:
    if player == None:
      player = MyPlayer()
    else:
      xbmc.sleep(1000)

    capture.waitForCaptureStateChangeEvent(1000)
    if capture.getCaptureState() == xbmc.CAPTURE_STATE_DONE:
      if player.playingvideo:
        pixels = capture.getImage()
        if settings.html:
          save_image(
            os.path.join(settings.html_dir, "screen_%d.png" % still),
            str(pixels),
            capture.getWidth(),
            capture.getHeight()
          )
          still += 1
        screen = Screenshot(pixels, capture.getWidth(), capture.getHeight())
        hsvRatios = screen.spectrum_hsv(screen.pixels, screen.capture_width, screen.capture_height)
        colors.append(hsvRatios)

def state_changed(state):
  if state == "started":
    #start capture when playback starts
    capture_width = 150 #32 #100
    capture_height = int(capture_width / capture.getAspectRatio())
    capture.capture(capture_width, capture_height, xbmc.CAPTURE_FLAG_CONTINUOUS)

  elif state == "stopped":
    if settings.html:
      shutil.copyfile(
        os.path.join(__js__, "hue.js"),
        os.path.join(settings.html_dir, "hue.js")
      )
      shutil.copyfile(
        os.path.join(__js__, "jquery-2.0.3.min.js"),
        os.path.join(settings.html_dir, "jquery-2.0.3.min.js")
      )
      generate_html(colors, settings.html_dir)
      notify("Saved palette", settings.html_dir)

    logger.log("settings.png: %s " % settings.png)
    if settings.png:
      generate_png(colors, settings.png_filename)
      notify("Saved palette", settings.png_filename)

if ( __name__ == "__main__" ):
  colors = []
  logger = Logger()
  settings = settings()
  if settings.html:
    if not os.path.isdir(settings.html_dir):
      os.mkdir(settings.html_dir)
    
  if settings.png:
    assert(os.path.isdir(os.path.dirname(settings.png_filename)))    
  run(logger)
