"""
Management command to populate detailed spare parts categories for Gurumisha Motors
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import SparePartCategory


class Command(BaseCommand):
    help = 'Populate detailed spare parts categories for automotive inventory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing categories...')
            SparePartCategory.objects.all().delete()

        self.stdout.write('Populating spare parts categories...')
        
        with transaction.atomic():
            self.create_categories()
        
        total_categories = SparePartCategory.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {total_categories} spare parts categories')
        )

    def create_categories(self):
        """Create comprehensive automotive spare parts categories"""
        
        # Define the detailed category structure
        categories_data = {
            # ENGINE SYSTEM
            'Engine System': {
                'description': 'Complete engine components and related systems for optimal vehicle performance',
                'subcategories': {
                    'Engine Block & Internal Components': {
                        'description': 'Core engine components including pistons, cylinders, and crankshaft parts',
                        'subcategories': {
                            'Pistons & Rings': 'High-performance pistons, piston rings, and connecting rods',
                            'Crankshaft & Bearings': 'Crankshafts, main bearings, and connecting rod bearings',
                            'Camshaft & Valvetrain': 'Camshafts, valve springs, lifters, and timing components',
                            'Cylinder Head Components': 'Cylinder heads, valves, valve seats, and head gaskets',
                            'Engine Gaskets & Seals': 'Complete gasket sets, oil seals, and O-rings'
                        }
                    },
                    'Fuel System': {
                        'description': 'Fuel delivery and injection system components',
                        'subcategories': {
                            'Fuel Injectors': 'Electronic and mechanical fuel injectors for all engine types',
                            'Fuel Pumps': 'Electric and mechanical fuel pumps, fuel pump modules',
                            'Fuel Filters': 'Inline fuel filters, fuel tank filters, and fuel strainers',
                            'Fuel Rails & Lines': 'Fuel rails, fuel lines, and fuel pressure regulators',
                            'Carburetors': 'Complete carburetors and carburetor rebuild kits'
                        }
                    },
                    'Air Intake System': {
                        'description': 'Air filtration and intake manifold components',
                        'subcategories': {
                            'Air Filters': 'Engine air filters, cabin air filters, and performance filters',
                            'Intake Manifolds': 'Intake manifolds, throttle bodies, and intake gaskets',
                            'Turbochargers': 'Turbocharger units, wastegates, and intercoolers',
                            'Superchargers': 'Supercharger units and drive components',
                            'Mass Air Flow Sensors': 'MAF sensors, MAP sensors, and intake sensors'
                        }
                    },
                    'Exhaust System': {
                        'description': 'Complete exhaust system from manifold to tailpipe',
                        'subcategories': {
                            'Exhaust Manifolds': 'Cast iron and stainless steel exhaust manifolds',
                            'Catalytic Converters': 'OEM and aftermarket catalytic converters',
                            'Mufflers & Resonators': 'Performance and OEM replacement mufflers',
                            'Exhaust Pipes & Tips': 'Exhaust pipes, clamps, and decorative tips',
                            'EGR Components': 'EGR valves, EGR coolers, and related components'
                        }
                    }
                }
            },

            # TRANSMISSION SYSTEM
            'Transmission System': {
                'description': 'Manual and automatic transmission components for smooth power delivery',
                'subcategories': {
                    'Automatic Transmission': {
                        'description': 'Automatic transmission components and rebuild parts',
                        'subcategories': {
                            'Transmission Filters': 'Internal filters, external filters, and filter kits',
                            'Torque Converters': 'Complete torque converters and rebuild components',
                            'Valve Bodies': 'Valve bodies, solenoids, and control modules',
                            'Clutch Packs': 'Friction plates, steel plates, and clutch bands',
                            'Transmission Pumps': 'Oil pumps, pressure regulators, and seals'
                        }
                    },
                    'Manual Transmission': {
                        'description': 'Manual transmission and clutch system components',
                        'subcategories': {
                            'Clutch Kits': 'Complete clutch kits, pressure plates, and clutch discs',
                            'Flywheels': 'Single mass and dual mass flywheels',
                            'Transmission Gears': 'Input shafts, output shafts, and gear sets',
                            'Synchronizers': 'Synchro rings, synchro hubs, and shift forks',
                            'Clutch Hydraulics': 'Master cylinders, slave cylinders, and clutch lines'
                        }
                    },
                    'Drivetrain Components': {
                        'description': 'Driveshafts, differentials, and related components',
                        'subcategories': {
                            'CV Joints & Axles': 'CV joints, drive axles, and CV boots',
                            'Driveshafts': 'Front and rear driveshafts, U-joints, and center bearings',
                            'Differential Components': 'Ring and pinion sets, differential carriers',
                            'Transfer Case Parts': '4WD transfer cases, chains, and shift motors',
                            'Transmission Mounts': 'Engine and transmission mounting systems'
                        }
                    }
                }
            },

            # SUSPENSION & STEERING
            'Suspension & Steering': {
                'description': 'Complete suspension and steering systems for vehicle control and comfort',
                'subcategories': {
                    'Front Suspension': {
                        'description': 'Front suspension components including struts and control arms',
                        'subcategories': {
                            'Struts & Shocks': 'MacPherson struts, shock absorbers, and coilovers',
                            'Control Arms': 'Upper and lower control arms, ball joints',
                            'Sway Bars': 'Anti-roll bars, sway bar links, and bushings',
                            'Springs': 'Coil springs, leaf springs, and air springs',
                            'Suspension Bushings': 'Rubber and polyurethane suspension bushings'
                        }
                    },
                    'Rear Suspension': {
                        'description': 'Rear suspension components for stability and comfort',
                        'subcategories': {
                            'Rear Shocks': 'Rear shock absorbers and strut assemblies',
                            'Rear Springs': 'Coil springs, leaf springs, and helper springs',
                            'Trailing Arms': 'Trailing arms, lateral links, and toe links',
                            'Panhard Bars': 'Panhard rods and track bars',
                            'Rear Sway Bars': 'Rear anti-roll bars and end links'
                        }
                    },
                    'Steering System': {
                        'description': 'Power steering and manual steering components',
                        'subcategories': {
                            'Steering Racks': 'Power and manual steering racks',
                            'Power Steering Pumps': 'Hydraulic and electric power steering pumps',
                            'Tie Rods': 'Inner and outer tie rod ends',
                            'Steering Columns': 'Steering columns, universal joints, and couplers',
                            'Steering Wheels': 'OEM and aftermarket steering wheels'
                        }
                    }
                }
            },

            # BRAKE SYSTEM
            'Brake System': {
                'description': 'Complete braking system components for safety and performance',
                'subcategories': {
                    'Disc Brakes': {
                        'description': 'Disc brake components for front and rear applications',
                        'subcategories': {
                            'Brake Pads': 'Ceramic, semi-metallic, and organic brake pads',
                            'Brake Rotors': 'Vented, slotted, and drilled brake rotors',
                            'Brake Calipers': 'Single and multi-piston brake calipers',
                            'Caliper Hardware': 'Caliper brackets, pins, and hardware kits',
                            'Brake Lines': 'Steel braided and rubber brake lines'
                        }
                    },
                    'Drum Brakes': {
                        'description': 'Drum brake components for rear brake applications',
                        'subcategories': {
                            'Brake Shoes': 'Bonded and riveted brake shoes',
                            'Brake Drums': 'Cast iron and composite brake drums',
                            'Wheel Cylinders': 'Single and dual piston wheel cylinders',
                            'Brake Hardware': 'Springs, adjusters, and hold-down hardware',
                            'Parking Brake': 'Parking brake cables and adjusters'
                        }
                    },
                    'Brake Hydraulics': {
                        'description': 'Hydraulic brake system components',
                        'subcategories': {
                            'Master Cylinders': 'Brake and clutch master cylinders',
                            'Brake Boosters': 'Vacuum and hydraulic brake boosters',
                            'ABS Components': 'ABS modules, sensors, and hydraulic units',
                            'Brake Fluid': 'DOT 3, DOT 4, and DOT 5.1 brake fluids',
                            'Proportioning Valves': 'Brake proportioning and combination valves'
                        }
                    }
                }
            },

            # ELECTRICAL SYSTEM
            'Electrical System': {
                'description': 'Complete electrical and electronic components for modern vehicles',
                'subcategories': {
                    'Charging System': {
                        'description': 'Battery charging and power generation components',
                        'subcategories': {
                            'Alternators': 'High-output alternators and rebuild components',
                            'Batteries': 'Lead-acid, AGM, and lithium automotive batteries',
                            'Voltage Regulators': 'Internal and external voltage regulators',
                            'Battery Cables': 'Positive and negative battery cable assemblies',
                            'Charging Accessories': 'Battery chargers, jump starters, and maintainers'
                        }
                    },
                    'Starting System': {
                        'description': 'Engine starting system components',
                        'subcategories': {
                            'Starters': 'Gear reduction and direct drive starters',
                            'Starter Solenoids': 'Starter solenoids and relay assemblies',
                            'Ignition Switches': 'Key and push-button ignition switches',
                            'Starter Drives': 'Bendix drives and starter gear assemblies',
                            'Flywheel Ring Gears': 'Starter ring gears and flex plates'
                        }
                    },
                    'Ignition System': {
                        'description': 'Spark ignition and timing components',
                        'subcategories': {
                            'Spark Plugs': 'Copper, platinum, and iridium spark plugs',
                            'Ignition Coils': 'Individual and pack ignition coils',
                            'Spark Plug Wires': 'High-performance ignition wire sets',
                            'Distributors': 'Complete distributors and distributor caps',
                            'Ignition Modules': 'Electronic ignition control modules'
                        }
                    },
                    'Lighting System': {
                        'description': 'Interior and exterior lighting components',
                        'subcategories': {
                            'Headlights': 'Halogen, HID, and LED headlight assemblies',
                            'Tail Lights': 'LED and incandescent tail light assemblies',
                            'Interior Lights': 'Dome lights, map lights, and courtesy lights',
                            'Signal Lights': 'Turn signals, hazard lights, and flashers',
                            'Light Bulbs': 'All automotive bulb types and LED replacements'
                        }
                    }
                }
            },

            # COOLING SYSTEM
            'Cooling System': {
                'description': 'Engine cooling and climate control system components',
                'subcategories': {
                    'Engine Cooling': {
                        'description': 'Primary engine cooling system components',
                        'subcategories': {
                            'Radiators': 'Aluminum and copper-brass radiators',
                            'Water Pumps': 'Mechanical and electric water pumps',
                            'Thermostats': 'OEM and performance thermostats',
                            'Cooling Fans': 'Engine cooling fans and fan assemblies',
                            'Radiator Hoses': 'Upper, lower, and heater hoses'
                        }
                    },
                    'HVAC System': {
                        'description': 'Heating, ventilation, and air conditioning components',
                        'subcategories': {
                            'A/C Compressors': 'Remanufactured and new A/C compressors',
                            'Condensers': 'A/C condensers and receiver driers',
                            'Evaporators': 'A/C evaporator cores and expansion valves',
                            'Heater Cores': 'Heater cores and heater control valves',
                            'Blower Motors': 'HVAC blower motors and resistors'
                        }
                    },
                    'Cooling Accessories': {
                        'description': 'Additional cooling system components',
                        'subcategories': {
                            'Coolant': 'Ethylene glycol and OAT coolants',
                            'Radiator Caps': 'Pressure caps and overflow tanks',
                            'Temperature Sensors': 'Coolant temperature sensors and switches',
                            'Oil Coolers': 'Engine and transmission oil coolers',
                            'Intercoolers': 'Turbo and supercharger intercoolers'
                        }
                    }
                }
            },

            # BODY & EXTERIOR
            'Body & Exterior': {
                'description': 'Body panels, trim, and exterior accessories',
                'subcategories': {
                    'Body Panels': {
                        'description': 'Replacement body panels and structural components',
                        'subcategories': {
                            'Fenders': 'Front and rear fender assemblies',
                            'Doors': 'Complete door assemblies and door skins',
                            'Hoods': 'Steel and carbon fiber hood assemblies',
                            'Bumpers': 'Front and rear bumper covers',
                            'Quarter Panels': 'Rear quarter panels and patch panels'
                        }
                    },
                    'Glass & Mirrors': {
                        'description': 'Automotive glass and mirror assemblies',
                        'subcategories': {
                            'Windshields': 'Laminated and tempered windshields',
                            'Side Windows': 'Door glass and quarter windows',
                            'Mirrors': 'Side mirrors, rearview mirrors, and mirror glass',
                            'Sunroofs': 'Sunroof assemblies and moonroof components',
                            'Window Regulators': 'Power and manual window regulators'
                        }
                    },
                    'Exterior Trim': {
                        'description': 'Decorative and functional exterior trim pieces',
                        'subcategories': {
                            'Grilles': 'Front grilles and grille inserts',
                            'Moldings': 'Body side moldings and trim strips',
                            'Emblems': 'Manufacturer emblems and badges',
                            'Spoilers': 'Rear spoilers and aerodynamic components',
                            'Running Boards': 'Side steps and running board assemblies'
                        }
                    }
                }
            },

            # INTERIOR COMPONENTS
            'Interior Components': {
                'description': 'Interior comfort, convenience, and safety components',
                'subcategories': {
                    'Seating': {
                        'description': 'Seats and seating-related components',
                        'subcategories': {
                            'Seat Covers': 'Leather, fabric, and custom seat covers',
                            'Seat Motors': 'Power seat motors and track assemblies',
                            'Seat Belts': 'Three-point and lap seat belt assemblies',
                            'Headrests': 'Adjustable and fixed headrest assemblies',
                            'Seat Cushions': 'Foam cushions and seat padding'
                        }
                    },
                    'Dashboard & Console': {
                        'description': 'Dashboard and center console components',
                        'subcategories': {
                            'Instrument Clusters': 'Gauge clusters and speedometers',
                            'Radio & Navigation': 'Aftermarket and OEM radio systems',
                            'Climate Controls': 'HVAC control panels and switches',
                            'Cup Holders': 'Center console and door cup holders',
                            'Storage Compartments': 'Glove boxes and console storage'
                        }
                    },
                    'Interior Trim': {
                        'description': 'Interior decorative and functional trim',
                        'subcategories': {
                            'Door Panels': 'Interior door panels and trim pieces',
                            'Carpet': 'Molded and cut-pile automotive carpet',
                            'Floor Mats': 'Rubber and carpet floor mat sets',
                            'Headliners': 'Fabric and vinyl headliner materials',
                            'Pillar Trim': 'A, B, and C pillar trim covers'
                        }
                    }
                }
            },

            # FILTERS & FLUIDS
            'Filters & Fluids': {
                'description': 'Maintenance filters and automotive fluids',
                'subcategories': {
                    'Engine Filters': {
                        'description': 'Engine-related filtration components',
                        'subcategories': {
                            'Oil Filters': 'Spin-on and cartridge oil filters',
                            'Air Filters': 'Paper, foam, and performance air filters',
                            'Fuel Filters': 'Inline and in-tank fuel filters',
                            'PCV Valves': 'Positive crankcase ventilation valves',
                            'Breather Elements': 'Crankcase breather filters'
                        }
                    },
                    'Transmission Filters': {
                        'description': 'Transmission and drivetrain filters',
                        'subcategories': {
                            'Automatic Transmission Filters': 'Internal transmission filters',
                            'Manual Transmission Filters': 'Gear oil filters and breathers',
                            'Differential Filters': 'Rear end and front differential filters',
                            'Transfer Case Filters': '4WD transfer case filters',
                            'CVT Filters': 'Continuously variable transmission filters'
                        }
                    },
                    'Automotive Fluids': {
                        'description': 'Essential automotive fluids and lubricants',
                        'subcategories': {
                            'Engine Oil': 'Conventional, synthetic, and high-mileage oils',
                            'Transmission Fluid': 'ATF, manual, and CVT fluids',
                            'Brake Fluid': 'DOT 3, DOT 4, and DOT 5.1 fluids',
                            'Power Steering Fluid': 'Hydraulic power steering fluids',
                            'Differential Oil': 'Gear oils and limited-slip additives'
                        }
                    }
                }
            }
        }

        # Create categories recursively
        self._create_category_tree(categories_data)

    def _create_category_tree(self, categories_data, parent=None):
        """Recursively create category tree"""
        for name, data in categories_data.items():
            if isinstance(data, dict):
                description = data.get('description', '')

                # Check if category already exists with same name and parent
                try:
                    category = SparePartCategory.objects.get(name=name, parent=parent)
                    created = False
                except SparePartCategory.DoesNotExist:
                    category = SparePartCategory.objects.create(
                        name=name,
                        parent=parent,
                        description=description
                    )
                    created = True

                if created:
                    self.stdout.write(f'Created category: {category}')
                else:
                    self.stdout.write(f'Category already exists: {category}')

                # Create subcategories if they exist
                subcategories = data.get('subcategories', {})
                if subcategories:
                    self._create_category_tree(subcategories, category)
            else:
                # This is a leaf category with just a description
                try:
                    category = SparePartCategory.objects.get(name=name, parent=parent)
                    created = False
                except SparePartCategory.DoesNotExist:
                    category = SparePartCategory.objects.create(
                        name=name,
                        parent=parent,
                        description=data
                    )
                    created = True

                if created:
                    self.stdout.write(f'Created category: {category}')
                else:
                    self.stdout.write(f'Category already exists: {category}')
