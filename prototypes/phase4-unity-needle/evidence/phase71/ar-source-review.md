# Needle 5.1.12 — lectura del recorrido de materiales
Sin cambios en dependencias; no acredita ejecución AR física.

## engine/engine_context.ts:1128
```
1128: 	get isVisibleToUser() {
1129: 		if (this.isInXR) return true;
1130: 		if (!this._isVisible) return false;
1131: 		// Make sure not to call getComputedStyle multiple times per frame
1132: 		if (!this._needsVisibleUpdate && this._lastStyleComputedResult !== undefined) return this._lastStyleComputedResult;
1133: 		this._needsVisibleUpdate = false;
1134: 		const style = getComputedStyle(this.domElement);
1135: 		this._lastStyleComputedResult = style.visibility !== "hidden" && style.display !== "none" && style.opacity !== "0";
1136: 		return this._lastStyleComputedResult;
1137: 	}
1138: 	private _needsVisibleUpdate: boolean = true;
1139: 	private _lastStyleComputedResult: boolean | undefined = undefined;
1140: 
```

## engine/engine_context.ts:1758
```
1758: 			}
1759: 
1760: 			this.executeCoroutines(FrameEvent.OnBeforeRender);
1761: 			invokeLifecycleFunctions(this, FrameEvent.OnBeforeRender);
1762: 
1763: 			if (this._needsUpdateSize)
1764: 				this.updateSize();
1765: 
1766: 			if (this.pre_render_callbacks) {
1767: 				for (const i in this.pre_render_callbacks) {
1768: 					this.pre_render_callbacks[i](frame);
1769: 				}
1770: 			}
1771: 
1772: 			if (this._focusRect) {
1773: 				if (this.mainCamera instanceof PerspectiveCamera) {
1774: 					const settings = this.focusRectSettings;
1775: 					const dt = settings.damping > 0 ? this.time.deltaTime / settings.damping : 1;
1776: 					updateCameraFocusRect(this._focusRect, this.focusRectSettings, dt, this.mainCamera, this.renderer);
1777: 				}
```

## engine/engine_context.ts:1894
```
1894: 		if (this.composer && !this.isInXR) {
1895: 			// if a camera is passed in we need to check if we need to update the composer's camera
1896: 			if (camera && "setMainCamera" in this.composer) {
1897: 				const currentPassesCamera = this.composer.passes[0]?.mainCamera;
1898: 				if (currentPassesCamera != camera)
1899: 					this.composer.setMainCamera(camera);
1900: 			}
1901: 
1902: 			const backgroundColor = this.renderer.getClearColor(this._tempClearColor);
1903: 			const clearAlpha = this.renderer.getClearAlpha();
1904: 			this._tempClearColor2.copy(backgroundColor);
1905: 			this.renderer.setClearColor(backgroundColor.convertSRGBToLinear(), this.renderer.getClearAlpha());
1906: 			this.composer.render(this.time.deltaTime);
1907: 			this.renderer.setClearColor(this._tempClearColor2, clearAlpha); // restore clear color
1908: 		}
1909: 		else if (camera) {
1910: 			// Workaround for issue on Vision Pro – 
1911: 			// depth buffer is not cleared between eye draws, despite the spec...
1912: 			if (this.isInXR && DeviceUtilities.isMacOS())
1913: 				this.renderer.clearDepth();
1914: 			this.renderer.render(this.scene, camera);
1915: 		}
1916: 		this._isRendering = false;
1917: 		return true;
```

## engine/xr/NeedleXRSession.ts:908
```
908:     readonly session: XRSession;
909: 
910:     /** XR Session Mode: AR or VR */
911:     readonly mode: XRSessionMode;
912: 
913:     /** The framebuffer scale factor this session was started with. On this
914:      * version the engine never requests a custom scale, so it is always 1 —
915:      * the property exists so session-resolution handling (e.g. the App Clip
916:      * canvas scaling) reads one authoritative value. */
917:     readonly appliedFramebufferScaleFactor: number = 1;
918: 
919:     /**
```

