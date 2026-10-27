# Technical Guide: Descent Rate (FPM) vs. Simulator Vertical Speed (Sim VS) in Stratos

**Context:** Walker Air Flight Telemetry & Stratos Landing Analyser  
**Source Code References:**  
- `%APPDATA%\Stratos\plugins\landing-analyser\ui\index.js`  
- `%APPDATA%\Stratos\plugins\landing-analyser\background\index.js`  
- `%APPDATA%\Stratos\plugins-data\landing-analyser\landing-analyser.db`  

---

## 1. The Core Difference

In the Walker Air and Stratos landing telemetry logs, there are two separate columns for vertical speed:

| Column Name | What It Actually Is | How It Is Measured | Behavior in Flight |
| :--- | :--- | :--- | :--- |
| **Descent fpm** | **True Geometric Descent Rate** | Calculated directly from how fast the wheels are approaching the ground. | Instantaneous and physically exact. Measures the true touchdown impact rate. |
| **Sim VS** | **Cockpit Instrument Needle** | Read directly from the flight simulator's cockpit vertical speed gauge. | Filtered and delayed. Exhibits a noticeable **0.5 to 1.0 second lag** behind real motion. |

---

## 2. Official Stratos Definitions

Hovering over the column headers in the Stratos desktop app displays the official developer tooltips:

- **Descent fpm Tooltip:**  
  *"Geometric descent rate from gear-AGL changes — unfiltered, unlike the sim's smoothed VS readout"*
- **Sim VS Tooltip:**  
  *"Simulator's vertical-speed readout (smoothed, lags reality by ~0.5–1.0s — visible as the trailing decay during rollout)"*

---

## 3. How Stratos Calculates Descent FPM

Instead of trusting the delayed cockpit gauge, Stratos calculates the true descent rate on the fly by looking at how fast the aircraft's altitude above ground (AGL) is changing.

### The 4 Practical Steps

1. **Look Back Half a Second:**  
   Every time a new row of data is recorded, the computer looks back over the previous 500 milliseconds (half a second) of flight history.  
   *Rule:* It never mixes airborne readings with on-ground readings. As soon as the wheels touch down, the history resets so rollout measurements don't contaminate the landing rate.

2. **Verify Enough Data Exists:**  
   To avoid calculating wild speeds from just one or two jittery points, Stratos enforces two safety rules:
   - There must be at least 5 recorded frames in that half-second window.
   - The time span between the oldest and newest reading must be at least 100 milliseconds (1/10th of a second).  
   If these conditions are not met (such as during the first few moments of recording or right after touchdown), Stratos prints a dash (**—**).

3. **Calculate the Rate of Drop:**  
   The computer calculates the trend line (linear regression) through the altitude points collected in that half-second. This gives the exact altitude drop in **feet per millisecond**.

4. **Convert to Feet per Minute:**  
   Because there are 60,000 milliseconds in one minute, multiplying the drop-per-millisecond by 60,000 gives the standard aviation metric: **Feet per Minute (FPM)**.

---

### Original Minified Code (Stratos)

Directly from `%APPDATA%\Stratos\plugins\landing-analyser\ui\index.js`:

```javascript
function Tn(e, r, n = 500) {
  const i = e[r].t - n, s = e[r].onGround, l = [];
  for (let p = r; p >= 0 && !(e[p].t < i || e[p].onGround !== s); p--)
    l.unshift(e[p]);
  if (l.length < 5) return null;
  const u = l[0].t;
  if (l[l.length - 1].t - u < 100) return null;
  let c = 0, x = 0;
  for (const p of l)
    c += p.t - u, x += p.agl;
  c /= l.length, x /= l.length;
  let v = 0, f = 0;
  for (const p of l) {
    const b = p.t - u - c;
    v += b * (p.agl - x), f += b * b;
  }
  return f === 0 ? null : v / f * 6e4;
}
```

---

### Readable Translation (JavaScript)

Here is the exact same function rewritten with clear variable names and step-by-step comments:

