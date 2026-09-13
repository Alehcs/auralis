import test from 'node:test';
import assert from 'node:assert/strict';
import {describeAR,shareable} from '../src/capabilities.mjs';
test('insecure LAN never presented as AR-capable',()=>assert.match(describeAR({secure:false,immersiveAR:true,ios:false,error:false}),/HTTPS/));
test('iPhone without WebXR distinguishes App Clip from Safari',()=>assert.match(describeAR({secure:true,immersiveAR:false,ios:true,error:false}),/No es WebXR nativo/));
test('unsupported desktop retains 3D',()=>assert.match(describeAR({secure:true,immersiveAR:false,ios:false,error:false}),/explorar el objeto en 3D/));
test('capability exception preserves 3D',()=>assert.match(describeAR({secure:true,immersiveAR:false,ios:false,error:true}),/modo 3D sigue/));
test('support probe is not proof of placement',()=>assert.match(describeAR({secure:true,immersiveAR:true,ios:false,error:false}),/aún deben probarse/));
test('localhost is not a phone sharing URL',()=>{for(const url of ['http://localhost:5184/','https://localhost/','https://127.0.0.1/','https://[::1]/','http://192.168.1.99:5184/']) assert.equal(shareable(url),false);assert.equal(shareable('https://example.com/probe/?scene=unity'),true);});
