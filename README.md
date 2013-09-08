script.palette
==============

An add-on for XBMC that creates a palette of the used colors in a video.

**'Avatar' trailer**

![Screenshot](https://raw.github.com/cees-elzinga/script.palette/master/sample/avatar.png)

**'Finding Nemo' trailer**

![Screenshot](https://raw.github.com/cees-elzinga/script.palette/master/sample/finding_nemo.png)

**'Life of Pi' trailer**

![Screenshot](https://raw.github.com/cees-elzinga/script.palette/master/sample/life_of_pi.png)

It samples the video every second and calculates the most dominant color. It creates a PNG image with the colors and/or a HTML page. The HTML page uses a mouse-over effect to show the image it sampled, and optionally updates a Philips Hue light bulb to the selected color.

**'Life of Pi' HTML output**

![Screenshot](https://raw.github.com/cees-elzinga/script.palette/master/sample/life_of_pi_html.png)

**Notes**

 - XBMC add-on is only tested on Ubuntu
 - HTML output is only tested on Chrome

This add-on is based on [script.xbmc.hue.ambilight](https://github.com/cees-elzinga/script.xbmc.hue.ambilight). The original project does color corrections/adjustments for better results on Philips Hue bulbs. The color corrections exluded from this project.
