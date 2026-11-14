"""Narrow proof witness, full 214326 exhaustive grammar audit is in research ZIP."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"program_synthesis"))
from learned_programs import learned_gf2_low,learned_integer_low

def test_scalar_carry_matters_for_integer_multiplication():
    # (1+x)*(1+x) differs from ordinary arithmetic 3*3.
    assert learned_gf2_low(3,3,3)==5
    assert learned_integer_low(3,3,3)==1
    # Do not conclude that every no-scalar algorithm is impossible from one witness.

def test_scaling_beyond_source_and_stateful_register():
    assert learned_integer_low(255,255,8)==1
    assert learned_integer_low(65535,65535,16)==1
