# 📘 BRD Agent Python - User Guide

**Complete Guide to Using the BRD Agent Engineering Manager**

Version: 1.0  
Last Updated: December 2025

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Features Overview](#features-overview)
4. [Input Methods](#input-methods)
5. [Processing BRDs](#processing-brds)
6. [Viewing Results](#viewing-results)
7. [Timeline Visualization](#timeline-visualization)
8. [Download & Export](#download--export)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## 🎯 Introduction

The **BRD Agent** is an AI-powered engineering management tool that automatically generates:
- ✅ **Engineering Plans** - Detailed technical implementation plans
- ✅ **Project Schedules** - Timeline with phases, milestones, and resource allocation
- ✅ **Risk Analysis** - Identified risks with mitigation strategies
- ✅ **Resource Requirements** - Team composition and technology stack

Simply upload your Business Requirements Document (BRD) and let our multi-agent system do the heavy lifting!

---

## 🚀 Getting Started

### Prerequisites

Before using the BRD Agent UI, ensure:

1. **Backend API Running** (Port 8000):
   ```bash
   source .venv/bin/activate
   uvicorn api.main:app --reload --port 8000
   ```

2. **Streamlit UI Running** (Port 8501):
   ```bash
   streamlit run frontend/app.py --server.port 8501
   ```

3. **API Key Configured**:
   - Valid `ANTHROPIC_API_KEY` in `.env` file

### Accessing the UI

Open your browser: **http://localhost:8501**

You'll see the BRD Agent interface with:
- **Left Sidebar**: Configuration and input methods
- **Main Area**: Processing controls and results

---

## ✨ Features Overview

### Core Capabilities

| Feature | Description | Status |
|---------|-------------|--------|
| **PDF Upload** | Upload BRD in PDF format | ✅ Available |
| **JSON Upload** | Upload structured JSON BRD | ✅ Available |
| **Manual Input** | Paste JSON directly | ✅ Available |
| **Sample BRDs** | Pre-loaded examples | ✅ Available |
| **Auto Retry** | Automatic retry on failures (3 attempts) | ✅ Available |
| **Toast Notifications** | Real-time feedback | ✅ Available |
| **Interactive Gantt Chart** | Visual project timeline | ✅ Available |
| **Collapsible Sections** | Organized, readable output | ✅ Available |
| **Download Artifacts** | Export results as JSON | ✅ Available |

---

## 📤 Input Methods

The BRD Agent supports **4 input methods**:

### 1. Upload PDF File 📄

**Best for**: Real-world BRDs in document format

**Steps**:
1. Click **"Upload PDF File"** radio button
2. Click **"Browse files"** or drag & drop
3. Select your BRD PDF file
4. Wait for upload confirmation
5. PDF will be automatically parsed by backend

**Supported**:
- ✅ Single or multi-page PDFs
- ✅ Text-based PDFs (not scanned images)
- ✅ Max size: ~50MB

**Example**:
```
✅ PDF Loaded: project_brd.pdf (245.3 KB)
📄 PDF will be parsed automatically by the backend
```

---

### 2. Upload JSON File 📋

**Best for**: Pre-structured BRDs in JSON format

**Steps**:
1. Click **"Upload JSON File"** radio button
2. Click **"Browse files"**
3. Select your `.json` file
4. BRD will be validated automatically

**Required JSON Structure**:
```json
{
  "project": {
    "name": "Your Project Name",
    "description": "Project description"
  },
  "features": [
    {
      "id": "F001",
      "name": "Feature Name",
      "priority": "High",
      "requirements": ["Requirement 1", "Requirement 2"]
    }
  ],
  "technical_requirements": {
    "platforms": ["Web", "Mobile"],
    "integrations": ["API1", "API2"]
  }
}
```

---

### 3. Paste JSON ✍️

**Best for**: Quick testing or API-generated BRDs

**Steps**:
1. Click **"Paste JSON"** radio button
2. Paste your JSON into the text area
3. JSON will be validated in real-time

**Tips**:
- Use proper JSON formatting (no trailing commas)
- Validate with a JSON linter first
- Maximum ~100KB recommended

---

### 4. Load Sample 🎯

**Best for**: First-time users, demos, testing

**Steps**:
1. Click **"Load Sample"** radio button
2. Sample BRD loads automatically
3. Example: "Customer Onboarding Portal"

**What's Included**:
- Complete project overview
- 5+ features with requirements
- Technical architecture details
- Success metrics

---

## ⚙️ Processing BRDs

### Starting Processing

1. **Load your BRD** using any input method
2. **Verify validation** - Look for "✅ Valid BRD JSON" or "✅ PDF Loaded"
3. **Click "🚀 Process BRD"** button
4. **Wait 30-90 seconds** - Processing happens in background

### What Happens During Processing?

```
🚀 Starting BRD processing...
  ↓
📄 BRD Parsing (normalization)
  ↓
🎯 Engineering Plan Generation
  ↓
📅 Project Schedule Creation
  ↓
✅ Processing complete!
```

### Processing Indicators

| Indicator | Meaning |
|-----------|---------|
| ⏳ Spinner | Active processing |
| 🚀 Toast (top-right) | Processing started |
| ✅ Success message | Completed successfully |
| ❌ Error message | Failed (check debug info) |
| (2 attempts) | Recovered after retry |

### Auto-Retry System

If processing fails, the system **automatically retries**:
- **Attempt 1**: Immediate
- **Attempt 2**: After 2 seconds
- **Attempt 3**: After 4 seconds

**Retry occurs for**:
- Network timeouts
- Server errors (5xx)
- Connection issues

**No retry for**:
- Invalid BRD format (4xx)
- JSON parsing errors

---

## 📊 Viewing Results

After successful processing, navigate to the **"Results"** tab.

### 1. Processing Summary

At the top, you'll see:

```
Status: ✅ Success
Stages Completed: 3
Completed At: 2025-12-12 10:43
```

**Stages**:
- ✓ BRD Parsing
- ✓ Engineering Plan
- ✓ Project Schedule

---

### 2. Engineering Plan 🎯

The Engineering Plan includes **7 collapsible sections**:

#### 📋 Project Overview
- Project name
- Description
- Key objectives

**Example**:
> **Project Name**: Customer Onboarding Portal  
> **Objectives**: Reduce churn, Improve TTV, Increase CSM efficiency

---

#### 🎯 Feature Breakdown
Each feature shows:
- **Feature ID** & Name
- **Priority**: Critical | High | Medium | Low
- **Complexity**: High | Medium | Low
- **Estimated Effort**: "2 weeks", "1 month", etc.
- **Technical Requirements**
- **Acceptance Criteria**

**Visual Indicators**:
- 🔴 Critical Priority
- 🟡 Medium Priority
- 🟢 Low Priority

---

#### 🏗️ Technical Architecture
- System components
- Integration points
- Data flow description
- Security considerations

---

#### 📅 Implementation Phases
Step-by-step rollout plan:
- Phase number & name
- Duration estimate
- Features included in each phase
- Deliverables

---

#### ⚠️ Risk Analysis
Color-coded risks:
- 🔴 High Impact
- 🟡 Medium Impact
- 🟢 Low Impact

Each risk includes:
- Description
- Impact level
- Probability
- Mitigation strategy

---

#### 👥 Resource Requirements
- Team composition (roles & count)
- Tools & technologies needed
- Infrastructure requirements

**Example**:
> - 2 Full-stack Developers  
> - 1 UI/UX Designer  
> - 1 DevOps Engineer  
> **Technologies**: React.js, Node.js, PostgreSQL

---

#### 📊 Success Metrics
KPIs to track:
- Metric name
- Target value
- Measurement method

---

### 3. Project Schedule 📅

The Project Schedule includes:

#### ℹ️ Project Information
```
Start Date: 2025-01-01
End Date: 2025-06-30
Total Duration: 26 weeks
```

#### 📅 Project Phases
Each phase shows:
- Phase name
- Start & end dates
- Duration in weeks
- **Milestones** with target dates

**Example**:
> **Phase 1: MVP Release**  
> Start: 2025-01-01 | End: 2025-03-31 | Duration: 13 weeks  
> Milestones:
> - 📍 Requirements Complete (2025-01-15)
> - 📍 Design Review (2025-02-01)
> - 📍 MVP Launch (2025-03-31)

---

#### 👥 Resource Allocation
Team assignments and allocation percentages

#### 🎯 Critical Path
Tasks that impact project timeline

#### 💡 Assumptions & Constraints
- **Assumptions**: Things we're assuming are true
- **Constraints**: Limitations we must work within

---

## 📅 Timeline Visualization

Navigate to the **"Timeline"** tab for an interactive Gantt chart.

### Features

1. **Interactive Chart**
   - Hover over bars for details
   - Zoom in/out
   - Pan left/right
   - Download as PNG

2. **Visual Elements**
   - 🔵 Blue bars = Phases
   - 🟢 Green markers = Milestones

3. **Schedule Overview Metrics**
   ```
   Start Date | End Date | Total Duration | Phases
   ```

### Using the Gantt Chart

- **Zoom**: Scroll wheel or pinch
- **Pan**: Click and drag
- **Details**: Hover over any element
- **Download**: Click camera icon (top-right of chart)

---

## 💾 Download & Export

### Download Options

| Artifact | Format | Location |
|----------|--------|----------|
| Engineering Plan | JSON | Results tab button |
| Project Schedule | JSON | Results tab button |
| Full Response | JSON | Results tab button |
| Gantt Chart | PNG | Timeline tab (camera icon) |

### Downloading Artifacts

1. Go to **Results** tab
2. Scroll to desired artifact section
3. Click **"💾 Download Engineering Plan"** or **"💾 Download Project Schedule"**
4. File saves to your Downloads folder

**Filename Format**:
```
engineering_plan_2025-12-12.json
project_schedule_2025-12-12.json
```

### Generated Files (Server-side)

All artifacts are also automatically saved to:
```
sample_inputs/outputs/
├── engineering_plans/
│   └── engineering_plan_{project_name}_v1_{timestamp}.json
└── project_schedules/
    └── project_schedule_{project_name}_v1_{timestamp}.json
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Empty response from orchestrator"

**Cause**: Backend not running or unreachable

**Solution**:
1. Check backend is running: `curl http://localhost:8000/health`
2. Restart backend if needed
3. Try processing again

---

#### 2. "Request timed out after 3 attempts"

**Cause**: Backend overloaded or slow

**Solutions**:
- Wait a few minutes and retry
- Check backend logs for errors
- Restart backend: `uvicorn api.main:app --reload --port 8000`

---

#### 3. "Invalid BRD: BRD must contain..."

**Cause**: Missing required fields in JSON

**Solution**:
Ensure your JSON has one of:
- `project` object
- `features` array
- `raw_brd_text` string

---

#### 4. "Could not generate Gantt chart"

**Cause**: Missing `phases` data in schedule

**Solutions**:
1. Check Results tab - is Project Schedule there?
2. Process a fresh BRD
3. Check for validation errors in backend logs

---

#### 5. PDF Upload Not Working

**Causes & Solutions**:

| Issue | Solution |
|-------|----------|
| File too large | Keep PDFs under 50MB |
| Scanned image PDF | Use text-based PDFs or OCR first |
| Corrupted file | Try re-exporting PDF |
| Wrong format | Ensure it's actually a PDF file |

---

## 💡 Best Practices

### For Best Results

1. **PDF BRDs**:
   - Use text-based PDFs (not scanned images)
   - Ensure proper structure (headings, sections)
   - Include all required sections
   - Keep under 50 pages for faster processing

2. **JSON BRDs**:
   - Follow the documented schema
   - Use clear, descriptive names
   - Include all key fields
   - Validate JSON before uploading

3. **Processing**:
   - Wait for full completion (don't refresh)
   - Check all 3 stages completed
   - Review Results before Timeline
   - Download artifacts for records

4. **Troubleshooting**:
   - Check backend logs first
   - Enable debug mode in sidebar
   - Test with sample BRD first

---

## 🎓 Tips & Tricks

### Power User Tips

1. **Quick Testing**: Use "Load Sample" to verify system is working
2. **Batch Processing**: Clear workspace between BRDs for clean state
3. **Compare Outputs**: Download artifacts to compare different BRD versions
4. **Custom BRDs**: Structure your BRDs consistently for better results
5. **Performance**: Smaller, focused BRDs process faster

### Workflow Optimization

1. Prepare BRDs in standard format
2. Validate JSON before uploading
3. Keep browser tab active during processing
4. Review engineering plan before relying on schedule
5. Export artifacts immediately after generation

---

## 📞 Support & Resources

### Documentation

- **Setup Guide**: `SETUP.md`
- **README**: `README.md`
- **API Reference**: `API_REFERENCE.md`
- **Architecture**: `ARCHITECTURE.md`

### Testing

- **Sample BRDs**: `sample_inputs/brds/`
- **Sample Outputs**: `sample_inputs/outputs/`

### Getting Help

1. Check troubleshooting section above
2. Review backend logs
3. Open GitHub issue with:
   - Error message
   - Steps to reproduce
   - Environment details

---

## ✅ Quick Reference

### Input Methods
| Method | Best For | Format |
|--------|----------|--------|
| PDF Upload | Real BRDs | .pdf |
| JSON Upload | Structured data | .json |
| Paste JSON | Quick tests | Text |
| Load Sample | First-time use | Built-in |

### Processing Time
- PDF: 60-90 seconds
- JSON: 30-60 seconds
- Retry adds: +2-8 seconds

### Output Artifacts
- Engineering Plan: Detailed implementation guide
- Project Schedule: Timeline with phases & milestones
- Gantt Chart: Visual timeline representation

### Key Features
- ✅ PDF Support
- ✅ Auto-Retry (3 attempts)
- ✅ Toast Notifications
- ✅ Interactive Charts
- ✅ One-click Downloads

---

**Happy Engineering Planning!** 🚀

For technical support or feature requests, open an issue on GitHub.

*Last updated: December 2025*

