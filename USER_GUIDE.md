# Semptify User Guide

## What Semptify Does

Semptify is a **document organization and search system** for your legal case. It helps you:

- **Store documents** - PDFs, emails, images, call logs, SMS messages
- **Find documents fast** - Search by keywords, dates, phone numbers
- **Organize automatically** - Categorizes files by type, extracts phone numbers
- **Remove duplicates** - Identifies duplicate files by hash
- **Track evidence** - Links phone numbers across all documents

---

## How to Start

1. **Open the app**: Go to http://localhost:8019 in your browser
2. **You'll see 6 tabs** on the left side (Dashboard, Search, Upload, Timeline, Phone Numbers, Quarantine)
3. **Click any tab** to use that feature

---

## Tab-by-Tab Guide

### 1. Dashboard (📊)
**What it does**: Shows you statistics about your documents

**What you see**:
- **Documents** - Total number of PDFs, emails, images stored
- **Calls** - Number of call records
- **SMS** - Number of text messages
- **Phone Numbers** - Total unique phone numbers found
- **Quarantined** - Number of duplicate files
- **Inbox Storage** - How much space your files use
- **Quarantine Storage** - Space used by duplicates

**How to use**: Just look at the numbers. No buttons to click here.

---

### 2. Search (🔍)
**What it does**: Find any document, call, or SMS message

**How to search**:
1. **Keywords** - Type words like "invoice", "rent", "Brad"
2. **Phone Numbers** - Type a phone number to find all related evidence
3. **Start Date** - Pick a date to find things after that date
4. **End Date** - Pick a date to find things before that date
5. **Document Types** - Select types (PDF, Email, Image, Bill) - hold Ctrl to select multiple
6. **Click "Search" button** - Results appear below

**What results show**:
- **Documents** - PDFs, emails, images with a snippet of text
- **Calls** - Phone calls with date and direction
- **SMS** - Text messages with date and direction

**Click any result** to see the full content in a popup window.

---

### 3. Upload (📤)
**What it does**: Add new files to the system

**How to upload**:
1. **Drag and drop** files onto the dotted box
2. **OR click the box** to browse your computer
3. **Select multiple files** - you can upload several at once
4. **Progress bar** shows upload status
5. **Files go to** `data/inbox/` folder automatically

**What happens after upload**:
- Files are automatically processed
- Text is extracted (OCR for images/PDFs)
- Phone numbers are extracted
- Files are deduplicated (duplicates go to quarantine)

---

### 4. Timeline (🕐)
**What it does**: See events in chronological order

**What you see**:
- A timeline of events with dates
- Each event shows title, type, and description

**How to use**:
- Currently shows events you manually create
- Events are listed newest to oldest
- Scroll down to see older events

---

### 5. Phone Numbers (📱)
**What it does**: See all phone numbers found in your documents

**What you see**:
- List of all phone numbers extracted from documents
- Each number has a label (e.g., "Brad", "Landlord")

**How to use**:
1. **Click any phone number** to see:
   - All documents containing that number
   - All calls to/from that number
   - All SMS messages to/from that number
2. **This helps** track who you communicated with and when

---

### 6. Quarantine (⚠️)
**What it does**: Review and manage duplicate files

**What you see**:
- List of duplicate files
- File names and sizes
- Delete button for each file

**How to use**:
1. **Review the list** - these are potential duplicates
2. **Click the trash icon** to delete a file from quarantine
3. **"Extract Phone Numbers" button** - Scans all documents again to find phone numbers

**Important**: Duplicates are moved here for safety - review before deleting.

---

## Quick Reference Card

| I want to... | Go to tab | What to do |
|--------------|-----------|------------|
| Add a new document | Upload | Drag-drop file or click to browse |
| Find a specific document | Search | Type keywords, click Search |
| See all phone numbers | Phone Numbers | Click a number to see linked evidence |
| Check how many files I have | Dashboard | Just look at the numbers |
| Remove duplicate files | Quarantine | Click trash icon to delete |
| See events in order | Timeline | Scroll through the list |

---

## Common Questions

**Q: Where do my files go?**
A: Files are stored in `data/inbox/` and `data/cases/` folders on your computer.

**Q: Can I delete a file?**
A: Yes, in the Quarantine tab. Be careful - you can't undo deletion.

**Q: What if I upload the same file twice?**
A: The second copy goes to Quarantine as a duplicate. The original stays in the main system.

**Q: How do I search for a specific date?**
A: Use the Start Date and End Date fields in the Search tab.

**Q: Can I label phone numbers?**
A: Currently you can view phone numbers. Labeling is a planned feature.

**Q: What file types work?**
A: PDF, images (JPG, PNG), emails (.eml), audio files, CSV call logs, SMS exports.

---

## Getting Help

If something doesn't work:
1. Check the status indicator in the bottom-left (should say "Connected")
2. Refresh the page
3. Make sure the server is running (run `start.bat` if needed)
