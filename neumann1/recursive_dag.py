"""Certified execution of compact ordered list DAGs without unrolling.

Known memoized DAG execution and list-summary induction, not learned discovery.
All native and prospective learned proposers receive the same compiler rights.
Expanded length is a semantic size, never an observed speedup multiplier.
"""
from copy import deepcopy
from neumann1.recursive_summary import CertifiedSummary,SummaryError,identity,interpret


def validate_dag(dag, *, max_nodes=100000, max_head_bits=4096, max_length_bits=8192):
    if (type(max_nodes)is not int or not 1<=max_nodes<=100000 or
        type(max_head_bits)is not int or not 1<=max_head_bits<=65536 or
        type(max_length_bits)is not int or not 1<=max_length_bits<=65536):
        raise SummaryError('Bounded DAG resources required')
    if (not isinstance(dag,dict) or set(dag)!={'semantics','nodes','roots'} or
        dag['semantics']!='ordered_integer_list_dag'):
        raise SummaryError('Strict ordered public DAG schema required')
    nodes,roots=dag['nodes'],dag['roots']
    if not isinstance(nodes,list) or not 1<=len(nodes)<=max_nodes:
        raise SummaryError('Bounded nonempty DAG nodes required')
    lengths=[]
    for index,node in enumerate(nodes):
        if node==['nil']:length=0
        elif (isinstance(node,list) and len(node)==2 and node[0]=='single' and type(node[1])is int):
            if abs(node[1]).bit_length()>max_head_bits:raise SummaryError('Head integer bit budget exceeded')
            length=1
        elif isinstance(node,list) and len(node)==3 and node[0]=='concat':
            left,right=node[1:]
            if any(type(i)is not int or not 0<=i<index for i in [left,right]):
                raise SummaryError('DAG references must point strictly backward; order is preserved')
            length=lengths[left]+lengths[right]
        else:raise SummaryError('Malformed ordered DAG node')
        if length.bit_length()>max_length_bits:raise SummaryError('Expanded semantic length bit budget exceeded')
        lengths.append(length)
    if not isinstance(roots,list) or not 1<=len(roots)<=8 or any(type(r)is not int or not 0<=r<len(nodes) for r in roots):
        raise SummaryError('Bounded ordered root goals required')
    return lengths


class CertifiedDagSummary(CertifiedSummary):
    """The frozen common certificate extends to DAGs by topological induction."""
    def run_dag(self,dag,*,max_nodes=100000,max_state_bits=65536,max_length_bits=8192):
        if type(max_state_bits)is not int or not 1<=max_state_bits<=65536:
            raise SummaryError('Bounded summary integer bit size required')
        if (identity(self._problem),identity(self._proposal))!=self._binding:
            raise SummaryError('Certificate/program binding changed')
        dag=deepcopy(dag)
        lengths=validate_dag(dag,max_nodes=max_nodes,max_length_bits=max_length_bits)
        nodes=dag['nodes'];wanted=set();pending=list(dag['roots'])
        while pending:
            index=pending.pop()
            if index in wanted:continue
            wanted.add(index)
            if nodes[index][0]=='concat':pending.extend(nodes[index][1:])
        states={};proposal=self._proposal
        for index in sorted(wanted):
            node=nodes[index]
            if node[0]=='nil':value=list(proposal['empty'])
            elif node[0]=='single':value=interpret(proposal['step'],[node[1]]+proposal['empty'])
            else:value=interpret(proposal['merge'],states[node[1]]+states[node[2]])
            if any(abs(v).bit_length()>max_state_bits for v in value):
                raise SummaryError('Generated summary integer bit budget exceeded')
            states[index]=value
        answers=[interpret(proposal['decode'],states[index]) for index in dag['roots']]
        if any(abs(v).bit_length()>max_state_bits for answer in answers for v in answer):
            raise SummaryError('Decoded integer bit budget exceeded')
        return {'outputs':answers,'input_nodes':len(nodes),'evaluated_nodes':len(wanted),
                'expanded_root_lengths':[lengths[index] for index in dag['roots']],
                'dag_sha256':identity(dag),'problem_sha256':self._binding[0],
                'proposal_sha256':self._binding[1],
                'scope':'ordered unfolded mathematical finite lists via certified summary; no materialized expansion',
                'expanded_length_is_speedup_claim':False}