## engine/xr/NeedleXRSession.ts:1339
```
1339: 
1340: 
1341:         // In the appclip we want to make sure the canvas resolution is correctly applied with the DPR  
1342:         // this change has been added to Needle Go AppClip in daa9c186e49fe9d6f14d200e307eb0664e35ad72
1343:         // But for an immediate fix for Needle Engine projects we also add it here.  
1344:         // We can most likely remove the folllowing block in march 2026
1345:         if (DeviceUtilities.isNeedleAppClip()) {
1346:             window.requestAnimationFrame(() => {
1347:                 const canvas = this.context.renderer.domElement;
1348:                 const dpr = window.devicePixelRatio || 1;
1349:                 const currentWidth = canvas.width;
1350:                 const currentHeight = canvas.height;
1351:                 // The NeedleGo polyfill renders through the canvas, so the canvas buffer
1352:                 // size IS the AR render resolution — apply the session's framebuffer
1353:                 // scale here too (a real WebXR framebuffer gets it via
1354:                 // setFramebufferScaleFactor; without this the App Clip silently renders
1355:                 // at full native DPR and e.g. the splat low preset's 0.8 scale is lost).
1356:                 const scale = dpr * this.appliedFramebufferScaleFactor;
1357:                 // Check if DPR is already applied (avoid double-scaling)
1358:                 const expectedWidth = Math.floor(window.innerWidth * scale);
1359:                 const expectedHeight = Math.floor(window.innerHeight * scale);
1360:                 if (Math.abs(currentWidth - expectedWidth) > 2 || Math.abs(currentHeight - expectedHeight) > 2) {
1361:                     canvas.width = expectedWidth;
1362:                     canvas.height = expectedHeight;
1363:                     console.debug("Applied DPR scaling for Needle AppClip XR session", dpr, this.appliedFramebufferScaleFactor, canvas.width, canvas.height);
1364:                 }
1365:             });
1366:         }
```

## engine-components/export/usdz/ThreeUSDZExporter.ts:2264
```
2264: 		// TODO does not help when a roughnessMap is used
2265: 		effectiveOpacity *= (1 - material.transmission * (1 - (material.roughness * 0.5)));
2266: 
2267: 	}
2268: 
2269: 	if ( material.map ) {
2270: 
2271: 		inputs.push( `${pad}color3f inputs:diffuseColor.connect = ${materialRoot}/${materialName}/${texName(material.map)}_diffuse.outputs:rgb>` );
2272: 
2273: 		// Enforce alpha hashing in QuickLook for unlit materials
2274: 		if (material instanceof MeshBasicMaterial && material.transparent && material.alphaTest == 0.0 && quickLookCompatible) {
2275: 			inputs.push( `${pad}float inputs:opacity.connect = ${materialRoot}/${materialName}/${texName(material.map)}_diffuse.outputs:a>` );
2276: 			haveConnectedOpacity = true;
2277: 			// see below – QuickLook applies alpha hashing instead of pure blending when
2278: 			// both opacity and opacityThreshold are connected
2279: 			inputs.push( `${pad}float inputs:opacityThreshold = ${0.0000000001}` );
2280: 			haveConnectedOpacityThreshold = true;
2281: 		}
2282: 		else if ( material.transparent ) {
2283: 
2284: 			inputs.push( `${pad}float inputs:opacity.connect = ${materialRoot}/${materialName}/${texName(material.map)}_diffuse.outputs:a>` );
2285: 			haveConnectedOpacity = true;
2286: 
2287: 		} else if ( material.alphaTest > 0.0 ) {
2288: 
2289: 			inputs.push( `${pad}float inputs:opacity.connect = ${materialRoot}/${materialName}/${texName(material.map)}_diffuse.outputs:a>` );
2290: 			haveConnectedOpacity = true;
2291: 			inputs.push( `${pad}float inputs:opacityThreshold = ${material.alphaTest}` );
2292: 			haveConnectedOpacityThreshold = true;
2293: 
2294: 		}
2295: 
2296: 		samplers.push( buildTexture( material.map, 'diffuse', quickLookCompatible, textures, material, usedUVChannels, material.color, effectiveOpacity ) );
2297: 
2298: 	} else {
2299: 
2300: 		inputs.push( `${pad}color3f inputs:diffuseColor = ${buildColor( material.color )}` );
```
