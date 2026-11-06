import sys,pathlib,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc37"))
from learned_two_head import *
def test_compiled_model_proves_all_finite_words():
 assert prove_compiled(LEARNED)=="PROVED_COMPILED_ALL_FINITE_WORDS"
 for n in range(1,9):
  for chars in itertools.product(ABC,repeat=n):
   word="".join(chars)
   assert run(LEARNED,word)==target(word)
def test_older_one_head_is_mathematically_insufficient():
 for d in range(-100,101):one_head_witness(d)
def test_wrong_new_program_not_admitted():
 wrong={"addresses":(3,-2),"table":[[list(row) for row in block] for block in LEARNED["table"]]}
 wrong["table"][1][2][0]=2
 assert prove_compiled(wrong)=="FAIL"
 assert prove_compiled({"addresses":(-2,-2),"table":LEARNED["table"]})=="UNKNOWN_BAD_COORDINATES"
