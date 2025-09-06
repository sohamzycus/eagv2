You are an expert Chrome Extension developer and UI/UX designer.  
Generate a **working Chrome Extension (Manifest V3)** called:  
**Web Lego – Modular Page Composer**  

---

### 🌟 Overview
This extension lets users **pick pieces of any webpage** (paragraphs, images, videos, divs), extract them into **draggable blocks**, and rearrange them inside a clean **canvas UI**.  
Think of it as **Lego for the web** – modular, intuitive, and visual.  

---

### 📂 Deliverables (Code Files)
1. `manifest.json` (Manifest v3, permissions, icons, background service worker).  
2. `popup.html` + `popup.js` → Minimal popup with **Activate Web Lego** button.  
3. `contentScript.js` → Injects toolbar, handles hover/selection of DOM blocks, extracts them.  
4. `canvas.html` + `canvas.js` → Clean UI canvas where blocks are draggable, resizable, deletable.  
5. `styles.css` → Modern clean UI with animations.  
6. `assets/` folder with **extension logo** and icons (generate simple Lego-like colorful logo).  

---

### 🎨 Design & UX
- **Logo/Icon**: Use a **colorful Lego-block style icon** (minimalist, flat, modern).  
- **Popup UI**: Minimal white card with soft shadows, rounded corners.  
- **Toolbar Overlay**:  
  - Floating top bar with 3 buttons:  
    1. **Select Blocks** (hover highlights elements in blue outline).  
    2. **Add to Canvas** (extracts highlighted element).  
    3. **Open Canvas** (opens canvas side panel).  
- **Canvas Panel**:  
  - White background, subtle grid pattern.  
  - Each block appears as a **card** with:  
    - Drag handle  
    - Resize corner  
    - Delete (X) button  
  - Smooth drag-and-drop animations.  
- **Onboarding Demo**:  
  - First-time use → overlay with tooltips:  
    - Step 1: Hover & select blocks  
    - Step 2: Add them to canvas  
    - Step 3: Rearrange & remix freely  
  - If no real content is selected, auto-generate **3 demo blocks** (text, image, quote).  

---

### ⚙️ Features
1. **Block Selection**  
   - Hover highlights block (`div`, `p`, `img`, `video`).  
   - Click → Add to selection.  

2. **Canvas UI**  
   - Open in side panel or new tab.  
   - Draggable & resizable blocks.  
   - Local save with `chrome.storage.local`.  
   - Reset button clears all blocks.  

3. **Onboarding**  
   - Runs once after installation.  
   - Shows how to pick blocks & remix.  
   - Demo blocks appear if no selection is made.  

---

### 🛠️ Technical Details
- Use **Manifest V3** with `service_worker`.  
- Permissions: `activeTab`, `scripting`, `storage`.  
- Styling:  
  - Rounded corners (`border-radius: 12px`).  
  - Subtle shadows (`box-shadow: 0 4px 12px rgba(0,0,0,0.1)`).  
  - Smooth transitions (`transition: all 0.2s ease`).  
- Use **vanilla JS** (no external libraries).  

---

### ✅ Expectations
- Fully working Chrome extension on first run.  
- Clean, modern UI with **wow factor**.  
- No external APIs or integrations.  
- Include **inline comments** in all code explaining logic.  

---

🚀 Now generate the **full extension codebase** with all files, so it can be copied directly into a project folder and loaded in Chrome (Developer Mode → Load unpacked).
