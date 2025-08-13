# 🎯 VCT Dashboard - How to Run

## 🚀 Quick Start

### Method 1: Full Setup with External Access (Recommended)
```bash
python reliable_tunnel.py
```

### Method 2: Local Only
```bash
streamlit run app.py
```

### Method 3: Network Access Only  
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### Method 4: With CloudFlare Tunnel (Manual)
```bash
# Terminal 1
streamlit run app.py --server.address 0.0.0.0 --server.port 8501

# Terminal 2  
cloudflared tunnel --url http://localhost:8501
```

## 🔧 Requirements

- Python 3.8+
- All dependencies installed (`pip install -r requirements.txt`)
- CloudFlared installed for external access (`brew install cloudflared`)

## 📊 Features Available

- ✅ VCT Data 2021-2025 (5+ million rows)
- ✅ Player Statistics and Analysis
- ✅ Agent Pick Rates and Meta Analysis  
- ✅ Match Overviews and Results
- ✅ Tournament Analytics
- ✅ Interactive Charts and Visualizations
- ✅ External Access via CloudFlare Tunnel

## 🌐 Access URLs

After running, you'll get:

- **Local**: http://localhost:8501
- **Network**: http://your-local-ip:8501  
- **External**: https://random-name.trycloudflare.com

## 🛑 Stopping the Dashboard

Press `Ctrl+C` in the terminal to stop all services.

## 🎯 Troubleshooting

### If you get database errors:
```bash
python scripts/import_large_files.py
```

### If CloudFlare tunnel fails:
The dashboard will still work locally at http://localhost:8501

### If you need to reimport data:
```bash
python scripts/import_to_sqlite.py
```

## 📝 File Structure

```
VCT-Dashboard/
├── app.py                    # Main Streamlit application
├── reliable_tunnel.py        # Run this for full setup
├── pages/                    # Dashboard pages
│   ├── overview.py
│   ├── agents.py  
│   ├── matches.py
│   └── players.py
├── utils.py                  # Utility functions
├── vct.db                    # SQLite database with all VCT data
├── data/                     # Original CSV data files
└── scripts/                  # Import and setup scripts
```

## 🎊 What You Get

Your VCT Dashboard includes:
- Complete VALORANT Champions Tour data from 2021-2025
- Player performance analytics and comparisons
- Agent meta analysis and pick rates
- Match results and tournament statistics  
- Interactive visualizations and charts
- External access for sharing with others

## 🔥 Pro Tips

1. **For permanent hosting**: Consider using Railway, Render, or Streamlit Cloud
2. **For better uptime**: Set up authenticated CloudFlare tunnels
3. **For local development**: Use Method 2 (local only)
4. **For sharing**: Use Method 1 (full setup) to get external URLs

---

Enjoy exploring the VCT data! 🎮
