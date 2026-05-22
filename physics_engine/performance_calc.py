"""
Performance Calculator
Top speed prediction, acceleration simulation, Reynolds number corrections
"""

import numpy as np
from typing import Dict, Tuple


class PerformanceCalculator:
    """Calculate vehicle performance metrics"""
    
    # Physical constants
    RHO_AIR = 1.225  # kg/m³ at sea level, 15°C
    MU_AIR = 1.81e-5  # Dynamic viscosity of air (Pa·s)
    G = 9.81  # Gravitational acceleration (m/s²)
    ROLLING_RESISTANCE_COEFF = 0.015  # Typical for car tires on asphalt
    
    # Material densities (kg/m³)
    MATERIALS = {
        'foam_composite': 1600,  # Classroom Composite: carved blue foam + plastic vacuum shell & plastic hardware
        'carbon_fiber': 1750,
        'aluminum': 2700,
        'steel': 7850,
        'abs_plastic': 1040,
        'balsa_wood': 130
    }
    
    def __init__(self, 
                 cd: float,
                 frontal_area: float,
                 volume: float,
                 material: str = 'aluminum',
                 custom_mass_kg: float = None):
        """
        Initialize performance calculator
        
        Args:
            cd: Drag coefficient
            frontal_area: Frontal area in m²
            volume: Vehicle volume in m³
            material: Material name (from MATERIALS dict)
            custom_mass_kg: Optional custom mass override in kg
        """
        self.cd = cd
        self.frontal_area = frontal_area
        self.volume = volume
        self.material = material
        self.custom_mass_kg = custom_mass_kg
        self.mass = custom_mass_kg if custom_mass_kg is not None else self._calculate_mass()
        
    def _calculate_mass(self) -> float:
        """
        Calculate vehicle mass from volume and material density
        
        Note: Vehicles are hollow shells, not solid blocks. We apply a structural
        factor to estimate actual material volume. Typical vehicles use 10-15% of
        their bounding box volume as actual material (body panels, frame, etc.)
        """
        density = self.MATERIALS.get(self.material, self.MATERIALS['aluminum'])
        
        # Structural factor: percentage of bounding volume that is actual material
        # 12% is typical for automotive construction (hollow body, interior space)
        structural_factor = 0.12
        
        return self.volume * density * structural_factor

    def _get_scaled_properties(self, length: float, scale_mode: str) -> Tuple[float, float, float]:
        """
        Get scaled length, frontal area, and mass for the given scale mode
        
        Args:
            length: Original length of the vehicle (m)
            scale_mode: 'miniature' or 'full_scale'
            
        Returns:
            Tuple of (scaled_length, scaled_frontal_area, scaled_mass)
        """
        density = self.MATERIALS.get(self.material, self.MATERIALS['aluminum'])
        structural_factor = 0.12
        
        if self.custom_mass_kg is not None:
            scaled_mass = self.custom_mass_kg
        else:
            scaled_mass = self.volume * density * structural_factor
            
        if scale_mode == 'miniature':
            return length, self.frontal_area, scaled_mass
        elif scale_mode == 'full_scale':
            if length >= 3.0:  # already full-scale
                return length, self.frontal_area, scaled_mass
            scale_factor = 4.5 / max(length, 0.01)
            scaled_length = 4.5
            scaled_frontal_area = self.frontal_area * (scale_factor ** 2)
            
            if self.custom_mass_kg is not None:
                scaled_mass = self.custom_mass_kg * (scale_factor ** 3)
            else:
                scaled_mass = self.volume * (scale_factor ** 3) * density * structural_factor
            return scaled_length, scaled_frontal_area, scaled_mass
        return length, self.frontal_area, scaled_mass
    
    def apply_reynolds_correction(self, 
                                  velocity: float,
                                  length: float,
                                  scale_mode: str = 'full_scale') -> Tuple[float, float]:
        """
        Apply Reynolds number correction to drag coefficient
        
        Args:
            velocity: Velocity in m/s
            length: Characteristic length in meters
            scale_mode: 'miniature' or 'full_scale'
            
        Returns:
            Tuple of (corrected_cd, reynolds_number)
        """
        # Calculate Reynolds number
        reynolds = (self.RHO_AIR * velocity * length) / self.MU_AIR
        
        cd_corrected = self.cd
        
        if scale_mode == 'miniature':
            # Miniature models have higher Cd due to laminar flow
            if reynolds < 1e5:
                cd_corrected = self.cd * 1.25  # +25% drag penalty
            elif reynolds < 5e5:
                cd_corrected = self.cd * 1.15  # +15% drag penalty
            else:
                cd_corrected = self.cd * 1.05  # +5% drag penalty
        
        elif scale_mode == 'full_scale':
            # Full-scale benefits from turbulent boundary layer
            if reynolds > 1e6:
                cd_corrected = self.cd * 0.92  # -8% drag reduction
            else:
                cd_corrected = self.cd
        
        return cd_corrected, reynolds
    
    def calculate_top_speed(self, 
                           power_watts: float,
                           length: float = 4.5,
                           scale_mode: str = 'full_scale') -> Dict:
        """
        Calculate theoretical top speed where power = drag power
        
        Args:
            power_watts: Engine power in Watts
            length: Vehicle length in meters
            scale_mode: 'miniature' or 'full_scale'
            
        Returns:
            Dictionary with top speed analysis
        """
        # Get scaled properties
        scaled_length, scaled_frontal_area, scaled_mass = self._get_scaled_properties(length, scale_mode)

        # Iterative solver to find velocity where P_engine = P_drag + P_rolling
        v_guess = 50.0  # Initial guess (m/s)
        tolerance = 0.01
        max_iterations = 100
        
        for _ in range(max_iterations):
            # Get Reynolds-corrected Cd at this velocity
            cd_corrected, reynolds = self.apply_reynolds_correction(
                v_guess, scaled_length, scale_mode
            )
            
            # Calculate drag force
            drag_force = 0.5 * self.RHO_AIR * (v_guess ** 2) * cd_corrected * scaled_frontal_area
            
            # Calculate rolling resistance
            rolling_force = self.ROLLING_RESISTANCE_COEFF * scaled_mass * self.G
            
            # Total resistance force
            total_force = drag_force + rolling_force
            
            # Power required at this velocity
            power_required = total_force * v_guess
            
            # Adjust velocity guess
            if abs(power_required - power_watts) < tolerance:
                break
            
            # Newton's method adjustment
            v_guess = v_guess * (power_watts / max(power_required, 1.0)) ** 0.33
            
            # Safety bounds
            v_guess = max(1.0, min(v_guess, 150.0))
        
        # Convert to km/h
        v_top_kmh = v_guess * 3.6
        
        # Power breakdown
        aero_power = drag_force * v_guess
        rolling_power = rolling_force * v_guess
        
        return {
            'top_speed_ms': v_guess,
            'top_speed_kmh': v_top_kmh,
            'reynolds_number': reynolds,
            'cd_corrected': cd_corrected,
            'drag_force_n': drag_force,
            'rolling_force_n': rolling_force,
            'power_breakdown': {
                'aerodynamic_watts': aero_power,
                'rolling_watts': rolling_power,
                'aerodynamic_pct': (aero_power / power_watts) * 100,
                'rolling_pct': (rolling_power / power_watts) * 100
            }
        }
    
    def simulate_acceleration(self,
                             power_watts: float,
                             target_velocity_kmh: float = 100.0,
                             length: float = 4.5,
                             scale_mode: str = 'full_scale',
                             dt: float = 0.01) -> Dict:
        """
        Simulate 0-to-target acceleration using time-step integration
        
        Args:
            power_watts: Engine power in Watts
            target_velocity_kmh: Target velocity in km/h (default: 100)
            length: Vehicle length in meters
            scale_mode: 'miniature' or 'full_scale'
            dt: Time step in seconds
            
        Returns:
            Dictionary with acceleration results
        """
        # Get scaled properties
        scaled_length, scaled_frontal_area, scaled_mass = self._get_scaled_properties(length, scale_mode)

        target_velocity_ms = target_velocity_kmh / 3.6
        
        # Traction limit (simplified - assume AWD with good tires)
        max_traction_force = 0.8 * scaled_mass * self.G  # ~0.8g acceleration limit
        
        # Initialize
        v = 0.1  # Start at 0.1 m/s to avoid division by zero
        t = 0.0
        
        # Track history
        time_history = [0.0]
        velocity_history = [0.0]
        acceleration_history = [0.0]
        
        max_time = 60.0  # Safety timeout
        
        while v < target_velocity_ms and t < max_time:
            # Get Reynolds-corrected Cd
            cd_corrected, _ = self.apply_reynolds_correction(v, scaled_length, scale_mode)
            
            # Calculate forces
            thrust_force = min(power_watts / v, max_traction_force)
            drag_force = 0.5 * self.RHO_AIR * (v ** 2) * cd_corrected * scaled_frontal_area
            rolling_force = self.ROLLING_RESISTANCE_COEFF * scaled_mass * self.G
            
            # Net force and acceleration
            net_force = thrust_force - drag_force - rolling_force
            acceleration = net_force / scaled_mass
            
            # Update velocity and time
            v += acceleration * dt
            t += dt
            
            # Record every 0.1 seconds
            if len(time_history) == 0 or t - time_history[-1] >= 0.1:
                time_history.append(t)
                velocity_history.append(v * 3.6)  # Convert to km/h
                acceleration_history.append(acceleration)
        
        if t >= max_time:
            return {
                'success': False,
                'message': f'Vehicle cannot reach {target_velocity_kmh} km/h with {power_watts/745.7:.0f} HP',
                'time_seconds': None
            }
        
        return {
            'success': True,
            'time_seconds': t,
            'time_history': time_history,
            'velocity_history_kmh': velocity_history,
            'acceleration_history_ms2': acceleration_history,
            'final_velocity_kmh': v * 3.6,
            'average_acceleration_ms2': target_velocity_ms / t
        }
    
    def compare_materials(self,
                         power_watts: float,
                         length: float = 4.5,
                         scale_mode: str = 'full_scale') -> Dict:
        """
        Compare performance across different materials
        
        Args:
            power_watts: Engine power in Watts
            length: Vehicle length in meters
            scale_mode: 'miniature' or 'full_scale'
            
        Returns:
            Dictionary with comparison data for all materials
        """
        results = {}
        
        for material_name in self.MATERIALS.keys():
            # Create temporary calculator with this material
            temp_calc = PerformanceCalculator(
                self.cd,
                self.frontal_area,
                self.volume,
                material_name
            )
            
            # Calculate top speed
            top_speed_data = temp_calc.calculate_top_speed(
                power_watts, length, scale_mode
            )
            
            # Calculate 0-100 km/h
            accel_data = temp_calc.simulate_acceleration(
                power_watts, 100.0, length, scale_mode
            )
            
            _, _, scaled_mass = temp_calc._get_scaled_properties(length, scale_mode)
            
            results[material_name] = {
                'mass_kg': scaled_mass,
                'top_speed_kmh': top_speed_data['top_speed_kmh'],
                'acceleration_0_100_sec': accel_data.get('time_seconds'),
                'success': accel_data['success']
            }
        
        return results
    
    def scale_comparison(self,
                        power_watts: float,
                        miniature_length: float,
                        full_scale_length: float = 4.5) -> Dict:
        """
        Compare miniature vs full-scale performance
        
        Args:
            power_watts: Engine power in Watts
            miniature_length: Miniature model length in meters
            full_scale_length: Full-scale length in meters
            
        Returns:
            Dictionary comparing both scales
        """
        # Miniature scale
        mini_top_speed = self.calculate_top_speed(
            power_watts, miniature_length, 'miniature'
        )
        mini_accel = self.simulate_acceleration(
            power_watts, 100.0, miniature_length, 'miniature'
        )
        
        # Full scale
        full_top_speed = self.calculate_top_speed(
            power_watts, full_scale_length, 'full_scale'
        )
        full_accel = self.simulate_acceleration(
            power_watts, 100.0, full_scale_length, 'full_scale'
        )
        
        scaled_mini_length, mini_frontal_area, _ = self._get_scaled_properties(miniature_length, 'miniature')
        scaled_full_length, full_frontal_area, _ = self._get_scaled_properties(miniature_length, 'full_scale')
        
        return {
            'miniature': {
                'length_m': scaled_mini_length,
                'reynolds_number': mini_top_speed['reynolds_number'],
                'cd_corrected': mini_top_speed['cd_corrected'],
                'top_speed_kmh': mini_top_speed['top_speed_kmh'],
                'acceleration_0_100_sec': mini_accel.get('time_seconds'),
                'drag_force_100kmh_n': 0.5 * self.RHO_AIR * ((100/3.6)**2) * 
                                       mini_top_speed['cd_corrected'] * mini_frontal_area
            },
            'full_scale': {
                'length_m': scaled_full_length,
                'reynolds_number': full_top_speed['reynolds_number'],
                'cd_corrected': full_top_speed['cd_corrected'],
                'top_speed_kmh': full_top_speed['top_speed_kmh'],
                'acceleration_0_100_sec': full_accel.get('time_seconds'),
                'drag_force_100kmh_n': 0.5 * self.RHO_AIR * ((100/3.6)**2) * 
                                       full_top_speed['cd_corrected'] * full_frontal_area
            },
            'comparison': {
                'cd_difference_pct': ((full_top_speed['cd_corrected'] - 
                                      mini_top_speed['cd_corrected']) / 
                                     mini_top_speed['cd_corrected']) * 100,
                'reynolds_ratio': full_top_speed['reynolds_number'] / 
                                 mini_top_speed['reynolds_number']
            }
        }
    
    def get_performance_summary(self,
                               power_hp: float,
                               length: float = 4.5,
                               scale_mode: str = 'full_scale') -> Dict:
        """
        Get complete performance summary
        
        Args:
            power_hp: Engine power in horsepower
            length: Vehicle length in meters
            scale_mode: 'miniature' or 'full_scale'
            
        Returns:
            Complete performance analysis dictionary
        """
        power_watts = power_hp * 745.7
        
        scaled_length, scaled_frontal_area, scaled_mass = self._get_scaled_properties(length, scale_mode)
        
        if scale_mode == 'full_scale' and length < 3.0:
            scale_factor = 4.5 / max(length, 0.01)
            scaled_volume = self.volume * (scale_factor ** 3)
        else:
            scaled_volume = self.volume
            
        top_speed = self.calculate_top_speed(power_watts, length, scale_mode)
        accel_100 = self.simulate_acceleration(power_watts, 100.0, length, scale_mode)
        accel_60 = self.simulate_acceleration(power_watts, 60.0, length, scale_mode)
        
        return {
            'vehicle_specs': {
                'mass_kg': scaled_mass,
                'material': self.material,
                'cd': self.cd,
                'frontal_area_m2': scaled_frontal_area,
                'volume_m3': scaled_volume,
                'length_m': scaled_length,
                'scale_mode': scale_mode
            },
            'powertrain': {
                'power_hp': power_hp,
                'power_kw': power_watts / 1000
            },
            'top_speed': {
                'speed_kmh': top_speed['top_speed_kmh'],
                'speed_mph': top_speed['top_speed_kmh'] / 1.609,
                'reynolds_number': top_speed['reynolds_number'],
                'cd_at_top_speed': top_speed['cd_corrected'],
                'drag_force_n': top_speed['drag_force_n']
            },
            'acceleration': {
                '0_60_kmh_sec': accel_60.get('time_seconds'),
                '0_100_kmh_sec': accel_100.get('time_seconds'),
                'average_acceleration_ms2': accel_100.get('average_acceleration_ms2')
            },
            'efficiency': {
                'aero_power_pct': top_speed['power_breakdown']['aerodynamic_pct'],
                'rolling_power_pct': top_speed['power_breakdown']['rolling_pct'],
                'power_to_weight_ratio': power_watts / scaled_mass
            }
        }
