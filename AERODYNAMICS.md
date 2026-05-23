# 🌬️ AeroClass Wind Tunnel: The Aerodynamics Behind the Visuals

Welcome to the **AeroClass Aerodynamics Guide**! This document is designed for the "nerds" who want to know the real science behind our wind tunnel visualizer, but it is written in a way that **Year 9 students and STEM teachers** can easily understand and teach.

In our simulator, the blue lines and flowing spheres represent **streamlines** and **air particles** moving through a virtual wind tunnel at 100 km/h. Here is the science of how they behave around your vehicle design!

---

## 🎯 1. The Nose Stagnation Point & Flow Split

### 🤓 For the Nerds:
When oncoming air hits the absolute front center of a vehicle (the "bumper nose"), its local velocity drops to exactly **zero** relative to the car. This specific location is called the **Stagnation Point**. 
* According to **Bernoulli's Principle**, as velocity drops to zero, the kinetic energy is converted into static pressure. This is the point of **maximum positive pressure** ($C_p = 1.0$) on the entire vehicle. 
* Right at this point, the flow must decisively split: air molecules above the stagnation line are pushed upwards, and molecules below are pushed downwards into the underbody.

### 🏫 For Year 9s & Teachers:
Imagine spraying a garden hose directly at a flat brick wall. Right where the water hits the center of the brick, it stops dead in its tracks for a microsecond. Because more water is rushing in behind it, it has nowhere to go but to **split decisively**—some splashing straight up over the top, and some splashing down to the floor. 

In our simulator, you will see the air lines travel perfectly straight from the right side until they get **right next to the front bumper**, where they hit this invisible wall and split sharply up over the hood or down under the chassis!

---

## 🥞 2. Streamline Stacking & Compression (Boundary Layers)

### 🤓 For the Nerds:
Streamlines in a steady fluid flow represent the path of air parcels. By definition, **streamlines can never cross or merge** (because an air molecule cannot be in two places at once, and fluid velocity at any point is single-valued). 
* As air is squeezed over the curved hood and roof of the car, the streamlines are compressed together. 
* This compression represents **flow acceleration** (the Venturi/Bernoulli effect). Closer spacing means the air is traveling faster, which creates a **low-pressure zone** (suction/lift) over the roof.
* We model this using an **exponential deflection decay formula**:
  $$y_{geom} = seedY + h_{obstacle} \cdot e^{-\frac{height}{\lambda}}$$
  This ensures that streamlines close to the roof deflect the most, while higher lines deflect less. They compress together beautifully but **never merge or cross**, preserving distinct stacked layers.

### 🏫 For Year 9s & Teachers:
Think of streamlines like a giant deck of cards. When you squeeze the deck over a hump, the cards get pushed closer together, but they **never merge into a single giant card**! 

On your screen, as the air lines climb over the hood and windshield, they squeeze tightly together. This squeezing shows that the air is **speeding up** as it is forced over the car. Because fast-moving air has lower pressure, this actually sucks the car upwards (creating aerodynamic lift).

---

## ✂️ 3. Flow Separation & Shear Layers

### 🤓 For the Nerds:
Air has viscosity (stickiness) and mass (momentum). When air flows over a smooth, curving surface, it sticks to it (attached flow). However, when the surface drops off sharply at the rear of the vehicle (like a flat hatchback trunk or a sharp spoiler), the air's momentum prevents it from negotiating such a sharp, sudden turn.
* The boundary layer detaches from the solid surface, a phenomenon called **Flow Separation**.
* The boundary between the fast-moving free stream air and the slow-moving air behind the car is called the **Shear Layer**. We model this by keeping the effective roof profile height high behind the car, letting the streamlines shoot straight back horizontally rather than curving down to hug the empty ground.

### 🏫 For Year 9s & Teachers:
Imagine riding a skateboard at high speed toward a curb. If the curb drops off suddenly, you don't instantly glue your wheels down the vertical face of the curb—your speed carries you **flying straight off the edge** into the air!

The same thing happens to air. When the car's body ends sharply at the back, the air can't turn that sharp corner. It shoots straight off the rear spoiler into the empty air, **separating** from the vehicle's body.

---

## 🌪️ 4. Low-Pressure Recirculation Wake & Chaotic Turbulence

### 🤓 For the Nerds:
Because the air separates and shoots straight off the back of the vehicle, it leaves behind a hollow cavity directly behind the rear bumper. This cavity is a **massive low-pressure zone (vacuum)**. 
* Because nature abhors a vacuum, the surrounding high-pressure air is sucked backwards into this void, creating a **Recirculation Zone**.
* In a real wind tunnel, this forms a **turbulent wake** made of chaotic, swirling eddies. 
* We model this by applying a **3D orbital looping displacement** to the path points in the wake cavity:
  $$x_{offset} = r \cdot \cos(\theta), \quad y_{offset} = r \cdot \sin(\theta)$$
  This forces the particles to **literally loop back on themselves in tight circles**!
* We overlay this with **multi-frequency chaotic noise** (fractional Brownian motion made of overlapping prime-frequency sine waves) to simulate the unpredictable, messy eddies of turbulent air.

### 🏫 For Year 9s & Teachers:
When a bus drives past at high speed, you might feel a gust of wind blowing *in the same direction* as the bus, sucking leaves and dust behind it. This is because the flat back of the bus acts like a giant plunger, leaving an empty "pocket" of low pressure behind it that sucks the surrounding air in.

In our wind tunnel, look at the area behind the rear bumper (on the left). You will see the glowing blue particles **literally loop backward in circles**, swirling towards the bumper before breaking apart into chaotic, wavy, unpredictable currents. This swirling wake is the primary cause of **aerodynamic drag** (the force pulling the car back)!

---

## 🏎️ 5. Underbody Ground Effect & Road Turbulence

### 🤓 For the Nerds:
The gap between the bottom of the vehicle (the chassis) and the road acts as a narrow channel. As air is forced under the car, the moving road (our moving floor grid) and the rough underbody (wheels, axles, suspension) disrupt the flow.
* The air passing underneath compresses and accelerates, creating a Venturi effect that generates **downforce** (suction that pulls the car toward the track).
* However, the wheels and rough components break this clean air into a highly turbulent, messy boundary layer. We model this by applying high-frequency, decaying turbulent oscillations underneath the chassis, showing the air shaking and breaking apart.

### 🏫 For Year 9s & Teachers:
The space under a racecar is a highly competitive zone! Racecar designers try to make the underside as flat as possible so air can rush through incredibly fast, sucking the car down to the road so it can corner at high speeds. 

In our simulator, look closely at the lines running under the wheels. You will see them compress, speed up, and start **waving and shaking rapidly** (turbulence) as they hit the wheels and road, showing how messy the air gets underneath the vehicle!
