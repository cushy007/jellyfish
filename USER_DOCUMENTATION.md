# Jellyfish - Scuba Diving Gear Management System
## User Documentation

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Main Features](#main-features)
4. [Core Sections](#core-sections)
5. [Common Workflows](#common-workflows)
6. [FAQ](#faq)

---

## Introduction

**Jellyfish** is a comprehensive web-based inventory and loan management system designed for managing scuba diving equipment and gear. It helps diving clubs and organizations track their equipment, manage member loans, conduct inventories, and maintain service records.

### Key Capabilities

- **Equipment Catalog**: Maintain a complete inventory of diving gear including regulators, tanks, suits, and accessories
- **Loan Management**: Track who has borrowed what gear and when it needs to be returned
- **Inventory Campaigns**: Conduct periodic inventories to track equipment condition and availability
- **Servicing Records**: Track equipment maintenance and service history
- **Member Management**: Maintain member information and guarantee records
- **QR Code Support**: Use QR codes for quick item scanning and identification

---

## Getting Started

### Authentication

1. Navigate to the Jellyfish web application
2. Log in with your credentials
3. You will be directed to the Overview tab

### User Roles

The system supports different access levels:
- **User**: Basic access to view and manage equipment
- **Lender**: Can manage loan operations
- **Treasurer**: Can manage member information
- **Admin**: Full system access including administrative tools

---

## Main Features

### Navigation

The application uses a tab-based interface with the following main sections:

#### Overview Tab
- Quick summary of the current status
- Items requiring service
- Active loans display
- Access to servicing requests

#### Gear Tab
Organized by equipment categories:
- **Regulators**: First stage, second stage, octopus, manometer
- **Tanks & Breathing**: BCD, tanks, weights
- **Suits & Protection**: Suits, hoods, boots, gloves
- **Fins & Propulsion**: Fins, monofins
- **Masks & Visibility**: Masks, snorkels
- **Computers & Electronics**: Dive computers, lamps, oxymeters
- **Accessories**: Keys, rings, frisbees, and other items

#### Loans Tab
- **Collect**: Issue gear to members
- **Reintegrate**: Process returned gear

#### Inventories Tab
- Start new inventory campaigns
- Track inventory progress
- View inventory statistics and analysis

#### Members Tab
- View member database
- Manage member information
- Track member guarantees and license numbers

#### Statistics Tab
- Loan statistics
- Historical data and trends

#### Admin Tab
- **Tools**: Database management and member import
- **QRCodes**: Generate QR codes for equipment identification

---

## Core Sections

### 1. Gear Management

#### Viewing Equipment

1. Navigate to the **Gear** tab
2. Select an equipment category from the left menu (e.g., "Regulators")
3. Select a specific item type (e.g., "Main regulator")
4. Browse the equipment list

Each item displays:
- **Reference Number**: Unique identifier with prefix (e.g., "REG01")
- **Brand & Model**: Manufacturer information
- **Serial Number**: Equipment serial for tracking
- **Status**: Available (green) or Unavailable (grayed out)
- **Availability Date**: When item is available for loan
- **Size/Type Information**: Relevant specifications (gender, size, age category)
- **Special Properties**: Cold water compliance, Nitrox compatibility, etc.

#### Adding Equipment

1. Navigate to the desired category in **Gear**
2. Click the "Add" button
3. Fill in the equipment details:
   - **Type**: Category of equipment
   - **Reference Number**: Unique identifier
   - **Owner Club**: Which club owns this item
   - **Brand & Model**: Manufacturer details
   - **Serial Number**: Equipment serial
   - **Size/Gender Options**: Relevant for fitting items
   - **Technical Specs**: Pressure ratings, materials, thickness, weight
   - **Condition Flags**: Cold water, Nitrox, apnea compatible, etc.

4. Click "Save" to add the equipment

#### Editing Equipment

1. Find the equipment in the Gear tab
2. Click on the item row
3. Modify the details as needed
4. Click "Save"

#### Equipment Lifecycle States

Equipment can be in different states:
- **Available**: Ready to borrow
- **Servicing**: Undergoing maintenance (tracked in Servicing Records)
- **Repairing**: Being repaired
- **Trashed**: No longer usable

---

### 2. Loan Management

Loans track who has borrowed equipment and when items need to be returned.

#### Borrowing Equipment (Collection)

**Collect Tab → Collect Sub-Tab**

##### Using Scanner (Recommended)

1. Navigate to **Loans → Collect**
2. Ensure "Use Scanner" option is selected
3. Scan the **item's QR code** using your device camera
   - The system recognizes the item type and reference
4. Scan the **member's license QR code** or enter the license number
5. Confirm the loan details
6. The system records:
   - Which member borrowed the item
   - The date and time of the loan
   - The item's usage counter increment

##### Manual Entry

1. Navigate to **Loans → Collect**
2. Disable "Use Scanner" 
3. Select the item from the dropdown
4. Enter the member information
5. Confirm the loan

#### Returning Equipment (Reintegration)

**Loans → Reintegrate Sub-Tab**

1. Navigate to **Loans → Reintegrate**
2. Scan the returned item's QR code or select from dropdown
3. (Optional) Enter usage counter if tracking is important
4. Confirm the return
5. The item becomes available again

#### Viewing Active Loans

1. Navigate to **Overview** tab
2. Scroll to "Active Loans" section
3. View all currently borrowed items with:
   - Member who borrowed it
   - Borrow date
   - Return date (if applicable)

---

### 3. Inventory Management

Inventories are periodic audits of all equipment to verify condition and availability.

#### Starting an Inventory Campaign

1. Navigate to **Inventories** tab
2. Click **"Start Inventory"** button
3. The system creates a new inventory record for today
4. You can only have one active inventory at a time

#### Conducting an Inventory

1. With an active inventory, the system displays:
   - Current item category in dropdown
   - Remaining items to process in that category
   - A table of items awaiting inventory check

2. For each item, record its state by:
   - Clicking on the item
   - Updating the item status form
   - Entering condition information (present, usable, price estimate)
   - Adding any comments about damage or issues

3. Select the next item category from dropdown to continue

#### Completing an Inventory

1. When all items are processed, click **"Stop Inventory"**
2. The inventory becomes a historical record

#### Viewing Inventory Reports

1. Click **"Inventory Info"** on a completed inventory
2. Review statistics:
   - **Total Equipment Value**: Estimated replacement cost
   - **Count by Type**: How many items of each type
   - **Price by Item Type**: Value breakdown
   - **Missing Items**: Items not found during inventory
   - **Unusable Items**: Damaged or non-functional gear
   - **Uninventoried Items**: Items not yet checked

#### Restarting an Inventory

1. If an inventory wasn't completed, click **"Restart Inventory"**
2. Resumes the inventory process

#### Deleting an Inventory

1. Click **"Delete Inventory"** to remove an incomplete inventory
2. **Warning**: This cannot be undone

---

### 4. Member Management

Track diving club members and their borrowing privileges.

#### Viewing Members

1. Navigate to **Members** tab
2. Browse the member list showing:
   - Last name and first name
   - License number
   - Guarantee status
   - Guarantee expiration date

3. Click on a member to view full details

#### Adding a Member

1. Navigate to **Members** tab
2. Click **"Add Member"** button
3. Fill in the member form:
   - **First Name**: Member's first name
   - **Last Name**: Member's last name
   - **License Number**: Diving certification/license number
   - **Has Guarantee**: Check if member has equipment guarantee
   - **Guarantee End Date**: When guarantee expires (if applicable)

4. Click **"Save"**

#### Editing Member Information

1. Find the member in the Members tab
2. Click on the member row
3. Update the information
4. Click **"Save"**

#### Member Guarantees

Some members may have equipment guarantees (e.g., club members with insurance):
- Check "Has Guarantee" checkbox
- Set the expiration date
- This information helps track member status

---

### 5. Servicing & Maintenance

Track equipment maintenance and service history.

#### Viewing Items Requiring Service

1. Navigate to **Overview** tab
2. Look for "Items Requiring Service" section
3. These are items flagged for maintenance

#### Recording a Service

1. Click on an item requiring service
2. Navigate to **Servicing → Add Service** (or use the quick link from Overview)
3. Fill out the service form:
   - **Item**: Pre-selected item requiring service
   - **Member**: Who performed the service
   - **Service Date**: When service was performed
   - **Report File**: Upload service documentation/report

4. Click **"Save"**

The item is automatically marked as serviceable after recording.

#### Viewing Service History

Each item displays its complete service history with:
- Service dates
- Service documentation
- Servicing technician/member

---

### 6. Admin Functions

Administrative users have access to advanced tools.

#### Database Management

**Admin → Tools**

1. **Export Database**: Download current database backup
2. **Restore Database**: Upload a previously exported database to restore data
3. **Import Members**: Bulk upload member list from a file

#### QR Code Generation

**Admin → QRCodes**

1. Navigate to **Admin → QRCodes**
2. The system displays any "holes" in your QR code numbering
   - Holes are missing reference numbers in the sequence
3. Generate PDF sheets of QR codes for:
   - Items in your inventory
   - Missing reference numbers to complete sequences

4. Use generated QR codes:
   - Print them on labels
   - Attach to physical equipment
   - Scan during loans and inventories

---

## Common Workflows

### Workflow 1: New Equipment Addition and QR Code Setup

1. **Add Equipment** (Gear section)
   - Select category and item type
   - Fill all required details
   - Note the reference number assigned

2. **Generate QR Codes** (Admin → QRCodes)
   - System identifies the new reference number
   - Generate QR code PDF
   - Print and attach to equipment

3. **Verify in System**
   - Scan the new QR code in Gear tab
   - Confirm equipment appears in system

### Workflow 2: Member Borrows Equipment

1. **Add Member** (if new)
   - Enter member details in Members section
   - Record license number

2. **Lend Equipment**
   - Navigate to Loans → Collect
   - Scan member license and item QR code
   - System records loan transaction

3. **Return Equipment**
   - Navigate to Loans → Reintegrate
   - Scan returned item QR code
   - Item becomes available for next loan

### Workflow 3: Equipment Service and Return to Service

1. **Flag Item for Service**
   - Navigate to item in Gear section
   - Set status to "Servicing"

2. **Record Service** (when complete)
   - Navigate to Overview or use quick link
   - Click "Add Service"
   - Upload service report
   - Item automatically marked available

3. **Confirm Availability**
   - Item appears as available in Gear section
   - Ready for next loan

### Workflow 4: Conduct Quarterly Inventory

1. **Start Inventory** (Inventories tab)
   - Click "Start Inventory" button
   - System creates today's inventory

2. **Process Each Category**
   - Select item category from dropdown
   - For each item: click it, record state (present/usable/price)
   - Add any damage comments
   - Move to next item

3. **Review Summary**
   - Once all items processed, click "Stop Inventory"
   - Click "Inventory Info" to see:
     - Total equipment value
     - Items by category
     - Missing or damaged items

4. **Take Action**
   - Schedule service for unusable items
   - Investigate missing items
   - Update pricing estimates

---

## FAQ

### Q: I accidentally started an inventory. Can I cancel it?

**A**: Yes. Click **"Restart Inventory"** to reset it, or **"Delete Inventory"** to remove it completely. No permanent changes are made until you stop the inventory.

### Q: How do QR codes work?

**A**: QR codes encode the item reference (e.g., "REG01"). When scanned, they automatically populate the item in loan forms. Admin can generate and print QR codes from the Admin section.

### Q: Can a member borrow the same item multiple times?

**A**: Yes. Each borrow is a separate transaction. The system tracks usage counters for equipment condition monitoring.

### Q: What happens to servicing records?

**A**: Service records are permanently stored with the item. Each service documents when it was performed and includes uploaded documentation. This helps track equipment maintenance history.

### Q: How do I bulk import members?

**A**: Use **Admin → Tools → Import Members**. Upload a file with member data. The system validates and imports new members.

### Q: Can I edit past inventory records?

**A**: Inventory records are snapshots. You cannot edit completed inventories. If you need corrections, contact an administrator.

### Q: What's the difference between "Servicing" and "Repairing" status?

**A**: 
- **Servicing**: Scheduled maintenance (e.g., regulator annual service)
- **Repairing**: Damage repair (e.g., broken fin blade)

Both mark equipment unavailable for loan until cleared.

### Q: How do I track equipment value?

**A**: During inventory, enter the price/value estimate for each item. The system calculates total inventory value and tracks value changes over time.

### Q: Can I export the data?

**A**: Yes. Administrators can export the complete database from **Admin → Tools**. This creates a backup file that can be restored later.

### Q: What if I lose a member's license number?

**A**: You can still add the member without it (optional field). If they loan gear, you can enter their license number later when they return.

---

## Support

For technical issues or feature requests:
- Contact your system administrator
- Check that you have the latest browser version
- Ensure you have JavaScript enabled in your browser

---

**Last Updated**: 2026-09-07

**Jellyfish** is built with Flask and powered by the [weblib](https://github.com/cushy007/weblib) library.

For more information about the project, visit: https://github.com/cushy007/jellyfish
