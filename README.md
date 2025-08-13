# 🎯 VCT Dashboard - VALORANT Champions Tour Analytics

A comprehensive Streamlit dashboard for analyzing VALORANT Champions Tour (VCT) data, featuring tournament statistics, agent meta analysis, match insights, and player performance tracking.

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/YOUR_USERNAME/vct-dashboard)
[![CI/CD](https://github.com/YOUR_USERNAME/VCT-Dashboard/workflows/Build%20and%20Deploy/badge.svg)](https://github.com/YOUR_USERNAME/VCT-Dashboard/actions)

🚀 **NEW**: Now with SQLite database backend, Docker containerization, and cloud deployment support!

## ✨ Features

### 🏆 Overview Page
- Tournament-wide statistics and metrics
- Map frequency analysis with interactive charts
- Data validation and error handling
- Responsive design with modern UI components

### 🎯 Agents Analytics
- Agent pick rate analysis across maps and tournaments
- Meta trends and comparative analysis
- Interactive visualizations with Plotly and Altair
- Agent comparison tools

### 📊 Match Details
- Team performance analysis
- Match results and statistics
- Economic round analysis (loadout values, round types)
- Team-specific filtering and insights

### 👥 Player Performance
- Individual player statistics and trends
- Performance leaderboards
- Player comparison tools
- Detailed statistics tables
- Performance tracking over time

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd VCT-Dashboard
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare your data:**
   Place your VCT CSV files in the following directory structure:
   ```
   data/
   ├── vct_2022/
   │   ├── agents/
   │   │   └── agents_pick_rates.csv
   │   ├── matches/
   │   │   ├── overview.csv
   │   │   └── eco_rounds.csv
   │   └── players_stats/
   │       └── players_stats.csv
   └── vct_2025/
       ├── agents/
       ├── matches/
       └── players_stats/
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## 📁 Data Structure

### Required CSV Files

#### **Matches Overview** (`matches/overview.csv`)
Expected columns (flexible naming):
- `Match ID` / `Match Name` - Match identifier
- `Map` / `Map Name` - Map name
- `Team` / `Team A` / `Team B` - Team names
- Additional match statistics

#### **Agent Pick Rates** (`agents/agents_pick_rates.csv`)
Expected columns:
- `Agent` - Agent name
- `Map` - Map name
- `Pick Rate` - Pick percentage
- Optional: `Tournament`, `Stage`

#### **Player Statistics** (`players_stats/players_stats.csv`)
Expected columns:
- `Player` - Player name
- `Team` / `Teams` - Team affiliation
- `Average Combat Score` / `ACS` / `Rating` - Performance metric
- Optional: `Kills`, `Deaths`, `Assists`, `Headshot %`

#### **Economic Rounds** (`matches/eco_rounds.csv`) - Optional
Expected columns:
- `Team` - Team name
- `Type` / `Round Type` - Round classification
- `Loadout Value` - Economic value

### Column Auto-Detection

The dashboard features robust column auto-detection that handles:
- Varying column names and cases
- Missing optional columns
- Different data formats
- Graceful error handling with user feedback

## 🛠️ Technical Features

### Performance Optimizations
- **Cached Data Loading**: `@st.cache_data` decorator for efficient CSV loading
- **Error Handling**: Comprehensive error catching and user-friendly messages
- **Memory Efficient**: Optimized data processing and visualization rendering

### UI/UX Enhancements
- **Responsive Design**: Works on desktop and mobile devices
- **Interactive Charts**: Plotly and Altair visualizations with tooltips
- **Modern Styling**: Custom CSS with VALORANT-inspired color scheme
- **Intuitive Navigation**: Clear sidebar with contextual descriptions

### Data Validation
- **Column Validation**: Automatic detection of required vs optional columns
- **Data Quality Checks**: Handles missing data gracefully
- **User Feedback**: Clear error messages and data structure guidance

## 📊 Usage Examples

### Analyzing Agent Meta
1. Select "Agents" from the sidebar
2. Choose specific agent or enable "Show all agents comparison"
3. Explore pick rates across different maps
4. View meta insights and trends

### Team Performance Analysis
1. Navigate to "Matches" section
2. Select team from dropdown
3. View match history and map performance
4. Analyze economic patterns (if data available)

### Player Comparisons
1. Go to "Players" section
2. Select primary player for analysis
3. Use "Player Comparison" section for side-by-side analysis
4. View performance trends over time

## 🔧 Development

### Project Structure
```
VCT-Dashboard/
├── app.py              # Main Streamlit application
├── utils.py            # Utility functions and data loading
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── pages/             # Individual page modules
│   ├── __init__.py
│   ├── overview.py    # Tournament overview
│   ├── agents.py      # Agent analytics
│   ├── matches.py     # Match analysis
│   └── players.py     # Player performance
└── data/              # Data directory (user-provided)
```

### Adding New Features
1. Create new page module in `pages/` directory
2. Add navigation option in `app.py`
3. Implement data loading with column auto-detection
4. Follow existing error handling patterns

## 📊 Database & Performance

### SQLite Database Backend
The dashboard now uses SQLite for better performance and easier deployment:

```bash
# Import CSV data to SQLite database
python scripts/import_to_sqlite.py

# Verify database structure
python scripts/verify_database.py

# Import large files (if needed)
python scripts/import_large_files.py
```

**Database Features:**
- 📁 Imports from `data/` directory and all `vct_*` subfolders
- 🔄 Automatic schema inference and data type detection
- 📊 111+ tables with 364,810+ rows of VCT data
- 📈 Optimized indexes for fast queries
- 🛡️ Error handling for encoding and format issues
- 🔍 Seamless fallback to CSV files if database unavailable

## 🚀 Deployment Options

### 1. 🐳 Docker (Recommended)
```bash
# Build and run with Docker
docker build -t vct-dashboard .
docker run -p 8501:8501 vct-dashboard

# Or use Docker Compose
docker-compose up --build

# Run with database admin interface
docker-compose --profile admin up
```

### 2. ☁️ Heroku (One-Click)
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Or manually:
```bash
heroku create your-vct-dashboard
heroku stack:set container
git push heroku main
```

### 3. 🌐 AWS ECS (Production)
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 4. 🌩️ Streamlit Cloud
1. Push code to GitHub repository
2. Connect to Streamlit Cloud
3. Database will be automatically created from CSV files

### 5. 💻 Local Development
```bash
# Development mode
streamlit run app.py

# Production mode
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## 🔄 CI/CD Pipeline

Automatic deployment with GitHub Actions:
- ✅ Automated testing and database verification
- 🐳 Multi-platform Docker image builds
- 📦 Docker Hub image publishing
- 🚀 Automatic Heroku deployment
- 🔐 Security scanning with Trivy
- ☁️ Optional AWS ECS deployment

**Setup:**
1. Add GitHub secrets for Docker Hub and Heroku
2. Push to `main` branch triggers full deployment
3. Pull requests trigger testing and validation

## 🐛 Troubleshooting

### Common Issues

**"No VCT data found"**
- Ensure data directory structure matches requirements
- Check CSV file names and locations
- Verify data files are not corrupted

**"Missing required columns"**
- Check CSV column names against expected formats
- Use debug information to see available columns
- Ensure data files contain required fields

**Performance Issues**
- Clear Streamlit cache: `streamlit cache clear`
- Reduce data size for testing
- Check for large CSV files that might need optimization

## 📝 License

[Add your license information here]

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review error messages and debug information

---

**Built with ❤️ for the VALORANT esports community**
