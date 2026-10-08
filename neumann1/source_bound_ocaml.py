"""Finite actual OCaml replay of the already source-bound pure fragment.

Generated code excludes synthesis holes and attributes. It executes the exact
validated reference/converter bodies and a separately emitted native summary.
This is a bounded runtime control, not an all-machine-integer theorem.
"""
from neumann1.source_bound_recursive import ProtocolError


PREFIX='neumann_fragment_'


def expression(term):
    if type(term)is bool:return 'true' if term else 'false'
    if type(term)is int:return '('+str(term)+')'
    if isinstance(term,str):return term
    op=term[0];args=[expression(t) for t in term[1:]]
    if op=='ite':return '(if '+args[0]+' then '+args[1]+' else '+args[2]+')'
    if op in {'max','min'}:return '('+op+' '+args[0]+' '+args[1]+')'
    if op=='not':return '(not '+args[0]+')'
    operators={'add':'+','sub':'-','ge':'>=','gt':'>','le':'<=','lt':'<','eq':'=','and':'&&','or':'||'}
    if op not in operators:raise ProtocolError('Unsupported emitted OCaml IR constructor')
    return '('+args[0]+' '+operators[op]+' '+args[1]+')'


def tuple_value(items):return '('+', '.join(items)+')' if len(items)>1 else items[0]


def function(name,program):
    # Flat parameter lists avoid OCaml tuples at the function boundary.
    return 'let '+PREFIX+name+' '+' '.join(program['inputs'])+' = '+tuple_value([expression(t) for t in program['outputs']])+';;\n'


def emit(binding,proposal):
    original=binding['assertion'];functions=binding['representation_functions']
    definitions={**functions,original['reference']:binding['reference_definition']}
    if any(n.startswith(PREFIX) for n in definitions):raise ProtocolError('Reserved OCaml replay prefix collision')
    if any(len(str(v))>17 for v in proposal['empty']):raise ProtocolError('Finite replay requires machine-sized constants')
    text="type 'a clist = CNil | Single of 'a | Concat of 'a clist * 'a clist;;\n"
    text+="type 'a linked = Nil | Cons of 'a * 'a linked;;\n"
    reference=binding['reference_definition']
    text+='let rec '+original['reference']+' '+' '.join(reference['params'])+' = '+reference['body']+';;\n'
    for index,(name,definition) in enumerate(sorted(functions.items())):
        text+=('let rec ' if index==0 else 'and ')+name+' '+' '.join(definition['params'])+' = '+definition['body']+'\n'
    text+=';;\n'
    for name in ['step','merge','decode']:text+=function(name,proposal[name])
    latent=len(proposal['empty']);names=['z'+str(i) for i in range(latent)]
    empty=tuple_value([str(v) for v in proposal['empty']])
    head='(if a then 1 else 0)' if binding['projection']['input_type']=='Bool' else 'a'
    text+='let rec '+PREFIX+'summary = function\n| CNil -> '+empty+'\n'
    text+='| Single a -> '+PREFIX+'step '+head+' '+' '.join('('+str(v)+')' for v in proposal['empty'])+'\n'
    text+='| Concat (a,b) -> let '+tuple_value(['l'+str(i) for i in range(latent)])+' = '+PREFIX+'summary a in '
    text+='let '+tuple_value(['r'+str(i) for i in range(latent)])+' = '+PREFIX+'summary b in '
    text+=PREFIX+'merge '+' '.join(['l'+str(i) for i in range(latent)]+['r'+str(i) for i in range(latent)])+';;\n'
    alphabet=[0,1] if binding['projection']['input_type']=='Bool' else [-2,0,3]
    text+='let '+PREFIX+'alphabet = [|'+ ';'.join(str(h) for h in alphabet)+'|];;\n'
    text+='let rec '+PREFIX+'power a n = if n=0 then 1 else a * '+PREFIX+'power a (n-1);;\n'
    treehead='('+PREFIX+'alphabet.(values.(a)) > 0)' if binding['projection']['input_type']=='Bool' else PREFIX+'alphabet.(values.(a))'
    text+='let rec '+PREFIX+'tree shape values a b =\n'
    text+='if a=b then CNil else if b-a=1 then Single '+treehead+' else\n'
    text+='let cut = if shape=0 then a+1 else if shape=1 then b-1 else (a+b)/2 in\n'
    text+='Concat ('+PREFIX+'tree shape values a cut, '+PREFIX+'tree shape values cut b);;\n'
    width=len(binding['projection']['goal_types']);original_names=['original'+str(i) for i in range(width)];candidate_names=['candidate'+str(i) for i in range(width)]
    text+='let () =\nfor n=0 to 4 do\nfor code=0 to '+PREFIX+'power '+str(len(alphabet))+' n-1 do\n'
    text+='let values=Array.init n (fun i -> (code / '+PREFIX+'power '+str(len(alphabet))+' i) mod '+str(len(alphabet))+') in\n'
    text+='for shape=0 to 2 do\nlet tree='+PREFIX+'tree shape values 0 n in\n'
    text+='let '+tuple_value(original_names)+' = '+original['reference']+' ('+original['representation']+' tree) in\n'
    text+='let '+tuple_value(names)+' = '+PREFIX+'summary tree in\n'
    text+='let '+tuple_value(candidate_names)+' = '+PREFIX+'decode '+' '.join(names)+' in\n'
    encoded=['(if '+n+' then 1 else 0)' if kind=='Bool' else n for n,kind in zip(original_names,binding['projection']['goal_types'])]
    text+='Printf.printf "'+','.join(['%d']*3)+'|'+','.join(['%d']*width)+'|'+','.join(['%d']*width)+'\\n" '
    text+=' '.join(['n','code','shape']+encoded+candidate_names)+'\ndone\ndone\ndone;;\n'
    return text,{'alphabet':alphabet,'max_length':4,'shapes':[0,1,2],'rows':3*sum(len(alphabet)**n for n in range(5)),
                 'scope':'actual OCaml finite mathematical-fragment replay; source holes/attributes removed,not the full upstream workflow or all machine integers'}
