# NL: This is the main file that provides a nice interface to gthoi_solver.py.
# See readme.md for detailed usage instructions.

import pygame as pg
import numpy as np
import json
import argparse

from basic_marker import BasicMarker
from gthoi_solver import gthoi_solver

pg.init()

parser = argparse.ArgumentParser()
parser.add_argument('config_file', nargs='?', default='config/config.json',
                    help="The name of a JSON config file containing some required initialisation parameters. This is "
                         "optional, as a default path and file has been supplied.")
args = parser.parse_args()

with open(args.config_file, mode="r") as config_file:
    configs = json.load(config_file)
max_dim = configs['max_dim']
guitar_image_path = configs['guitar_image_path']
gitar = pg.image.load(guitar_image_path)

image_dims = gitar.get_size()
image_scale_ratio = max_dim / max(image_dims)
scaled_width = int(image_dims[0] * image_scale_ratio)
scaled_height = int(image_dims[1] * image_scale_ratio)

screen = pg.display.set_mode((scaled_width, scaled_height))
pg.display.set_caption('Get the Hang of It')

gitar = gitar.convert()
gitar = pg.transform.scale(gitar, (scaled_width, scaled_height))

marker_colour = configs['marker_colour']
marker_font = configs['marker_font']
marker_font_colour = configs['marker_font_colour']
marker_font_size = configs['marker_font_size']
marker_size = configs['marker_size']
B1_init_pixel_coords = configs['B1_init_pixel_coords']
COM_init_pixel_coords = configs['COM_init_pixel_coords']
B2_init_pixel_coords = configs['B2_init_pixel_coords']
init_real_to_pixel_dist_ratio = configs['init_real_to_pixel_dist_ratio']
init_strap_length = configs['init_strap_length']

# There is a bespoke ordering to the markers: (1) B1, (2) COM, (3) B3.
# Note that we store markers by their centres, not by their top left coords, because we want their locations to be
#   independent of their display widths. So we have to apply offsets, as below.
markers = [
    BasicMarker(rect=pg.Rect(B1_init_pixel_coords[0] - marker_size/2.0, B1_init_pixel_coords[1] - marker_size/2.0,
                             marker_size, marker_size),
                colour=pg.Color(marker_colour), font=pg.font.SysFont(marker_font, marker_font_size),
                font_colour=pg.Color(marker_font_colour), text='B1'),
    BasicMarker(rect=pg.Rect(COM_init_pixel_coords[0] - marker_size/2.0, COM_init_pixel_coords[1] - marker_size/2.0,
                             marker_size, marker_size),
                colour=pg.Color(marker_colour), font=pg.font.SysFont(marker_font, marker_font_size),
                font_colour=pg.Color(marker_font_colour), text='COM'),
    BasicMarker(rect=pg.Rect(B2_init_pixel_coords[0] - marker_size/2.0, B2_init_pixel_coords[1] - marker_size/2.0,
                             marker_size, marker_size),
                colour=pg.Color(marker_colour), font=pg.font.SysFont(marker_font, marker_font_size),
                font_colour=pg.Color(marker_font_colour), text='B2')
]
active_marker = None

# The other parameter defining the system is the strap length. It's given a default value, but this can be overwritten
#   at any time by entering any representation of a float into the keyboard and hitting Return. (Backspace will work
#   while editing as well.) Either the new value will be confirmed in the console window or, if not valid, the existing
#   value will be retained, the input cleared, and the user informed through the console.

# There is also the question of scale, which effectively defines the units in which the user expresses the strap length
#   (as well as all of the other distances between markers, though the user does not need to be concerned about those
#   directly).
real_to_pixel_dist_ratio = init_real_to_pixel_dist_ratio
strap_length = init_strap_length
# This point may be a bit confusing, but it ultimately makes everything simpler for the user: the marker positions are
#   represented in pixel terms, but there is a ratio maintained between distances in pixels and whatever other
#   reference the user wants to use (e.g. a standard unit like m or cm). This is especially useful for entering the
#   strap length in real units rather than pixels. The button-distance calibration tool triggered by the 'd' key offers
#   a straightforward method of setting this up, and the 'w' key allows the user to write these parameters out to the
#   config file for reuse in later sessions once this has been done.
# However, the user may want to know what to do at first when initialising these parameters manually in a new config
#   file (e.g. for a new guitar). A simple way to start is to set init_real_to_pixel_dist_ratio to 1.0 (meaning that all
#   measurements are in terms of pixels), and then set the strap length to something reasonable, e.g. 3 times the
#   distance in pixels between the strap buttons. From there, the I/O tools can be used to set these values more
#   precisely.
# One note: because pixel coordinates are used in places, changing the "max_dim" parameter that controls the window size
#   will invalidate other measurements, and require recalibration.

