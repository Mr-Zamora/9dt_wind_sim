# AeroClass - Errors Encountered and Fixed

This document tracks all errors encountered during development and their resolutions.

---

## 1. UnicodeEncodeError on Windows Console

**Error:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713' in position 0: character maps to <undefined>
```

**Location:** 
- `physics_engine/demo.py` (emoji characters in print statements)
- `backend/main.py` (emoji characters in debug print statements)

**Cause:** Windows console uses cp1252 encoding which doesn't support Unicode emoji characters.

**Fix:** 
- Removed all emoji characters from print statements
- Replaced with plain text indicators (e.g., "[DRAG]", "[COMPLETE]")

**Status:** ✅ FIXED

---

## 2. Unrealistic Vehicle Mass Calculation

**Error:**
- Vehicle mass calculated as 10,449 kg (unrealistic for a sedan)
- Top speed only 172 km/h (too low for 150 HP)

**Location:** `physics_engine/performance_calc.py`

**Cause:** Mass calculation used full bounding box volume as if vehicle were solid, but vehicles are hollow shells.

**Fix:**
- Added structural factor of 0.12 (12%) to account for hollow vehicle body
- Mass = volume × structural_factor × material_density
- Updated SPEC_REVISED.md to document this assumption

**Status:** ✅ FIXED

---

## 3. KeyError: 'length' in Drag Estimator

**Error:**
```
KeyError: 'length'
File "drag_estimator.py", line 152, in _estimate_nose_radius
    threshold = front_x + self.features['length'] * 0.1
```

**Location:** `physics_engine/drag_estimator.py`

**Cause:** Methods `_estimate_nose_radius()`, `_estimate_rear_taper()`, and `_estimate_underbody_flatness()` tried to access `self.features['length']` while the features dictionary was still being built (circular dependency).

**Fix:**
- Changed method signatures to accept parameters directly
- `_estimate_nose_radius(vertices, front_x, length)` - receives length as parameter
- `_estimate_rear_taper(vertices, rear_x, length)` - receives length as parameter
- `_estimate_underbody_flatness(vertices, height)` - receives height as parameter

**Status:** ✅ FIXED

---

## 4. Slow Volume Calculation (Timeout)

**Error:** Upload and analysis timing out on large STL files (90,000 triangles)

**Location:** `physics_engine/geometry_analyzer.py`

**Cause:** Voxel-based volume calculation was too slow for educational use.

**Fix:**
- Changed from voxel method to convex hull method
- Reduced calculation time from 30+ seconds to <5 seconds
- Set volume confidence to 85% (convex hull is slightly less accurate but sufficient for educational use)

**Status:** ✅ FIXED

---

## 5. FastAPI Static File Serving (Blank Screen)

**Error:** UI pages showing blank screen when accessed via FastAPI at http://localhost:8000/ui/

**Location:** `backend/main.py`

**Cause:** Static files mounting order - routes were mounted after static files, causing conflicts.

**Fix:**
- Reordered: API routes first, then root endpoint, then static files last
- Added debug logging to verify UI path exists
- Removed unused StaticFiles import

**Status:** ✅ FIXED

---

## 6. JSON Serialization Error (Numpy Types)

**Error:**
```
ValueError: [TypeError("'numpy.float32' object is not iterable"), TypeError('vars() argument must have __dict__ attribute')]
```

**Location:** 
- `backend/routers/simulations.py` (simulation endpoint)
- `backend/routers/designs.py` (design info endpoint)

**Cause:** FastAPI's jsonable_encoder cannot serialize numpy types (np.float32, np.int64, etc.) to JSON.

**Fix:**
- Created `convert_numpy_types()` helper function
- Converts numpy integers to Python int
- Converts numpy floats to Python float
- Converts numpy arrays to Python lists
- Applied conversion before building API responses in both endpoints

**Status:** ✅ FIXED

---

## 7. JavaScript DOMContentLoaded Issue

**Error:** JavaScript event listeners not attaching, buttons not responding

**Location:** `UI_test/simulator.html`

**Cause:** JavaScript code executed before DOM was fully loaded.

**Fix:**
- Wrapped all JavaScript in `document.addEventListener('DOMContentLoaded', function() {...})`
- Ensures DOM is ready before attaching event listeners

**Status:** ✅ FIXED

---

## 8. Material Dropdown Selector Error

**Error:**
```
Uncaught (in promise) TypeError: Cannot read properties of null (reading 'value')
    at HTMLButtonElement.<anonymous> (simulator.html:732:65)
```

**Location:** `UI_test/simulator.html`

**Cause:** JavaScript trying to access `document.getElementById('material').value` but element doesn't have that ID.

**Status:** ⚠️ NOT YET FIXED - Needs investigation of HTML dropdown IDs

---

## 9. Design Info Endpoint 500 Error

**Error:**
```
Failed to load resource: the server responded with a status of 500 (Internal Server Error)
Failed to load design info: SyntaxError: Unexpected token 'I', "Internal S"... is not valid JSON
```

**Location:** `backend/routers/designs.py` GET endpoint

**Cause:** Same numpy serialization error as #6, in the design info endpoint.

**Fix:** Applied same `convert_numpy_types()` conversion to design info endpoint.

**Status:** ✅ FIXED (after server restart)

---

## 10. Server Auto-Reload Not Working

**Error:** Changes to code not being picked up by auto-reload, requiring manual restarts

**Location:** FastAPI uvicorn server

**Cause:** WatchFiles sometimes fails to detect changes or gets stuck in reload loop.

**Fix:** Manual server restarts using `taskkill /F /IM python.exe` then `python main.py`

**Status:** ⚠️ WORKAROUND - Manual restarts required

---

## Summary

**Total Errors:** 10
**Fixed:** 8
**Workaround:** 1
**Pending:** 1

### Remaining Issues:
1. Material dropdown selector ID mismatch (needs HTML inspection)
2. Server auto-reload reliability (workaround: manual restart)

### Key Learnings:
- Windows console encoding limitations with Unicode
- Numpy types require explicit conversion for JSON serialization
- Circular dependencies in class initialization need parameter passing
- Static file mounting order matters in FastAPI
- DOMContentLoaded needed for JavaScript in HTML files
