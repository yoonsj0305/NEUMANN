"""CI smoke; full weights and independent all-length grade in ZIP."""
import sys,pathlib,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc38"))
import learned_grammar as m
def test_zero_to_four_auto_created_read_ops():
 assert sorted(len(x) for x in m.LEARNED.values())==[0,1,2,3,3,4]
 for task,code in m.LEARNED.items():
  grammar=m.emit(code)
  assert m.parse(grammar)==code
  assert m.authorize(task,grammar)["status"]=="SCOPED_CERTIFIED"
  for n in range(1,8):
   for letters in itertools.product("ABC",repeat=n):
    word="".join(letters)
    assert m.run(code,word)==m.run(m.REFERENCE[task],word)
def test_13_essential_read_head_lower_bound_witnesses():
 assert sum(map(len,m.REFERENCE.values()))==13
 for task,reads in m.REFERENCE.items():
  for offset,symbol in reads:m.lower_bound_witness(task,offset)
def test_failclosed_unknown_syntax_and_semantics():
 assert m.authorize("two","import os")["status"]=="UNKNOWN_BAD_SYNTAX"
 for task,reads in m.LEARNED.items():
  if reads:modified=reads[:-1]
  else:modified=((1,"A"),)
  assert m.authorize(task,m.emit(modified))["status"]=="UNKNOWN_NOT_ALL_LENGTHS_PROVEN"