print()
print("Let's find out how your guitar hangs.")
print("Press 'd' to enter button-distance calibration mode, or 's' for strap-length entry mode.")
print("Press 'h' to solve the system.")
print("Press 'w' to overwrite the configuration file with the current marker locations, strap length, and length "
      "units.")
print(f"Strap length has been initialised to {strap_length:.4f}. The ratio between the units of strap length and "
      f"distance in pixels is {real_to_pixel_dist_ratio:.4f}.")
print()

entering_strap_length = False
entering_real_button_dist = False
text_input_string = ""

run = True
update_screen = True
while run:

    for event in pg.event.get():

        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                for num, marker in enumerate(markers):
                    if marker.rect.collidepoint(event.pos):
                        active_marker = num

        if event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                active_marker = None

        if event.type == pg.MOUSEMOTION:
            if active_marker is not None:
                markers[active_marker].move_ip(event.rel)
                update_screen = True

        if event.type == pg.KEYDOWN:
            if entering_strap_length or entering_real_button_dist:
                if event.key == pg.K_BACKSPACE:
                    text_input_string = text_input_string[:-1]
                elif event.key == pg.K_RETURN:
                    if entering_strap_length:
                        try:
                            strap_length = float(text_input_string)
                            print(f"strap_length is now {strap_length:.4f}")
                            entering_strap_length = False
                        except ValueError:
                            print(f"{text_input_string} can't be converted to a float. Try entering another value.")
                            print(f"The strap length remains {strap_length:.4f}, in terms of current length units.")
                            print("You are still in strap length editing mode.")
                    else:  # entering_real_button_dist
                        try:
                            real_button_dist = float(text_input_string)
                            strap_length_in_pixels = strap_length / real_to_pixel_dist_ratio
                            button_pixel_dist = np.linalg.norm(
                                np.array(markers[2].rect.center) - np.array(markers[0].rect.center))
                            real_to_pixel_dist_ratio = real_button_dist / button_pixel_dist
                            strap_length = strap_length_in_pixels * real_to_pixel_dist_ratio
                            print(f"The distance between the buttons has been entered as {real_button_dist}. All "
                                  f"lengths are now calibrated against that.")
                            print(f"The existing value of strap length has been converted to a new value of "
                                  f"{strap_length:.4f} to reflect the new units.")
                            entering_real_button_dist = False
                        except ValueError:
                            print(f"{text_input_string} can't be converted to a float. Try entering another value.")
                            print(f"System length calibration is unchanged from its previous state.")
                            print("You are still in real button distance editing mode.")
                    text_input_string = ""

        if event.type == pg.TEXTINPUT:
            if entering_strap_length or entering_real_button_dist:
                if entering_strap_length and (event.text == "s"):
                    print("Strap length entry aborted.")
                    print(f"The strap length remains {strap_length:.4f}, in terms of current length units.")
                    text_input_string = ""
                    entering_strap_length = False
                elif entering_real_button_dist and (event.text == "d"):
                    print("Real button distance entry aborted.")
                    text_input_string = ""
                    entering_real_button_dist = False
                else:
                    text_input_string += event.text
            elif event.text == "h":
                # The user has triggered a solve. So get the hang of it.

                # Before anything else, we'll check that the user hasn't specified a strap length that's shorter than
                #   the distance between the strap buttons (a constraint violation). This is a specific case that we
                #   can warn about directly, rather than just having the solver say that the system is unstable.
                # Take the distance between the strap buttons:
                g3 = (np.linalg.norm(np.array(markers[2].rect.center) - np.array(markers[0].rect.center)) *
                      real_to_pixel_dist_ratio)
                if g3 > strap_length:
                    print(f"The strap length of {strap_length:.4f} is shorter than the distance between the buttons of "
                          f"{g3:.4f}. Move the buttons and/or increase the strap length and try again.")
                else:
                    # First, we need to compute the inputs to the solver: we need to get the angle theta_COM between the
                    #   two vectors that the buttons define vs. the COM, and we need to compute the (left-handed) pre-
                    #   rotation that places the system into the state in terms of which the solver is defined.
                    # We are using clockwise-positive/left-handed conventions for our angles, as decided offline. This
                    #   is the simplest way of expressing things given our choices in the original derivation:
                    v1 = np.array(markers[0].rect.center) - np.array(markers[1].rect.center)
                    v2 = np.array(markers[2].rect.center) - np.array(markers[1].rect.center)
                    # And then we have to correct for the Original Sin of graphics and get positive y pointing upwards
                    #   like it's supposed to:
                    v1[1] = -v1[1]
                    v2[1] = -v2[1]

                    reference_ax = np.array([-1, 0])
                    theta_v2_v1 = np.arctan2(np.cross(v2, v1), np.dot(v1, v2))
                    if theta_v2_v1 >= 0:
                        # The vector that will be rotated clockwise to (-1, 0) is v1
                        theta_COM = theta_v2_v1
                        g1 = np.linalg.norm(v1)
                        g2 = np.linalg.norm(v2)
                        pre_rot = np.arctan2(np.cross(reference_ax, v1), np.dot(v1, reference_ax))
                    else:
                        # The vector that will be rotated clockwise to (-1, 0) is v2
                        theta_COM = -theta_v2_v1
                        g1 = np.linalg.norm(v2)
                        g2 = np.linalg.norm(v1)
                        pre_rot = np.arctan2(np.cross(reference_ax, v2), np.dot(v2, reference_ax))
                    # We'll put everything into "real" units of length, according to the current calibration, such that
                    #   the left-side strap length is returned in units consistent with the representation of the total
                    #   strap length, as you'd expect:
                    all_res = gthoi_solver(g1 * real_to_pixel_dist_ratio,
                                           g2 * real_to_pixel_dist_ratio,
                                           theta_COM,
                                           strap_length)
                    if all_res:
                        post_rot = all_res['guitar_angle']
                        total_rot = pre_rot + post_rot
                        print(f"Equilibrium angle is {total_rot * 180 / np.pi:.2f} degrees clockwise vs. the "
                              f"horizontal.")
                    else:
                        print("Unstable design. Not recommended.")
            elif event.text == "s":
                print()
                print("You are now entering the length of the strap, in terms of the units defined by the provided "
                      "distance between the strap buttons.")
                print("Type in a string that can be converted to a float and press Return. You can use Backspace. "
                      "Press 's' again at any time to abort and retain the current value of the strap length.")
                entering_strap_length = True
            elif event.text == "d":
                print()
                print("You are now entering the distance between the strap buttons in their current positions, to be "
                      "used for defining the units of length. Choose whichever units you intend to represent the strap "
                      "length in. Note that the current strap length will be updated to reflect the unit conversion.")
                print("Type in a string that can be converted to a float and press Return. You can use Backspace. "
                      "Press 'd' again at any time to abort and retain the current state.")
                entering_real_button_dist = True
            elif event.text == "w":
                configs['B1_init_pixel_coords'] = markers[0].rect.center
                configs['COM_init_pixel_coords'] = markers[1].rect.center
                configs['B2_init_pixel_coords'] = markers[2].rect.center
                configs['init_real_to_pixel_dist_ratio'] = real_to_pixel_dist_ratio
                configs['init_strap_length'] = strap_length
                with open(args.config_file, mode="w") as config_file:
                    json.dump(configs, config_file, indent=4)
                print()
                print(f"NOTE --> Initial values of marker locations (strap buttons and C.O.M.), strap length, and "
                      f"length units in terms of pixels in {args.config_file} have all been overwritten with their "
                      f"current values. When you next load {args.config_file}, you'll be starting from this "
                      f"configuration.")
            else:
                # No other cases at present. Just keeping this here for clarity.
                pass

        if event.type == pg.QUIT:
            run = False

    if update_screen:
        screen.blit(gitar, (0, 0))
        for marker in markers:
            marker.draw(screen)
        pg.display.flip()
        update_screen = False

pg.quit()
