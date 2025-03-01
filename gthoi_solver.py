# NL: This is the core solver implementing the Method of Solution section in readme.md. See that.
# It's called from get_the_hang_of_it.py, the main program.

# TODO: Validity checks on parameter values to produce readable error messages instead of crashes. E.g. if a strap
#  length is specified that is shorter than the distance between the buttons. Also to disallow the C.O.M. from sitting
#  above the segment between the buttons. Note though that there are now no known inputs from the main client script
#  (get_the_hang_of_it.py) that can produce a crash in this function, as this now returns an empty result structure in
#  many cases that is then caught in the main script, and the main script is handling the issue of ensuring that the
#  "C.O.M. kink" is in the right direction (meaning that theta_COM <= pi).

import numpy as np
from sympy import solve
from sympy.abc import l
from sympy.core.numbers import Float


# There are four parameters specifying the system:
# g_1: The length of the segment between the C.O.M. and the left/bottom strap button (facing the player).
# g_2: The length of the segment between the C.O.M. and the right/top strap button (facing the player).
# theta_COM: The angle between the above two segments.
# L: The total length of the strap.
def gthoi_solver(g_1, g_2, theta_COM, L):

    # The coefficients of the quartic in the length l of the leftmost (facing the player) segment of the strap:
    #   C_4*l**4 + C_3*l**3 + C_2*l**2 + C_1*l + C_0 = 0:
    A = (g_1/g_2) / np.sin(theta_COM)
    B = 1 / np.tan(theta_COM)
    g_3 = np.sqrt(g_1**2 + g_2**2 - 2*g_1*g_2*np.cos(theta_COM))
    C_4 = -4*(1 + A**2 - 2*A*B + B**2)
    C_3 = 4*L*(1 + A**2 - 2*A*B + B**2) - 4*(2*A*B*L - 2*L*A**2)
    C_2 = (g_3**2 - L**2)*(1 + A**2 - 2*A*B + B**2) + 4*L*(2*A*B*L - 2*L*A**2) - 4*(A**2*L**2 - g_1**2)
    C_1 = 4*A**2*L**3 + (g_3**2 - L**2)*(2*A*B*L - 2*L*A**2) - 4*g_1**2*L
    C_0 = (g_3**2 - L**2)*A**2*L**2

    # Now call the quartic solver to get the solution(s) for l:
    sols = solve(C_4*l**4 + C_3*l**3 + C_2*l**2 + C_1*l + C_0)
    # Keep only the real solutions:
    real_l = np.array([float(r) for r in sols if isinstance(r, Float)])

    # There is the chance that you've been given an unstable/ill-specified system, and that there are no real solutions.
    # This typically comes up when someone puts the C.O.M. very close to the segment between the strap buttons. You
    #   know, like a Gibson SG. What happens here is that you get a few different solutions with tiny imaginary
    #   components, where the real components of each represent the respective cases of (a) balancing near the
    #   horizontal, (b) the head diving straight at the floor, and (c) the head flying up and smacking you in the teeth.
    # Their residuals are all actually very small, as they all represent approximate solutions to the original problem
    #   as posed, but this is not a situation you want to be in, as the middle solution is not stable, and the guitar
    #   ultimately wants to end up in whichever of the near-vertical situations puts the C.O.M. further down. In the
    #   typical case of the C.O.M. being closer to the heel button than the end button, that corresponds to
    #   catastrophic neck dive. You know, like a Gibson SG.
    # None of these solutions will be returned, and the empty return serves as a warning that you should pick a
    #   different design.
    if real_l.size == 0:
        return {}
    # Otherwise, you're in the intended case of a single, stable, valid equilibrium, and you can proceed as below.
    # (This appears as two real solutions, one of which represents the strap pushing instead of pulling, which can be
    #   discarded, as follows.)

    # Solve for the unknown angles through substitution (see derivation);
    theta_g = np.arctan(A*(L/real_l - 1) + B)
    theta_s = np.arccos(g_1 * np.cos(theta_g) / real_l)

    # We should now have two candidate solutions for (l, theta_g, theta_s). Because inverse trig operations are
    #   involved, we actually have many shadow candidate solutions as well: arctan + pi is always another solution to
    #   arctan, and -arccos is another solution to arccos. Yucky. *However*, in our case, the conventions work
    #   immediately in our favour: we constrain theta_g to [-pi/2, pi/2], just as is returned by np.arctan, because
    #   outside of this interval represents the left strap button moving to the right of the C.O.M. (i.e. the guitar
    #   turning upside down), which is disqualifying, and likewise, we constrain theta_s to be positive (as returned by
    #   np.arccos, which is in [0, pi]), as in our convention this represents both sides of the strap angled above the
    #   horizontal from their respective buttons, as is needed for them to pull upwards. (In fact, our constraint is
    #   stricter: theta_s must be in [0, pi/2] to keep the strap inflection point horizontally between the strap
    #   buttons, but we will need to address cases in which the wrong solution still falls in this interval, so this
    #   isn't too important here.)
    # Since there is only one unique solution that obeys all constraints, this means that one of the two solutions we
    #   have at this point is simply wrong, because one of its angles "wanted" to take the other, illegal value. All we
    #   have to do now is run those solutions through our original system constraints directly and find out who the
    #   impostor is.
    # Since we originally used constraints on horizontal distances in deriving our solutions, we're going to finally
    #   apply the constraint on the equality of the left and right vertical paths to select the correct solution. The
    #   sin functions will ensure that theta_s's sign is correct, and that will be that:
    err = np.abs(np.sin(theta_g)*g_1 + np.sin(theta_s)*real_l -
                 ((L-real_l)*np.sin(theta_s) + g_2*np.sin(np.pi-theta_COM-theta_g)))
    correct_ind = np.argmin(err)

    # Some bit of numerical error is tolerated in the correct solution. Define that tolerance for a final check here:
    eps = 1e-8 * L
    assert(err[correct_ind] < eps)

    # The final results:
    #   'guitar_angle': the angle that the segment between the left/bottom button and the guitar C.O.M. makes with the
    #       horizontal; for common configurations, this will be close to the guitar "centreline" (down the middle of the
    #       neck) and will correspond quite directly to what you would intuitively think of as "the guitar's angle"; you
    #       want a moderately negative value of this to indicate a healthy rise in the neck (about -pi/4 for technical
    #       playing); note correspondingly that if your left/bottom button is somewhere else and/or your C.O.M. is off
    #       of the neckline, then you're going to need to interpret the result accordingly for your guitar
    #   'left_strap_seg_len': the length of the segment of the strap between the shoulder inflection point and the left/
    #       bottom strap button (to someone facing the player, as in the diagram)
    #   'strap_angle': the (common) angle that each strap segment forms vs. the horizontal at each strap button; the
    #       angle of the strap kink at the player's shoulder is (pi-2*strap_angle), by simple trig
    result_dict = {'guitar_angle': theta_g[correct_ind],
                   'left_strap_seg_len': real_l[correct_ind],
                   'strap_angle': theta_s[correct_ind]}

    return result_dict


if __name__ == '__main__':
    res = gthoi_solver(174.0028735394907, 181.99450541156455, 3.0312562559449687, 400)
