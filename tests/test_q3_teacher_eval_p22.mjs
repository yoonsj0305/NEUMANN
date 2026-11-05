import test from 'node:test';import assert from 'node:assert/strict';
import {FIRST_PROPOSALS,glyphType,componentsOf} from '../experiments/q3_teacher_eval_p22_FIRST_PROPOSAL.mjs';
const grid=lines=>lines.map(x=>x.split('').map(Number));
function gtype(lines){const g=grid(lines);return glyphType(componentsOf(g,1)[0]);}
test('C-like boundary and scaled U have shared analog class',()=>{assert.equal(gtype(['111','100','111']),'c_shape');assert.equal(gtype(['111','101','101','101']),'c_shape');assert.equal(gtype(['1111','0101','1111']),null);});
test('H and transposed H but not E',()=>{assert.equal(gtype(['101','111','101']),'h_shape');assert.equal(gtype(['11111','00100','11111']),'h_shape');assert.equal(gtype(['1000','1111','1000','1111','1000']),null);});
test('simple frame classified without foreground-specific task ID',()=>{assert.equal(gtype(['111','101','111']),'closed_1');assert.equal(gtype(['1111','1001','1001','1111']),'closed_1');});
test('two enclosed holes form a reusable multi-frame glyph',()=>{assert.equal(gtype(['11111','10101','11111']),'closed_2');});
test('patch positions assemble a 2x2 summary',()=>{const g=grid(['0000000000','0888888880','0811883380','0811883380','0888888880','0888882280','0888882280','0888888880']);assert.deepEqual(FIRST_PROPOSALS['19bb5feb'](g),[[1,3],[0,2]]);});
test('unique fully occupied 3x3 object with three colors is isolated',()=>{const g=grid(['00000000','01330000','01220000','01320000','00000000','00555000','00666000','00555000']);assert.deepEqual(FIRST_PROPOSALS['9a4bb226'](g),grid(['133','122','132']));});
test('count components plus one gives column of zeroes',()=>{const g=grid(['550000','550000','000000','000055','000055']);assert.deepEqual(FIRST_PROPOSALS['e872b94a'](g),[[0],[0],[0]]);});
test('fill zeros between first and last per-row anchors',()=>{const g=grid(['00030000','00303000','03000300','30000030']);assert.deepEqual(FIRST_PROPOSALS['aa18de87'](g),grid(['00030000','00323000','03222300','32222230']));});
test('unsupported task explicit ABSTAIN and malformed rejected',()=>{assert.equal(FIRST_PROPOSALS['759f3fd3'](grid(['00','00'])),null);assert.equal(FIRST_PROPOSALS['19bb5feb']([[0,1],[0]]),null);});
