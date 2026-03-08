# Receipt Data Workflow
Product: EZWorks-Expense

This document defines the lifecycle of a receipt inside the system.

The workflow must remain consistent across all modules.

---

# Receipt Lifecycle

A receipt moves through the following states.

UPLOADED  
OCR_PROCESSING  
OCR_COMPLETED  
NEEDS_REVIEW  
READY_FOR_REPORT  
ASSIGNED_TO_REPORT  
ARCHIVED

---

# State Definitions

UPLOADED
A receipt image has been uploaded but OCR has not started.

OCR_PROCESSING
The system is currently extracting data from the image.

OCR_COMPLETED
OCR completed successfully.

NEEDS_REVIEW
OCR data requires user validation.

READY_FOR_REPORT
Receipt is confirmed and available for report assignment.

ASSIGNED_TO_REPORT
Receipt has been included in a report.

ARCHIVED
Report has been finalized and receipt is locked.

---

# OCR Failure States

The OCR system may return error states.

OCR_FAILED
OCR could not process the image.

LOW_CONFIDENCE
OCR result confidence is low.

IMAGE_UNREADABLE
Image quality is too poor.

---

# Manual Entry Mode

When OCR confidence is low, the system must allow manual entry.

Manual entry is triggered in Wizard Step 4.

Users can manually edit:

Vendor  
Date  
Amount  
Currency  
Category

---

# Duplicate Detection

The system should detect potential duplicates.

Possible duplicate conditions:

same vendor  
same amount  
date difference within 1 day  

Possible duplicates should be flagged in the Inbox UI.

---

# Data Ownership Rules

Inbox owns receipt data.

Reports only reference receipts.

Reports must not duplicate receipt data.

---

# Data Integrity

Editing a receipt inside a report must update the original receipt in the Inbox.

The Inbox remains the single source of truth.