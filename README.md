# GI Reconciliation App

## 📋 Description

The GI Reconciliation App is a Streamlit-based web tool designed to reconcile transactional data between two sources: Atlantis and GMI. It compares records by Carry Broker (CB), Date, and Account, and provides four distinct summary views:
- ✅ Full Matches (Qty and Fee match)
- 🔍 Qty Match Only (Fee differs)
- 🔍 Fee Match Only (Qty differs)
- ⚠️ No Match (Qty and Fee differ)

Additionally, users can:
- Select a specific month to filter transactions
- Download results as an Excel file with multiple tabs for each summary view

---

## 📦 Requirements

Install Python 3.9+ and the following packages:

```bash
pip install streamlit pandas openpyxl
```

---

## ▶️ How It Works

### 1. Upload Files
- **Atlantis file** (CSV or Excel): must contain columns:
  - `ExchangeEBCode`, `TradeDate`, `Quantity`, `GiveUpAmt`, `ClearingAccount`, `RecordType`
- **GMI file** (CSV or Excel): must contain columns:
  - `TGIVF#`, `TEDATE`, `TQTY`, `TFEE5`, `ACCT`, `TGIVIO`

### 2. Filter and Transform
- Filters `RecordType == 'TP'` in Atlantis
- Filters `TGIVIO == 'GI'` in GMI
- Converts date columns to datetime using format `YYYYMMDD`
- Filters records by selected month

### 3. Group and Compare
- Groups by `CB`, `Date`, `Account`
- Sums `Qty` and `Fee`
- Merges and calculates:
  - `Qty_Diff = Qty_Atlantis - Qty_GMI`
  - `Fee_Diff = Fee_Atlantis + Fee_GMI` (signed)

### 4. Export
- Excel file with 4 sheets:
  - Full Matches
  - Qty Match Only
  - Fee Match Only
  - No Match

---

## 💻 Run Locally

```bash
streamlit run cb_month_summary_app.py
```

## 🗂 Output
An Excel file will be generated with 4 summary tabs for further review and audit.