```javascript
// ========================================================
// Calculate Geometric Descent Rate in Feet per Minute (FPM)
// ========================================================
function calculateDescentFpm(recordedFrames, currentRowIndex) {
  const windowMilliseconds = 500; // Look back over the last half-second
  const minSamplesRequired = 5;   // Need at least 5 readings to be reliable
  const minTimeSpanMs = 100;      // Need at least 100 ms between first and last reading

  const currentFrame = recordedFrames[currentRowIndex];
  const currentTimeMs = currentFrame.timeMs;
  const currentGroundState = currentFrame.onGround;

  // ------------------------------------------------------
  // Step 1: Collect readings from the last 500 milliseconds
  // ------------------------------------------------------
  const windowFrames = [];
  for (let i = currentRowIndex; i >= 0; i--) {
    const frame = recordedFrames[i];
    const timeDifference = currentTimeMs - frame.timeMs;

    // Stop if older than 500 ms or if we cross the touchdown boundary
    if (timeDifference > windowMilliseconds || frame.onGround !== currentGroundState) {
      break;
    }
    // Add this frame to our recent history window
    windowFrames.unshift(frame);
  }

  // ------------------------------------------------------
  // Step 2: Safety check - verify we have enough data
  // ------------------------------------------------------
  if (windowFrames.length < minSamplesRequired) {
    return "—"; // Not enough points yet, show a dash
  }

  const oldestTimeMs = windowFrames[0].timeMs;
  const newestTimeMs = windowFrames[windowFrames.length - 1].timeMs;
  if (newestTimeMs - oldestTimeMs < minTimeSpanMs) {
    return "—"; // Time span is too short, show a dash
  }

  // ------------------------------------------------------
  // Step 3: Find average time and average altitude
  // ------------------------------------------------------
  let totalTime = 0;
  let totalAltitude = 0;
  for (const frame of windowFrames) {
    totalTime += (frame.timeMs - oldestTimeMs);
    totalAltitude += frame.altitudeAgl;
  }
  const averageTime = totalTime / windowFrames.length;
  const averageAltitude = totalAltitude / windowFrames.length;

  // ------------------------------------------------------
  // Step 4: Calculate the trend slope (drop per millisecond)
  // ------------------------------------------------------
  let numerator = 0;
  let denominator = 0;
  for (const frame of windowFrames) {
    const deltaTime = (frame.timeMs - oldestTimeMs) - averageTime;
    const deltaAltitude = frame.altitudeAgl - averageAltitude;

    numerator += deltaTime * deltaAltitude;
    denominator += deltaTime * deltaTime;
  }

  if (denominator === 0) {
    return "—";
  }

  const dropPerMillisecond = numerator / denominator;

  // ------------------------------------------------------
  // Step 5: Convert to Feet per Minute (60,000 ms in 1 minute)
  // ------------------------------------------------------
  const descentRateFpm = dropPerMillisecond * 60000;
  return Math.round(descentRateFpm);
}
```

---

## 4. Practical Flight Factors Explained

### A. Landing Gear Height Detection & Calibration

Flight simulators measure an aircraft's height from the center of the airplane (the middle of the fuselage), not from the bottom of the tires. 

Because of this, even when your wheels are firmly rolling on the runway, the simulator's raw altitude reading is never zero—it still reads roughly **4 feet** in a Cessna 172, and **12 to 16 feet** in an airliner.

To make landing analysis useful, Stratos has to zero the scale so that **0.0 ft means your wheels are touching the runway**. It does this automatically using a calibration system in its core engine (`%APPDATA%\Stratos\core\core.mjs`):

1. **Preflight Ground Sampling:**  
   During ground operations—specifically while the aircraft is in `PUSH_BACK` or `TAXI` state and `planeOnground = true`—Stratos continuously collects samples of the raw gear altitude into a buffer (`gearOffsetSamples`).

2. **Calculating the Ground Offset:**  
   From these ground samples, Stratos establishes a fixed baseline offset for that specific aircraft model:
   ```javascript
   // In Stratos core.mjs:
   this.gearAglGroundOffset = t.altitudeAglGear;
   ```

