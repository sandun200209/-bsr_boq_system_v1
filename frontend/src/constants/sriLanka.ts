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
