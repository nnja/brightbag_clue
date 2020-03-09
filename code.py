import board
import time
import random
import displayio
import adafruit_dotstar
import adafruit_imageload
import adafruit_fancyled.adafruit_fancyled as fancy
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.color_packet import ColorPacket
from adafruit_bluefruit_connect.button_packet import ButtonPacket
from adafruit_clue import clue

ble = BLERadio()
uart_server = UARTService()
advertisement = ProvideServicesAdvertisement(uart_server)

num_pixels = 12
pixels = adafruit_dotstar.DotStar(board.P13, board.P15, num_pixels, brightness=0.15, auto_write=False)


# Load the sprite sheet (bitmap)
hearts, palette = adafruit_imageload.load("/nested_hearts_small.bmp",
                                                bitmap=displayio.Bitmap,
                                                palette=displayio.Palette)
new_palette = displayio.Palette(16)

RED = 0xFF0000
WHITE = 0XFFFFFF
heart_list = [9,11,14]  #palette index of pixel color for each heart
background = 15         #palette index of pixel color for bitmap background

new_palette[heart_list[0]]= RED
new_palette[heart_list[1]]= WHITE
new_palette[heart_list[2]]= RED
new_palette[background] = WHITE
current_color = fancy.CRGB(RED) #led color

# Create a sprite (tilegrid) from the heart bitmap
heart_sprite = displayio.TileGrid(hearts, x=0, y=0, pixel_shader=new_palette)
group = displayio.Group(scale=2)
group.append(heart_sprite)

# Add the Group to the Display
display = board.DISPLAY
display.show(group)



def set_heart_colors(col):
    global new_palette, heart_list
    new_palette[heart_list[0]] = col
    new_palette[heart_list[2]] = col

def rgb_to_hex(rgb):
    return int('0x%02x%02x%02x' % rgb)

def set_unique_element(list, index, range_min = 0, range_max = 11):
    new_val = random.randint(range_min, range_max)
    while new_val in list:
        new_val = random.randint(range_min, range_max)
    list[index] = new_val



#number of LEDs illuminated at a given time
num_twinkles = 6

#lifetime (in cycles) of an illuminated LED
bright_steps = 16

#twinkle_list containes indices of LEDs that are turned on
twinkle_list = [0]*num_twinkles
#twinkle_bright contains the
twinkle_bright = [0]*num_twinkles

#initialize lists
for i in range(num_twinkles):
    set_unique_element(twinkle_list, i, 0, num_pixels-1)
    set_unique_element(twinkle_bright, i, 0, bright_steps-1)


#increase twinkle_delay to slow down the animation
twinkle_delay = 0.05
last_step_time = time.monotonic()

def twinkle(color):
    global twinkle_list, twinkle_bright, last_step_time

    #non-blocking delay between animation steps
    cur_time = time.monotonic()
    if (cur_time - last_step_time < twinkle_delay):
        return
    else:
        last_step_time = cur_time

    pixels.fill((0,0,0))
    bright_val = 0.0
    for i in range(len(twinkle_list)):
        if (twinkle_bright[i] >= bright_steps):
            twinkle_bright[i] = 0
            set_unique_element(twinkle_list, i, 0, num_pixels-1)
        else:
            if (twinkle_bright[i] > (bright_steps//2)):
                bright_val = 2.0*(bright_steps - twinkle_bright[i])/bright_steps
            else:
                bright_val = 2.0*twinkle_bright[i]/bright_steps

            pixels[twinkle_list[i]]=fancy.gamma_adjust(color, brightness=bright_val).pack()
            twinkle_bright[i] = twinkle_bright[i] + 1
    pixels.show()

while True:
    # Advertise when not connected.
    ble.start_advertising(advertisement)
    while not ble.connected:
        twinkle(current_color)
        pass
    ble.stop_advertising()


    while ble.connected:
        if (uart_server.in_waiting):
            packet = Packet.from_stream(uart_server)
            if isinstance(packet, ColorPacket):
                print(packet.color)
                # current_color controls the LED color
                current_color = fancy.CRGB(packet.color[0], packet.color[1], packet.color[2])
                #change the colors on the TFT
                set_heart_colors(rgb_to_hex(packet.color))
            elif isinstance(packet, ButtonPacket):
                if packet.pressed:
                    if packet.button == ButtonPacket.UP:
                        # The UP button was pressed.
                        print("UP button pressed!")
                        if twinkle_delay >= 0:
                            twinkle_delay -= 0.01
                    elif packet.button == ButtonPacket.DOWN:
                        # The Down button was pressed.
                        print("DOWN button pressed!")
                        twinkle_delay += 0.01
                    elif packet.button == ButtonPacket.LEFT or packet.button == ButtonPacket.RIGHT:
                        print("LEFT or RIGHT were pressed!")
                        # set the current color to a random color
                        # set random values for RGB tuple (between 0 and 255)
                        r = random.randint(0, 256)
                        g = random.randint(0, 256)
                        b = random.randint(0, 256)
                        current_color = fancy.CRGB(r, g, b)
                    elif packet.button == ButtonPacket.BUTTON_1:
                        print("Button 1 was pressed")
                        clue.play_tone(880, 1)
                    elif packet.button == ButtonPacket.BUTTON_2:
                        clue.play_tone(442, 1)
        twinkle(current_color)