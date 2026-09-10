export const SRI_LANKA_PROVINCES: Record<string, string[]> = {
  "All Provinces": ["All Districts", "National / All Island"],
  "Western": ["All Districts", "Colombo", "Gampaha", "Kalutara"],
  "Central": ["All Districts", "Kandy", "Matale", "Nuwara Eliya"],
  "Southern": ["All Districts", "Galle", "Matara", "Hambantota"],
  "Northern": ["All Districts", "Jaffna", "Kilinochchi", "Mannar", "Vavuniya", "Mullaitivu"],
  "Eastern": ["All Districts", "Trincomalee", "Batticaloa", "Ampara"],
  "North Western": ["All Districts", "Kurunegala", "Puttalam"],
  "North Central": ["All Districts", "Anuradhapura", "Polonnaruwa"],
  "Uva": ["All Districts", "Badulla", "Monaragala"],
  "Sabaragamuwa": ["All Districts", "Ratnapura", "Kegalle"]
};

export const PROVINCE_LIST = Object.keys(SRI_LANKA_PROVINCES);

export const REVISION_OPTIONS = [
  "Original",
  "First Half",
  "Second Half",
  "Revision 01",
  "Revision 02",
  "Final"
];

export const DATASET_TYPES = [
  "BSR Rate Book",
  "Material Rates",
  "Labour Rates",
  "Transport Rates",
  "Other"
];

export const VAT_BASIS_OPTIONS = [
  "Without VAT",
  "With VAT",
  "Not Applicable"
];

export const SECTORS = [
  "Building Works",
  "Highway / Road Works",
  "Water Supply Works",
  "Sewerage Works",
  "Storm Water Drainage Works",
  "Other"
];

export const RATE_SYSTEMS = [
  "BSR",
  "HSR",
  "Water Supply Rates",
  "Sewerage & Storm Water Drainage Works",
  "Other / Custom"
];

export const SECTOR_RATE_SYSTEM_MAP: Record<string, string[]> = {
  "Building Works": ["BSR"],
  "Highway / Road Works": ["HSR"],
  "Water Supply Works": ["Water Supply Rates"],
  "Sewerage Works": ["Sewerage & Storm Water Drainage Works"],
  "Storm Water Drainage Works": ["Sewerage & Storm Water Drainage Works"],
  "Other": ["Other / Custom", "BSR", "HSR", "Water Supply Rates", "Sewerage & Storm Water Drainage Works"]
};

export const SECTOR_BADGE_CLASSES: Record<string, string> = {
  "Building Works": "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300 border-blue-200 dark:border-blue-800",
  "Highway / Road Works": "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 border-amber-200 dark:border-amber-800",
  "Water Supply Works": "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/40 dark:text-cyan-300 border-cyan-200 dark:border-cyan-800",
  "Sewerage Works": "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
  "Storm Water Drainage Works": "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300 border-sky-200 dark:border-sky-800",
  "Other": "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300 border-purple-200 dark:border-purple-800"
};

export const SECTOR_CATEGORY_PRESETS: Record<string, string[]> = {
  "Building Works": [
    "Demolition & Alterations", "Earthwork & Excavation", "Concrete Work", 
    "Masonry & Brickwork", "Roofing & Cladding", "Carpentry & Joinery", 
    "Plumbing & Drainage", "Electrical Installation", "Floor & Wall Finishes", 
    "Painting & Decorating", "Metalwork & Ironmongery", "External Works"
  ],
  "Highway / Road Works": [
    "Site Clearing & Earthwork", "Subbase, Base & Shoulder Construction", 
    "Bituminous Surfacing & Asphalt", "Road Drainage Structures", 
    "Bridges & Precast Culverts", "Traffic Safety, Signs & Road Marking", 
    "Retaining Walls & Gabions", "Incidental Road Works"
  ],
  "Water Supply Works": [
    "Ductile Iron (DI) Pipes & Fittings", "HDPE / MDPE Pipes & Fittings", 
    "uPVC Pipes & Pressure Fittings", "Valves, Hydrants & Flow Meters", 
    "Pumping Machinery, Motors & Controls", "Water Treatment Plant Equipment", 
    "Ground & Elevated Water Reservoirs", "Customer Service Connections", 
    "Hydrostatic Pressure Testing & Disinfection"
  ],
  "Sewerage Works": [
    "Gravity Sewer Collection Mains", "Sewer Manholes & Drop Chambers", 
    "Wastewater Pumping Stations & Force Mains", "Screening & Grit Chambers", 
    "Aeration, Sedimentation & Treatment Tanks", "Sludge Dewatering & Drying Beds", 
    "Odor Control Systems & Effluent Disposal"
  ],
  "Storm Water Drainage Works": [
    "Open Lined & Unlined Surface Drains", "Precast Concrete U-Drains & Covers", 
    "Box Culverts & Circular Pipe Culverts", "Inlet Pits, Catch Basins & Gullies", 
    "Channel Excavation & River Training", "Flood Retention Basins & Sluice Gates", 
    "Erosion Control & Gabion Mattresses"
  ],
  "Other": ["General Works", "Provisional Sums", "Prime Cost Items", "Miscellaneous"]
};
