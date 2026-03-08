# EZWorks-Expense AI Design

This document defines the AI-assisted features of the EZWorks-Expense system.

---

# AI Scope

The system uses AI for:

OCR extraction  
Vendor recognition  
Expense category suggestion  
Duplicate detection  

AI must assist the user, not replace validation.

---

# OCR Extraction

The OCR system extracts:

Vendor name  
Transaction date  
Total amount  
Currency  

OCR results include confidence score.

---

# Vendor Recognition

The system should attempt to normalize vendor names.

Example:

UBER TRIP → Uber  
STARBUCKS STORE 123 → Starbucks  
HILTON ATLANTA → Hilton

This improves reporting consistency.

---

# Category Suggestion

The system should automatically suggest expense categories.

Example mapping:

Uber → Transportation  
Starbucks → Meals  
Hilton → Lodging  
Delta → Airfare

This suggestion should appear during review.

Users can override the suggestion.

---

# Vendor Mapping Memory

When a user assigns a category to a vendor, the system should remember it.

Example:

Vendor: Uber  
User Category: Transportation

Future receipts from Uber should default to Transportation.

This rule is stored in Vendor Mapping.

---

# Duplicate Detection

AI should flag possible duplicate receipts.

Rules include:

same vendor  
same amount  
close transaction date  

Duplicates are flagged but not automatically removed.

---

# Confidence Handling

If OCR confidence is below threshold:

system marks receipt as LOW_CONFIDENCE.

Wizard Step 4 should require user confirmation.

---

# AI Role

AI assists the workflow.

Users remain the final authority.

All AI suggestions must be editable.