# How to Save & Reuse Video Results (No API Waste!)

This guide shows you how to save processed video data and reuse it for testing without burning API credits.

---

## 📋 Quick Guide

### **Step 1: Process a Video Once**
1. Upload your video at `http://localhost:5001/`
2. Wait for processing to complete
3. Note the job ID from the URL (e.g., `What_Is_n8n__..._20251215_194234`)

### **Step 2: Save the Results**
Run this in your terminal:
```bash
cd /Users/falahi/VidScrib
python3 save_results.py <JOB_ID>
```

**Example:**
```bash
python3 save_results.py What_Is_n8n__The_Beginner-Friendly_Automation_Tool_Explained_1_20251215_194234
```

You'll see:
```
✅ Saved results to: saved_results/What_Is_n8n__..._20251215_194234.json
   - Title: What Is n8n? The Beginner-Friendly Automation Tool Explained
   - Slides: 6
   - Template: professional
   - Size: 12345 bytes
```

### **Step 3: Reuse Anytime (No API Calls!)**
Visit in your browser:
```
http://localhost:5001/saved/<JOB_ID>
```

**Example:**
```
http://localhost:5001/saved/What_Is_n8n__The_Beginner-Friendly_Automation_Tool_Explained_1_20251215_194234
```

---

## 🎯 Use Cases

### **Test Template Changes**
1. Save your video results once
2. Change templates in code
3. Load saved results → See new template instantly
4. **No LLM API calls needed!**

### **Test UI Changes**
1. Save results
2. Modify `results.html`, `results.css`, or `results.js`
3. Load saved results to see changes
4. **No video processing needed!**

### **Test Download/Present Buttons**
1. Save results
2. Test button functionality repeatedly
3. **No API usage!**

---

## 📂 List Saved Results

See all your saved results:
```bash
python3 save_results.py list
```

Output:
```
📁 Saved Results (2):
  • What_Is_n8n__..._20251215_194234.json
    Title: What Is n8n?
    Slides: 6

  • AI_Tutorial_20251215_120000.json
    Title: AI & Machine Learning Guide
    Slides: 8
```

---

## 🔄 Complete Workflow

```
┌─────────────────────────────────────┐
│ 1. Upload Video (ONCE)              │  ← Uses API
│    • Processes with Gemini AI       │
│    • Generates slides               │
│    • Creates PPT                    │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ 2. Save Results                     │  ← No API
│    python3 save_results.py <ID>     │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ 3. Reuse Forever                    │  ← No API
│    http://localhost:5001/saved/<ID> │
│    • Test templates                 │
│    • Test UI changes                │
│    • Test buttons                   │
│    • Test everything!               │
└─────────────────────────────────────┘
```

---

## 💡 Tips

### **Organize Your Saved Results**
Name them descriptively:
```bash
# After saving, you can rename for clarity:
cd saved_results
mv long_video_id.json my_test_video.json
```

Then access via:
```
http://localhost:5001/saved/my_test_video
```

### **Share with Team**
The JSON files contain all the data! Share with teammates:
```bash
# They can put it in their saved_results folder
# and view it instantly - no processing needed!
```

### **Version Control**
You can commit a `saved_results/sample.json` to git for demos/testing!

---

## 📁 What Gets Saved?

The JSON file contains:
- ✅ All slide content (titles, bullets, text)
- ✅ Video metadata (title, language, duration)
- ✅ Template selection
- ✅ Processing time
- ✅ Summary/overview

**Does NOT contain:**
- ❌ Original video file
- ❌ Keyframe images (optional - can be added if needed)

---

## 🚀 Example Session

```bash
# 1. Process video once
# (Upload via browser at http://localhost:5001/)
# Wait for completion, copy job ID from URL

# 2. Save it
python3 save_results.py What_Is_n8n__The_Beginner-Friendly_Automation_Tool_Explained_1_20251215_194234

# 3. Test template change
# Edit code to change template styling...

# 4. View with saved data (no API!)
# Visit: http://localhost:5001/saved/What_Is_n8n__The_Beginner-Friendly_Automation_Tool_Explained_1_20251215_194234

# 5. Test UI change
# Edit results.html...

# 6. Refresh browser - see changes instantly!
# Still no API calls!

# 7. Repeat steps 4-6 as many times as needed!
```

---

## ✅ Perfect for Development!

Save one good video result, then:
- ⚡ Test unlimited times
- 💰 Save API costs
- 🚀 Faster iteration
- 🎯 Consistent test data

No more waiting for video processing during development! 🎉