3. **In-Flight Real-Time Zeroing:**  
   During flight and landing, Stratos continuously subtracts this calibrated baseline offset from every incoming frame sample:
   ```javascript
   // In Stratos core.mjs:
   e.altitudeAglGear = Math.round((e.altitudeAglGear - this.gearAglGroundOffset) * 10) / 10;
   ```
   This ensures that regardless of whether you fly a light Cessna or a commercial airliner, the altitude reading (`AGL ft`) is calibrated so that **`0.0 ft` represents the exact moment the tires touch the runway in a level attitude**.

---

### B. Runway Slope: Why Sim VS Can Read Positive During an Uphill Landing

Runway slope creates a dramatic divergence between `Descent fpm` and `Sim VS` because they operate in two completely different frames of reference:

- **`Descent fpm` is Terrain-Relative:** It measures the rate at which the distance between the tires and the runway surface directly below is closing.
- **`Sim VS` is Sea-Level Relative:** It measures vertical velocity relative to the earth's global sea-level plane, with no awareness of the ground elevation beneath the aircraft.

#### Why Sim VS Can Be Positive When Landing on an Incline:
When landing on an uphill runway (such as Courchevel, Lukla, or an inclined airstrip), the runway elevation rises in front of you. To land smoothly without flying straight into the hill, the pilot flares to align the flight path with the upward slope of the runway.

1. **Physical Climb Relative to Sea Level:**  
   At a typical touchdown groundspeed of **60 knots**, the aircraft travels forward at approximately **100 feet per second**.
2. If the runway has a **3% uphill grade** (rising 3 feet for every 100 feet forward):
   - Flying or rolling along that slope means the aircraft is physically gaining **3 feet of sea-level altitude every second**.
   - Converted to aviation units:
     ```text
     Vertical Climb Rate = 3 ft/s * 60 s/min = +180 FPM
     ```
3. **The Result at Touchdown:**  
   - **`Descent fpm`** correctly records a descent or landing impact rate (e.g., -150 FPM) because the tires are closing with and compressing onto the asphalt.
   - **`Sim VS`** simultaneously displays a **positive climb (+180 FPM)** because the aircraft is physically ascending relative to sea level.

#### During Rollout on an Incline:
Once all wheels are firmly on the ground:
- **`Descent fpm`** settles to **`0 FPM`** (the distance between tires and runway surface is no longer changing).
- **`Sim VS`** continues to read a **positive climb (+150 to +300 FPM)** as long as the aircraft rolls uphill, because the plane is literally driving up an inclined plane.

---

### C. Ground Irregularities (Bumps, Dips & Surface Undulations)

Ground irregularities (such as runway humps, frost heaves, pavement seams, or grass mounds on unpaved strips) directly impact the geometric descent calculation because **`Descent fpm` cannot distinguish between an airplane sinking and the ground rising beneath it.**

1. **The Moving Ground Effect:**
   - **A 2-inch bump in the runway:** As the aircraft flies over a slight rise, the distance between the tires and the ground suddenly shrinks. The formula interprets this rapid closure as the airplane suddenly sinking faster, causing an instantaneous **spike in negative descent rate** (e.g. an extra -50 to -100 FPM).
   - **A 2-inch dip or depression:** As the ground dips away, the distance momentarily expands or stays flat. The formula interprets this as the descent leveling off or even **momentarily climbing (+FPM)**.

2. **Why High Forward Speed Amplifies Micro-Bumps:**
   - At a typical touchdown groundspeed of **70 knots**, the aircraft travels forward at roughly **118 feet per second**.
   - Stratos calculates descent using a **500 ms (half-second)** lookback window. In that half-second, the aircraft covers **59 feet of runway**.
   - A surface contour change of **just 2 inches (0.17 ft)** over a tenth of a second calculates to:
     ```text
     Rate Spike = (0.17 ft / 0.1 s) * 60 s/min ≈ 100 FPM
     ```
   Even micro-terrain variations you would barely notice in a car register on telemetry as an apparent 100 FPM speed change.

3. **Contrast with Cockpit `Sim VS`:**
   - **`Sim VS` is completely immune** to ground irregularities while in the air because air pressure does not change when passing over a pavement bump.
   - **`Descent fpm` tracks every contour** of the ground surface directly below the wheels. Initial contact on the rising face of a bump will score a harder landing rate, while touching down on the descending backside of an undulation yields a gentler score.

---

### D. Why Sim VS Lags Reality
In real aircraft, a mechanical Vertical Speed Indicator (VSI) does not measure movement directly. It measures changes in air pressure leaking through a calibrated pinhole into a small diaphragm capsule. 

This creates an unavoidable physical delay of **0.5 to 1.5 seconds**:
- **During the Flare:** If the pilot pulls back on the yoke and arrests the descent from -400 FPM down to -150 FPM in half a second, the cockpit needle is still slowly swinging downward and reads -300 FPM.
- **At Touchdown:** When the wheels hit the tarmac, the cockpit needle is typically only halfway to the true impact rate.
- **During Rollout:** Once rolling on the ground, true vertical speed is 0 FPM. However, the cockpit gauge needle slowly decays over 1 to 2 seconds (e.g. -120 → -80 → -40 → 0 FPM).

---

### E. Aircraft Pitch and Bank (Attitude)
Stratos does **not** perform complex 3D trigonometric rotations for pitch and bank during descent calculations:
1. **Pre-Takeoff Zeroing:** While the airplane is parked on the ramp or taxiing before flight, Stratos samples the aircraft on the ground to record a baseline gear offset (`gearAglGroundOffset`).
2. **Fixed Height Subtraction:** During flight, Stratos simply subtracts this fixed number from the simulator's gear altitude reading so that flat touchdown reads `0.0 ft`.
3. **The Flare Rotation Effect:** Because main landing gear sits behind the aircraft center of gravity, pitching the nose up into the flare swings the main wheels downward toward the runway. Stratos reads this geometric closure directly as altitude loss without trying to separate body rotation from vertical movement.
4. **Wing-Low Crosswinds:** In a crosswind landing with one wing lowered into the wind, one tire touches down before the other. Stratos does not calculate separate left and right tire elevations; it triggers the touchdown event at the exact instant the flight simulator reports `onGround = true`.

---

## 5. How the Flare Phase is Detected

Stratos does not use a rigid altitude cutoff to decide when you started flaring. Instead, it looks for the pilot's control action:

1. It monitors frames where altitude is below **50 feet AGL** before touchdown.
2. It looks for the **inflection point** where vertical speed stops getting steeper and begins leveling off (where each new frame is descending slower than the previous one).
3. The exact frame where that deceleration begins is tagged as the start of the **Flare** phase. All frames before that point are tagged as **Approach**.

---

## 6. Post-Touchdown Oscillations (Why Descent FPM Fluctuates on Rollout)

In the telemetry logs, you will notice that even after the wheels are firmly on the ground, `Descent fpm` continues to fluctuate between negative numbers (descent) and positive numbers (climb) before settling. 

This happens because the calculation measures the physical motion of the aircraft body relative to the runway surface:

1. **Shock Strut Compression and Spring Rebound:**
   - When the aircraft touches down, the oleo-pneumatic shock struts and rubber tires compress under the dynamic impact load (typically compressing 3 to 4 inches). 
   - Because the aircraft fuselage is moving closer to the ground while the struts compress, Stratos registers this as a continued descent (e.g. -110 FPM).
   - Once the impact energy is absorbed, the pressurized struts spring back up (rebound), pushing the aircraft body slightly higher. This upward motion reads as an apparent climb (e.g. +120 FPM). The aircraft bobs up and down for a second or two until the struts settle.

2. **Nosewheel Derotation (Lowering the Nose):**
   - At touchdown, the aircraft is held in a nose-up flare attitude with only the main gear touching the pavement.
   - Over the next second, the pilot lowers the nose onto the runway.
   - Because the main landing gear acts as a pivot, rotating the fuselage forward tilts the airframe and moves the reference sensor up or down relative to the runway, creating an apparent vertical speed.

3. **High Mathematical Sensitivity:**
   - Because the formula converts tiny millisecond changes into feet per minute (multiplying by 60,000), even microscopic movements show up as significant numbers.
   - A runway undulation, seam, or tire bounce of **just 1 inch over a tenth of a second** mathematically calculates to nearly **50 FPM**.
   - Stratos does not turn off the calculation after touchdown—it continues to report the real, unfiltered mechanical motion of the airframe as it rolls down the runway.
